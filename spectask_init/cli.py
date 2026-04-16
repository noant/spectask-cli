from __future__ import annotations

import argparse
import sys
import zipfile
from dataclasses import dataclass

from spectask_init.bootstrap import run_extend, run_template_bootstrap

DEFAULT_TEMPLATE_URL = "https://github.com/noant/spectask.git"

# IDE `name` values from the official template's .metadata/skills-map.json on main (keep in sync with upstream).
OFFICIAL_TEMPLATE_IDE_KEYS: tuple[str, ...] = (
    "cursor",
    "claude-code",
    "qwen-code",
    "qoder",
    "windsurf",
)


def _template_url_from_argv(argv: list[str] | None) -> str:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--template-url", default=DEFAULT_TEMPLATE_URL)
    ns, _ = p.parse_known_args(argv)
    return ns.template_url


def _official_ide_keys_with_all() -> list[str]:
    return [*OFFICIAL_TEMPLATE_IDE_KEYS, "auto", "all"]


def _ide_choices_for_template_url(template_url: str) -> list[str] | None:
    if template_url != DEFAULT_TEMPLATE_URL:
        return None
    return _official_ide_keys_with_all()


def _ide_argument_help(*, parse_time_restricted: bool) -> str:
    keys = _official_ide_keys_with_all()
    listed = ", ".join(keys)
    base = (
        f"One or more IDE keys: {listed}. "
        "Each key selects file paths from the resolved template’s .metadata/skills-map.json; "
        "multiple keys merge those lists in order without duplicate paths. "
        "The key auto resolves to one or more IDE keys using that template’s .metadata/ide-detection.json and "
        "file or directory markers under the current working directory (every matching IDE is included, "
        "in detection-file order, and their path lists are merged like multiple explicit keys); "
        "it must be used alone. "
        "The special key all copies the union of every IDE’s file list and must be used alone."
    )
    if parse_time_restricted:
        return base + f" With the default --template-url ({DEFAULT_TEMPLATE_URL}), only these values are accepted."
    return (
        base
        + " With a custom --template-url, the value must exist in that template’s skills-map.json "
        + "(the list above matches the official default repository)."
    )


@dataclass(frozen=True)
class CliOptions:
    template_url: str
    ide: tuple[str, ...]
    template_branch: str
    extend: str | None
    extend_branch: str
    skip_example: bool
    skip_navigation_file: bool
    skip_hla_file: bool


def build_parser(*, ide_choices: list[str] | None = None, ide_help: str | None = None) -> argparse.ArgumentParser:
    epilog = """
ZIP vs Git:
  If the URL path ends with .zip (case-insensitive), the tool downloads and extracts
  the archive. Otherwise it runs git clone (requires git on PATH), using
  --template-branch for --template-url and --extend-branch for --extend.
  The same rule applies to --extend when that option is used.

Default --template-url is the official Spectask GitHub repository (.git); use a .zip URL
  to avoid git for the template step only.
""".strip()
    p = argparse.ArgumentParser(
        description="Bootstrap Spectask template files into the current directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    p.add_argument(
        "--template-url",
        default=DEFAULT_TEMPLATE_URL,
        metavar="URL",
        help=f"Template source (ZIP or Git). Default: {DEFAULT_TEMPLATE_URL}",
    )
    if ide_choices is not None:
        p.add_argument(
            "--ide",
            required=False,
            nargs="+",
            default=None,
            choices=ide_choices,
            metavar="IDE",
            help=ide_help,
        )
    else:
        p.add_argument("--ide", required=False, nargs="+", default=None, metavar="IDE", help=ide_help)
    p.add_argument("--template-branch", default="main", help="Git branch for template URL when not ZIP (default: main).")
    p.add_argument("--extend", default=None, help="Optional overlay source (ZIP or Git) for spec/extend/.")
    p.add_argument("--extend-branch", default="main", help="Git branch for --extend when not ZIP (default: main).")
    p.add_argument("--skip-example", action="store_true", help="Do not copy example-list.json paths.")
    p.add_argument(
        "--skip-navigation-file",
        action="store_true",
        help=(
            "Do not copy spec/navigation.md from required-list. "
            "Advanced merge use case; Spectask normally expects this file."
        ),
    )
    p.add_argument(
        "--skip-hla-file",
        action="store_true",
        help=(
            "Do not copy spec/design/hla.md from required-list. "
            "Advanced merge use case; Spectask normally keeps HLA in this file."
        ),
    )
    p.add_argument(
        "--update",
        action="store_true",
        help=(
            "Apply --skip-example, --skip-navigation-file, and --skip-hla-file. "
            "When --ide is omitted, default to auto (same as --ide auto). "
            "Explicit --ide values are unchanged."
        ),
    )
    return p


def parse_args(argv: list[str] | None = None) -> CliOptions:
    template_url = _template_url_from_argv(argv)
    restricted = template_url == DEFAULT_TEMPLATE_URL
    p = build_parser(
        ide_choices=_ide_choices_for_template_url(template_url),
        ide_help=_ide_argument_help(parse_time_restricted=restricted),
    )
    ns = p.parse_args(argv)
    if ns.ide is None:
        if not ns.update:
            p.error("--ide is required unless --update is passed")
        ns.ide = ["auto"]
    if "auto" in ns.ide and len(ns.ide) > 1:
        p.error("'auto' cannot be combined with other --ide values")
    if "all" in ns.ide and len(ns.ide) > 1:
        p.error("'all' cannot be combined with other --ide values")
    skip_example = ns.skip_example or ns.update
    skip_navigation_file = ns.skip_navigation_file or ns.update
    skip_hla_file = ns.skip_hla_file or ns.update
    return CliOptions(
        template_url=ns.template_url,
        ide=tuple(ns.ide),
        template_branch=ns.template_branch,
        extend=ns.extend,
        extend_branch=ns.extend_branch,
        skip_example=skip_example,
        skip_navigation_file=skip_navigation_file,
        skip_hla_file=skip_hla_file,
    )


def main() -> None:
    opts = parse_args()
    try:
        run_template_bootstrap(
            template_url=opts.template_url,
            ide=opts.ide,
            skip_example=opts.skip_example,
            skip_navigation_file=opts.skip_navigation_file,
            skip_hla_file=opts.skip_hla_file,
            template_branch=opts.template_branch,
        )
    except (OSError, RuntimeError, zipfile.BadZipFile) as e:
        print(f"spectask-init: {e}", file=sys.stderr)
        sys.exit(1)

    if opts.extend:
        try:
            run_extend(extend_url=opts.extend, extend_branch=opts.extend_branch)
        except (OSError, RuntimeError, zipfile.BadZipFile) as e:
            print(f"spectask-init: {e}", file=sys.stderr)
            sys.exit(1)
