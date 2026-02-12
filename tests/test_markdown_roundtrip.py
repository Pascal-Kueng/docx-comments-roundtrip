from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.helpers.docx_inspector import inspect_docx
from tests.helpers.markdown_inspector import inspect_markdown_comments

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_PATH = REPO_ROOT / "docx-comments"
CHALLENGING_MD = REPO_ROOT / "tests" / "challenging.md"
CARD_META_INLINE_RE = re.compile(
    r"<!--\s*CARD_META\s*\{\s*#(?P<id>[A-Za-z0-9][A-Za-z0-9_-]*)\s*(?P<attrs>.*?)\}\s*-->",
    re.DOTALL,
)
CARD_HEADER_RE = re.compile(
    r"^\[!\s*(?P<kind>COMMENT|REPLY)\s+(?P<id>[A-Za-z0-9][A-Za-z0-9_-]*)\s*:\s*(?P<author>.+?)\s*\((?P<state>active|resolved)\)\s*\]$",
    re.IGNORECASE,
)


def run_converter(input_path: Path, output_path: Path) -> None:
    subprocess.run(
        [str(CONVERTER_PATH), str(input_path.absolute()), "-o", str(output_path.absolute())],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def strip_blockquote_prefix(line: str) -> str:
    text = str(line or "")
    while True:
        updated = re.sub(r"^\s*>\s?", "", text)
        if updated == text:
            return text.strip()
        text = updated


def parse_fixture_card_meta(markdown_text: str) -> tuple[dict[str, dict[str, str]], dict[str, str], list[str]]:
    cards_by_id: dict[str, dict[str, str]] = {}
    kind_by_id: dict[str, str] = {}
    errors: list[str] = []
    pending_header: tuple[str, str, int] | None = None

    for line_no, raw in enumerate(str(markdown_text or "").splitlines(), start=1):
        normalized = strip_blockquote_prefix(raw)
        header_match = CARD_HEADER_RE.match(normalized)
        if header_match:
            pending_header = (
                str(header_match.group("id") or "").strip(),
                str(header_match.group("kind") or "").strip().upper(),
                line_no,
            )

        meta_match = CARD_META_INLINE_RE.search(raw)
        if not meta_match:
            continue

        comment_id = str(meta_match.group("id") or "").strip()
        attrs_raw = str(meta_match.group("attrs") or "").strip()
        parsed: dict[str, str] = {}
        if attrs_raw:
            try:
                payload = json.loads("{" + attrs_raw + "}")
            except json.JSONDecodeError as exc:
                errors.append(
                    f"Line {line_no}: CARD_META for #{comment_id} is not canonical JSON pairs "
                    f"(expected style like \"author\":\"Alice\"): {exc.msg}"
                )
                payload = {}
            if isinstance(payload, dict):
                for key, value in payload.items():
                    key_str = str(key or "").strip()
                    if key_str:
                        parsed[key_str] = str(value or "").strip()

        cards_by_id[comment_id] = parsed
        if pending_header and pending_header[0] == comment_id:
            kind_by_id[comment_id] = pending_header[1]
        elif comment_id not in kind_by_id:
            kind_by_id[comment_id] = "COMMENT"

    return cards_by_id, kind_by_id, errors


class TestMarkdownRoundtripStability(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("pandoc") is None:
            raise unittest.SkipTest("pandoc not found on PATH")
        if not CONVERTER_PATH.exists():
            raise unittest.SkipTest(f"converter script not found: {CONVERTER_PATH}")
        if not CHALLENGING_MD.exists():
            raise unittest.SkipTest(f"challenging fixture not found: {CHALLENGING_MD}")

    def assert_set_equal(self, label: str, expected: set[str], actual: set[str]) -> None:
        if expected == actual:
            return
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        self.fail(
            f"{label} mismatch\n"
            f"- Missing: {missing}\n"
            f"- Extra: {extra}"
        )

    def assert_dict_equal(self, label: str, expected: dict, actual: dict) -> None:
        if expected == actual:
            return
        keys = sorted(set(expected.keys()) | set(actual.keys()))
        lines = []
        for key in keys:
            exp = expected.get(key)
            got = actual.get(key)
            if exp != got:
                lines.append(f"{key!r}: expected={exp!r} actual={got!r}")
        self.fail(f"{label} mismatch\n- " + "\n- ".join(lines))

    def test_challenging_fixture_card_meta_contract(self) -> None:
        text = CHALLENGING_MD.read_text(encoding="utf-8")
        cards_by_id, kind_by_id, parse_errors = parse_fixture_card_meta(text)
        if parse_errors:
            self.fail("Fixture CARD_META syntax errors:\n- " + "\n- ".join(parse_errors))

        if not cards_by_id:
            self.fail("Fixture has no CARD_META entries.")

        required_common = {"author", "state"}
        errors: list[str] = []
        for comment_id, meta in sorted(cards_by_id.items()):
            kind = kind_by_id.get(comment_id, "COMMENT")
            missing = sorted(k for k in required_common if not str(meta.get(k) or "").strip())
            if missing:
                errors.append(f"Comment #{comment_id} missing required CARD_META keys: {missing}")
            state = str(meta.get("state") or "").strip().lower()
            if state not in {"active", "resolved"}:
                errors.append(f"Comment #{comment_id} has invalid state {state!r}")
            if kind == "REPLY" and not str(meta.get("parent") or "").strip():
                errors.append(f"Reply #{comment_id} missing required CARD_META key: parent")

        if str(cards_by_id.get("5", {}).get("parent") or "").strip() != "4":
            errors.append("Fixture reply #5 must reference parent #4 via CARD_META parent field.")

        if errors:
            self.fail("Fixture CARD_META contract failed:\n- " + "\n- ".join(errors))

    def test_markdown_roundtrip_semantic_fidelity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="md-roundtrip-") as tmp:
            tmp_path = Path(tmp)
            roundtrip_docx = tmp_path / "roundtrip.docx"
            roundtrip_md = tmp_path / "roundtrip.md"

            run_converter(CHALLENGING_MD, roundtrip_docx)
            run_converter(roundtrip_docx, roundtrip_md)

            source = inspect_markdown_comments(CHALLENGING_MD)
            docx = inspect_docx(roundtrip_docx)
            roundtrip = inspect_markdown_comments(roundtrip_md)

            source_ids = set(source.start_ids_order)
            docx_ids = set(docx.comment_ids_order)
            roundtrip_ids = set(roundtrip.start_ids_order)
            self.assert_set_equal("Comment IDs (source->docx)", source_ids, docx_ids)
            self.assert_set_equal("Comment IDs (source->roundtrip markdown)", source_ids, roundtrip_ids)

            source_parent = dict(source.parent_by_id)
            docx_parent = dict(docx.parent_map)
            roundtrip_parent = dict(roundtrip.parent_by_id)
            self.assert_dict_equal("Thread parent map (source->docx)", source_parent, docx_parent)
            self.assert_dict_equal(
                "Thread parent map (source->roundtrip markdown)",
                source_parent,
                roundtrip_parent,
            )

            source_state = {cid: source.state_by_id.get(cid, "active") for cid in source_ids}
            docx_state = {
                cid: ("resolved" if docx.resolved_by_id.get(cid, False) else "active")
                for cid in source_ids
            }
            roundtrip_state = {cid: roundtrip.state_by_id.get(cid, "active") for cid in source_ids}
            self.assert_dict_equal("Comment state map (source->docx)", source_state, docx_state)
            self.assert_dict_equal(
                "Comment state map (source->roundtrip markdown)",
                source_state,
                roundtrip_state,
            )

            source_text = {cid: source.own_text_by_id.get(cid, "") for cid in source_ids}
            docx_text = {cid: docx.comments_by_id[cid].text for cid in source_ids}
            roundtrip_text = {cid: roundtrip.own_text_by_id.get(cid, "") for cid in source_ids}
            self.assert_dict_equal("Comment text map (source->docx)", source_text, docx_text)
            self.assert_dict_equal(
                "Comment text map (source->roundtrip markdown)",
                source_text,
                roundtrip_text,
            )


if __name__ == "__main__":
    unittest.main()
