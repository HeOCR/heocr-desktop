"""Start the app, or, with ``--smoke OUT FILE...``, convert files without a window and write a JSON
summary to OUT (used by CI on the packaged app, where a window cannot be driven)."""
import sys


def run():
    if len(sys.argv) > 2 and sys.argv[1] == "--smoke":
        from heocr_desktop.smoke import main as smoke
        sys.exit(smoke(sys.argv[2], sys.argv[3:]))
    from heocr_desktop.app import main
    main()


if __name__ == "__main__":
    run()
