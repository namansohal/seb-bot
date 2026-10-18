"""
SEB Bot — main entry point.
Reads focused control via UIAutomation (no screenshot/OCR unless needed).
Only calls the AI when @@TAG@@ patterns are detected.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import threading

from constants import (
    DEBOUNCE_WITH_CONTENT,
    DEBOUNCE_BARE,
    MAIN_LOOP_POLL_INTERVAL,
    TEXT_PREVIEW_LENGTH,
)

REQUIRED_PACKAGES = {
    "uiautomation": "uiautomation",
    "pyperclip": "pyperclip",
}


def _check_dependencies():
    """Fail fast with a clear message if required packages are missing."""
    missing = []

    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"   pip install {pkg}")
        print("\nOr run: pip install -r requirements.txt")
        sys.exit(1)


_check_dependencies()


try:
    from config import Settings, is_api_key_configured
except Exception as e:
    print(f"Error in settings.json: {e}")
    print("   Fix the value and try again.")
    sys.exit(1)


if not is_api_key_configured(Settings):
    print("Missing API key in settings.json")
    print("Gemini (free): https://aistudio.google.com/apikey")
    print("Add it to the api_key field in settings.json, then run again.")
    sys.exit(1)


from reader import read_focused_text
from detector import peek_tag, is_new, mark_processed, reset as reset_hash
from tag_handlers import dispatch


REPEATABLE_TAGS = {
    "SCREENSHOT",
    "COPYALL",
    "COPYABOVE",
    "SSTOCHAT",
    "SSTOSS",
    "CHAT",
}


def _safe_dispatch(tag_type: str, content: str, full_text: str):
    """Wrapper so exceptions inside a handler don't silently kill the thread."""

    print(
        f"[Agent] @@{tag_type}@@ <- "
        f"'{content[:50]}{'...' if len(content) > 50 else ''}'"
    )

    try:
        dispatch(tag_type, content, full_text)

    except Exception as e:
        print(
            f"[Agent] Unhandled error in handler for "
            f"@@{tag_type}@@: {e}"
        )

        try:
            import ui_window

            ui_window.show("ERROR", f"Unexpected error:\n{e}")

        except Exception:
            pass


def _print_banner():
    print("=" * 55)
    print("  SEB Bot — Running in the background")
    print(f"  Model: {Settings['model']}")
    print(f"  Response mode: {Settings['response_mode']}")
    print("=" * 55)
    print()

    print("Available tags:")
    print("  @@ASK: question@@        -> Short explanation (no full code)")
    print("  @@SOLVE: task@@          -> Full code")
    print("  @@FIX: instruction@@     -> Fix the code above the tag")
    print("  @@COPY: text@@           -> Put specific text into Clipboard")
    print("  @@COPYABOVE@@            -> Put all text above into Clipboard")
    print("  @@COPYALL@@              -> Put all field content into Clipboard")
    print("  @@CLIPBOARD@@            -> Show current Clipboard contents")
    print("  @@PASTE@@                -> Paste Clipboard contents two lines below")
    print("  @@CHAT@@                 -> Open Gemini chat")
    print("  @@SCREENSHOT@@           -> Take a screenshot and save it as PNG")
    print("  @@SSTOCHAT@@             -> Screenshot and open Gemini chat with it")
    print("  @@SSTOSS@@               -> Add another screenshot to current chat")
    print()

    print("Waiting for tags... (Ctrl+C to stop)")
    print()


def main():
    _print_banner()

    last_read_preview = None

    pending_key = None
    pending_since = None
    pending_data = None

    last_processed_key = None

    while True:
        try:
            text = read_focused_text()

            preview = (
                text[:TEXT_PREVIEW_LENGTH].replace("\n", "↵")
                if text
                else "—"
            )

            if preview != last_read_preview:
                print(f"[reader] {preview}")
                last_read_preview = preview

            if text and "@@" in text:
                result = peek_tag(text)

                if result:
                    tag_type, content = result
                    key = f"{tag_type}:{content}"

                    # If the same tag is still present after it has fired,
                    # do nothing. This prevents repeatable tags from firing
                    # continuously while their marker remains in the field.
                    if key == last_processed_key:
                        pending_key = None
                        pending_since = None
                        pending_data = None

                    elif (
                        not is_new(tag_type, content)
                        and tag_type not in REPEATABLE_TAGS
                    ):
                        pending_key = None
                        pending_since = None
                        pending_data = None

                    elif key != pending_key:
                        pending_key = key
                        pending_since = time.time()
                        pending_data = (
                            tag_type,
                            content,
                            text,
                        )

                        print(
                            f"[debounce] Waiting for tag: "
                            f"{key[:40]}"
                        )

                    else:
                        debounce = (
                            DEBOUNCE_BARE
                            if not content
                            else DEBOUNCE_WITH_CONTENT
                        )

                        elapsed = time.time() - pending_since

                        if elapsed >= debounce:
                            print(
                                f"[debounce] Firing! "
                                f"{key[:40]}"
                            )

                            mark_processed(
                                tag_type,
                                content,
                            )

                            last_processed_key = key

                            pending_key = None
                            pending_since = None

                            threading.Thread(
                                target=_safe_dispatch,
                                args=pending_data,
                                daemon=True,
                            ).start()

            # If the tag disappears, allow the same tag to be used again.
            elif last_processed_key:
                reset_hash()
                last_processed_key = None
                pending_key = None
                pending_since = None
                pending_data = None

            # NOTE: We do NOT reset pending when text disappears.
            # The user may have temporarily switched to another window.

        except KeyboardInterrupt:
            print("\n[Agent] Stopped.")
            sys.exit(0)

        except Exception as e:
            print(f"[Agent] Error: {e}")

        time.sleep(MAIN_LOOP_POLL_INTERVAL)


if __name__ == "__main__":
    main()