"""Entry point for `python3 -m symphony`."""
import sys

# External packages that symphony depends on.
# Only these are caught as "missing dependency" — anything else propagates.
_KNOWN_EXTERNAL_DEPS = frozenset({"jinja2", "yaml", "pyyaml"})


def _main() -> None:
    try:
        from symphony.cli import main  # noqa: WPS433
    except ImportError as e:
        # Only catch missing *known external* packages (jinja2, yaml, etc.)
        # Everything else (internal bugs, typos, unknown packages) propagates.
        pkg = (e.name or "").split(".")[0].lower()
        if pkg in _KNOWN_EXTERNAL_DEPS:
            print(
                f"Error: Missing dependency '{e.name}' — {e}\n"
                "Run: pip install -r sdd-templates/requirements.txt",
                file=sys.stderr,
            )
            sys.exit(1)
        raise
    main()


if __name__ == "__main__":
    _main()
