from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import converter
from .commands import run_auto, run_docx2md, run_md2docx
from .version import __version__

# Keep parity with previous script behavior in stow/symlink environments.
sys.dont_write_bytecode = True


def _help_formatter(prog: str):
    # Keep option/help columns stable and avoid cramped wrapping.
    return argparse.HelpFormatter(prog, max_help_position=30, width=100)


class _DmcHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=30, width=100)


def _build_dmc_help_parser():
    parser = argparse.ArgumentParser(
        prog="dmc",
        description=f"dmc {__version__} - Docx Markdown Comments\n\n"
        "Lossless bidirectional conversion preserving comment threads.",
        usage="dmc <FILE>\n       dmc <COMMAND> [OPTIONS]",
        epilog=(
            "COMMANDS:\n"
            "  docx2md (d2m)   Convert DOCX -> Markdown\n"
            "  md2docx (m2d)   Convert Markdown -> DOCX\n\n"
            "AUTO-DETECT:\n"
            "  dmc draft.docx  Creates draft.md\n"
            "  dmc draft.md    Creates draft.docx\n\n"
            "Use 'dmc <command> --help' for more information."
        ),
        formatter_class=_DmcHelpFormatter,
    )
    parser.add_argument(
        "target",
        nargs="?",
        metavar="FILE|COMMAND",
        help="Input file for auto mode, or a command name such as docx2md / md2docx",
    )
    return parser


def _handle_common_errors(fn):
    try:
        return fn()
    except subprocess.CalledProcessError as exc:
        print(f"pandoc failed (exit {exc.returncode}): {' '.join(exc.cmd)}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - explicit user-facing fallback path.
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_docx2md_parser(prog_name: str):
    parser = argparse.ArgumentParser(
        prog=prog_name,
        description="docx2md (d2m) - Convert DOCX to Markdown",
        formatter_class=_help_formatter,
    )
    parser.add_argument("input", type=Path, help="Input DOCX path")
    parser.add_argument("-o", "--output", type=Path, help="Output markdown file")
    return parser


def _build_md2docx_parser(prog_name: str):
    parser = argparse.ArgumentParser(
        prog=prog_name,
        description="md2docx (m2d) - Convert Markdown to DOCX",
        formatter_class=_help_formatter,
    )
    parser.add_argument("input", type=Path, help="Input markdown path")
    parser.add_argument("-o", "--output", type=Path, help="Output DOCX file")
    parser.add_argument(
        "-r",
        "--ref",
        dest="reference_doc",
        type=Path,
        help="Reference DOCX style file (maps to pandoc --reference-doc)",
    )
    return parser


def main_docx_comments(argv=None):
    return converter.legacy_main(argv=argv, prog_name="docx-comments")


def main_docx2md(argv=None, prog_name=None):
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = _build_docx2md_parser(prog_name or "docx2md")
    args, pandoc_extra_args = parser.parse_known_args(args_list)
    return _handle_common_errors(lambda: run_docx2md(args.input, args.output, pandoc_extra_args))


def main_md2docx(argv=None, prog_name=None):
    args_list = list(sys.argv[1:] if argv is None else argv)
    parser = _build_md2docx_parser(prog_name or "md2docx")
    args, pandoc_extra_args = parser.parse_known_args(args_list)
    return _handle_common_errors(
        lambda: run_md2docx(
            args.input,
            args.output,
            reference_doc=args.reference_doc,
            pandoc_extra_args=pandoc_extra_args,
        )
    )


def _main_dmc(argv=None):
    args_list = list(sys.argv[1:] if argv is None else argv)
    if not args_list or args_list[0] in {"-h", "--help"}:
        _build_dmc_help_parser().print_help()
        return 0

    if args_list[0] in {"-V", "--version"}:
        print(f"dmc {__version__}")
        return 0

    subcmd = args_list[0]
    rest = args_list[1:]
    if subcmd in {"docx2md", "d2m"}:
        return main_docx2md(rest, prog_name=f"dmc {subcmd}")
    if subcmd in {"md2docx", "m2d"}:
        return main_md2docx(rest, prog_name=f"dmc {subcmd}")

    if subcmd in {"threads", "stats", "check", "diff"}:
        print(
            f"error: command '{subcmd}' is planned but not implemented yet in this release.",
            file=sys.stderr,
        )
        return 2

    auto_parser = argparse.ArgumentParser(
        prog="dmc",
        description="Auto-detect conversion mode from input extension.",
        formatter_class=_help_formatter,
    )
    auto_parser.add_argument("input", type=Path, help="Input file (.docx or markdown)")
    auto_parser.add_argument("-o", "--output", type=Path, help="Output file path")
    auto_args, pandoc_extra_args = auto_parser.parse_known_args(args_list)
    return _handle_common_errors(lambda: run_auto(auto_args.input, auto_args.output, pandoc_extra_args))


def main(argv=None):
    invoked = Path(sys.argv[0]).name.lower()
    if invoked in {"docx-comments"}:
        return main_docx_comments(argv)
    if invoked in {"docx2md", "d2m"}:
        return main_docx2md(argv, prog_name=Path(sys.argv[0]).name)
    if invoked in {"md2docx", "m2d"}:
        return main_md2docx(argv, prog_name=Path(sys.argv[0]).name)
    return _main_dmc(argv)
