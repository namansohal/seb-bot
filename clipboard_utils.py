"""
Clipboard operations — single source of truth for clipboard logic.
Used by the main tag handlers and the popup window's copy button.
"""


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to the system clipboard.

    Tries pyperclip first, then falls back to Tkinter.

    Returns True on success, False on failure.
    """
    try:
        import pyperclip

        pyperclip.copy(text)

        print(f"[clipboard] Copied {len(text)} characters.")
        return True

    except Exception as e:
        print(
            f"[clipboard] pyperclip failed ({e}), "
            "trying Tk fallback..."
        )

    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()

        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()

        root.destroy()

        print(f"[clipboard] Copied {len(text)} characters using Tk.")
        return True

    except Exception as e:
        print(f"[clipboard] Tk fallback also failed: {e}")
        return False


def get_clipboard_text() -> str:
    """
    Return the current system clipboard text.

    Also prints the clipboard contents to the console so we can
    verify exactly what is currently stored.
    """
    try:
        import pyperclip

        text = pyperclip.paste()

        if text:
            print(
                f"[clipboard] Current clipboard "
                f"({len(text)} characters):"
            )
            print("----------------------------------------")
            print(text)
            print("----------------------------------------")
        else:
            print("[clipboard] Clipboard is EMPTY.")

        return text

    except Exception as e:
        print(f"[clipboard] Could not read clipboard: {e}")
        return ""


def show_clipboard():
    """
    Read and display the current clipboard contents.

    Returns the clipboard text.
    """
    return get_clipboard_text()