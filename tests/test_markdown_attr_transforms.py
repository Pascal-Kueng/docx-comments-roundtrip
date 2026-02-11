from __future__ import annotations

import runpy
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.helpers.markdown_inspector import extract_comment_start_attrs

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_PATH = REPO_ROOT / "docx-comments"


class TestMarkdownAttrTransforms(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("pandoc") is None:
            raise unittest.SkipTest("pandoc not found on PATH")
        if not CONVERTER_PATH.exists():
            raise unittest.SkipTest(f"converter script not found: {CONVERTER_PATH}")
        cls.converter_mod = runpy.run_path(str(CONVERTER_PATH))

    def test_annotate_comment_attrs_does_not_touch_code_literals(self) -> None:
        annotate = self.converter_mod["annotate_markdown_comment_attrs"]
        work_dir = Path(tempfile.mkdtemp(prefix="ast-annotate-", dir="/tmp"))
        md_path = work_dir / "input.md"
        md_path.write_text(
            (
                "```text\n"
                "FAKE {.comment-start id=\"999\"}\n"
                "```\n\n"
                "Real [anchor]{.comment-start id=\"10\" author=\"A\" date=\"2026-01-01T00:00:00Z\"}"
                " text[]{.comment-end id=\"10\"}.\n"
            ),
            encoding="utf-8",
        )

        changed = annotate(
            md_path,
            parent_map={},
            state_by_id={"10": "resolved"},
            para_by_id={"10": "AAAABBBB"},
            durable_by_id={"10": "CCCCDDDD"},
            presence_provider_by_id={},
            presence_user_by_id={},
            pandoc_extra_args=None,
            writer_format="markdown",
            cwd=work_dir,
        )
        self.assertGreater(changed, 0)

        output = md_path.read_text(encoding="utf-8")
        self.assertIn('FAKE {.comment-start id="999"}', output)

        attrs = extract_comment_start_attrs(md_path)
        self.assertEqual(attrs["10"].get("state"), "resolved")
        self.assertEqual(attrs["10"].get("paraId"), "AAAABBBB")
        self.assertEqual(attrs["10"].get("durableId"), "CCCCDDDD")

    def test_strip_transport_attrs_does_not_touch_code_literals(self) -> None:
        strip_ast = self.converter_mod["strip_comment_transport_attrs_ast"]
        work_dir = Path(tempfile.mkdtemp(prefix="ast-strip-", dir="/tmp"))
        in_md = work_dir / "input.md"
        out_md = work_dir / "output.md"
        in_md.write_text(
            (
                "```text\n"
                "FAKE {.comment-start id=\"999\" paraId=\"BAD1\" durableId=\"BAD2\" "
                "presenceProvider=\"BAD3\" presenceUserId=\"BAD4\"}\n"
                "```\n\n"
                "Real [anchor]{.comment-start id=\"20\" author=\"A\" date=\"2026-01-01T00:00:00Z\" "
                "paraId=\"AAAA0001\" durableId=\"BBBB0002\" presenceProvider=\"AD\" "
                "presenceUserId=\"USR\"} text[]{.comment-end id=\"20\"}.\n"
            ),
            encoding="utf-8",
        )

        strip_ast(
            in_md,
            out_md,
            pandoc_extra_args=None,
            writer_format="markdown",
            cwd=work_dir,
        )

        output = out_md.read_text(encoding="utf-8")
        self.assertIn(
            'FAKE {.comment-start id="999" paraId="BAD1" durableId="BAD2" '
            'presenceProvider="BAD3" presenceUserId="BAD4"}',
            output,
        )

        attrs = extract_comment_start_attrs(out_md)
        self.assertNotIn("paraId", attrs["20"])
        self.assertNotIn("durableId", attrs["20"])
        self.assertNotIn("presenceProvider", attrs["20"])
        self.assertNotIn("presenceUserId", attrs["20"])

    def test_writer_passthrough_helpers(self) -> None:
        resolve_writer = self.converter_mod["resolve_pandoc_writer_format"]
        render_args = self.converter_mod["pandoc_args_for_json_markdown_render"]

        self.assertEqual(resolve_writer(["-t", "commonmark"], default_format="markdown"), "commonmark")
        self.assertEqual(resolve_writer(["--to=gfm"], default_format="markdown"), "gfm")
        self.assertEqual(resolve_writer([], default_format="markdown"), "markdown")

        filtered = render_args(
            [
                "-t",
                "commonmark",
                "--extract-media=.",
                "--output=out.md",
                "--wrap=none",
                "--columns=120",
            ]
        )
        self.assertIn("--wrap=none", filtered)
        self.assertIn("--columns=120", filtered)
        self.assertNotIn("-t", filtered)
        self.assertTrue(all(not arg.startswith("--to") for arg in filtered))
        self.assertTrue(all(not arg.startswith("--output") for arg in filtered))
        self.assertTrue(all(not arg.startswith("--extract-media") for arg in filtered))
