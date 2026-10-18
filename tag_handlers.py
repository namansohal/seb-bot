"""
Tag handlers — one function per @@TAG@@ type.
Each handler receives (content, full_text) and is responsible for its
own side effects (showing a popup, copying to clipboard, etc).

To add a new tag: write a handler function here and register it in HANDLERS.
"""

import re
from datetime import datetime
from pathlib import Path

import ui_window
import keyboard_input
from ai_provider import ask_ai
from clipboard_utils import copy_to_clipboard, get_clipboard_text
from config import Settings
from constants import (
    ASKALL_CODE_CONTEXT_LIMIT,
    SOLVEALL_FIELD_LIMIT,
    FIX_CONTEXT_LIMIT,
    POPUP_CLIPBOARD_PREVIEW_LENGTH,
    ERROR_MESSAGE_MAX_LENGTH,
)


def _code_above_tag(full_text: str, tag_marker: str) -> str:
    """Return the text preceding the given tag marker (e.g., '@@ASKALL')."""
    tag_pos = full_text.upper().find(tag_marker)
    return full_text[:tag_pos].strip() if tag_pos > 0 else ""


def _truncate(text: str, limit: int, from_end: bool = True) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:] if from_end else text[:limit]


def _deliver_ai_response(tag_type: str, response: str):
    """Send an AI response to the user via the configured response mode."""
    mode = Settings.get("response_mode", "auto")

    if mode == "type":
        keyboard_input.append_below_tag(response)
    else:
        ui_window.show(tag_type, response)


def _format_error(e: Exception) -> str:
    err_str = str(e)

    if "<html" in err_str.lower() or "<!doctype" in err_str.lower():
        return (
            "The API is blocked by a network filter (NetFree?).\n"
            "Try another API or check your NetFree settings."
        )

    if len(err_str) > ERROR_MESSAGE_MAX_LENGTH:
        return err_str[:ERROR_MESSAGE_MAX_LENGTH] + "..."

    return err_str


# ── Handlers ───────────────────────────────────────────────────────────────

def handle_screenshot(content: str, full_text: str):
    try:
        import pyautogui
    except ImportError:
        ui_window.show(
            "ERROR",
            "pyautogui is not installed. Run: pip install pyautogui"
        )
        return

    try:
        filename = (
            f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        save_path = Path(__file__).parent / filename

        img = pyautogui.screenshot()
        img.save(str(save_path))

        ui_window.show(
            "SCREENSHOT",
            f"Screenshot saved:\n\n{save_path}"
        )

        print(f"[Agent] Screenshot saved: {save_path}")

    except Exception as e:
        ui_window.show(
            "ERROR",
            f"Screenshot error:\n{e}"
        )


def handle_sstochat(content: str, full_text: str):
    """
    Take a screenshot and open a Gemini chat with that screenshot
    as the initial conversation context.
    """

    try:
        import pyautogui
    except ImportError:
        ui_window.show(
            "ERROR",
            "pyautogui is not installed. Run: pip install pyautogui"
        )
        return

    try:
        filename = (
            f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        save_path = Path(__file__).parent / filename

        print("[Agent] Taking screenshot for SSTOCHAT...")

        img = pyautogui.screenshot()
        img.save(str(save_path))

        print(
            f"[Agent] Screenshot saved: {save_path}"
        )

        ui_window.show_chat(
            str(save_path)
        )

    except Exception as e:
        ui_window.show(
            "ERROR",
            f"SSTOCHAT error:\n{_format_error(e)}"
        )


def handle_askall(content: str, full_text: str):
    code = _code_above_tag(full_text, "@@ASKALL")

    if not code:
        ui_window.show(
            "ERROR",
            "No code above the tag.\n"
            "Example:\n"
            "  [your code]\n"
            "  @@ASKALL: Why does the loop not stop?@@"
        )
        return

    if not content:
        ui_window.show(
            "ERROR",
            "Write a question inside the tag:\n"
            "@@ASKALL: Your question@@"
        )
        return

    code = _truncate(
        code,
        ASKALL_CODE_CONTEXT_LIMIT
    )

    try:
        print("[Agent] Sending to AI (ASKALL)...")

        response = ask_ai(
            "ASKALL",
            f"Code:\n{code}\n\nQuestion: {content}"
        )

        print(
            f"[Agent] Response received ({len(response)} characters)"
        )

        ui_window.show(
            "ASK",
            response
        )

    except Exception as e:
        ui_window.show(
            "ERROR",
            f"Error:\n{_format_error(e)}"
        )


def handle_solveall(content: str, full_text: str):
    clean = re.sub(
        r'@@SOLVEALL@@',
        '',
        full_text
    ).strip()

    if not clean:
        ui_window.show(
            "ERROR",
            "The field is empty — there is no exercise to read."
        )
        return

    clean = _truncate(
        clean,
        SOLVEALL_FIELD_LIMIT,
        from_end=False
    )

    try:
        print(
            f"[Agent] Sending to AI "
            f"(SOLVEALL, {len(clean)} characters)..."
        )

        response = ask_ai(
            "SOLVEALL",
            clean
        )

        print(
            f"[Agent] Response received ({len(response)} characters)"
        )

        ui_window.show(
            "SOLVE",
            response
        )

    except Exception as e:
        ui_window.show(
            "ERROR",
            f"Error:\n{_format_error(e)}"
        )


def handle_copyall(content: str, full_text: str):
    clean = re.sub(
        r'@@COPYALL@@',
        '',
        full_text
    ).strip()

    if copy_to_clipboard(clean):
        ui_window.show(
            "COPY",
            f"Copied to Clipboard:\n\n"
            f"{clean[:POPUP_CLIPBOARD_PREVIEW_LENGTH]}"
        )
    else:
        ui_window.show(
            "ERROR",
            "Failed to copy to Clipboard"
        )


def handle_copyabove(content: str, full_text: str):
    above = _code_above_tag(
        full_text,
        "@@COPYABOVE@@"
    )

    if not above:
        ui_window.show(
            "COPY",
            "There is no text above the tag."
        )
        return

    if copy_to_clipboard(above):
        ui_window.show(
            "COPY",
            f"Copied to Clipboard:\n\n"
            f"{above[:POPUP_CLIPBOARD_PREVIEW_LENGTH]}"
        )
    else:
        ui_window.show(
            "ERROR",
            "Failed to copy to Clipboard"
        )


def handle_copy(content: str, full_text: str):
    if not content:
        ui_window.show(
            "COPY",
            "Write the text inside the tag: @@COPY: text@@"
        )
        return

    if copy_to_clipboard(content):
        ui_window.show(
            "COPY",
            f"Copied to Clipboard:\n\n"
            f"{content[:POPUP_CLIPBOARD_PREVIEW_LENGTH]}"
        )
    else:
        ui_window.show(
            "ERROR",
            "Failed to copy to Clipboard"
        )


def handle_clipboard(content: str, full_text: str):
    """Show the current clipboard contents in the SEB Bot popup."""

    clipboard_text = get_clipboard_text()

    if clipboard_text:
        ui_window.show(
            "CLIPBOARD",
            clipboard_text[:POPUP_CLIPBOARD_PREVIEW_LENGTH]
        )
    else:
        ui_window.show(
            "CLIPBOARD",
            "Clipboard is empty."
        )


def handle_paste(content: str, full_text: str):
    keyboard_input.paste_from_clipboard_after_two_lines()


def handle_fix(content: str, full_text: str):
    context = _code_above_tag(
        full_text,
        "@@FIX"
    )

    if context:
        context = _truncate(
            context,
            FIX_CONTEXT_LIMIT
        )

    if not content and not context:
        ui_window.show(
            "ERROR",
            "Write an instruction inside the tag:\n"
            "@@FIX: Describe the problem@@\n\n"
            "The code to fix should be above the tag."
        )
        return

    _call_ai_and_deliver(
        "FIX",
        content,
        context
    )


def handle_ask(content: str, full_text: str):
    if not content:
        ui_window.show(
            "ERROR",
            "The tag is empty. Example:\n"
            "@@ASK: What is the difference between a list and a tuple?@@"
        )
        return

    _call_ai_and_deliver(
        "ASK",
        content,
        ""
    )


def handle_solve(content: str, full_text: str):
    if not content:
        ui_window.show(
            "ERROR",
            "The tag is empty. Example:\n"
            "@@SOLVE: Write a function that calculates a factorial@@"
        )
        return

    _call_ai_and_deliver(
        "SOLVE",
        content,
        ""
    )


def _call_ai_and_deliver(
    tag_type: str,
    content: str,
    context: str
):
    print("[Agent] Sending to AI...")

    try:
        response = ask_ai(
            tag_type,
            content,
            context
        )

        print(
            f"[Agent] Response received ({len(response)} characters)"
        )

    except Exception as e:
        ui_window.show(
            "ERROR",
            f"AI communication error:\n\n"
            f"{_format_error(e)}"
        )

        print(
            f"[Agent] AI error: {e}"
        )

        return

    _deliver_ai_response(
        tag_type,
        response
    )


def handle_chat(content: str, full_text: str):
    ui_window.show_chat()


# ── Registry ───────────────────────────────────────────────────────────────

HANDLERS = {
    "SCREENSHOT": handle_screenshot,
    "SSTOCHAT":   handle_sstochat,
    "ASKALL":     handle_askall,
    "SOLVEALL":   handle_solveall,
    "COPYALL":    handle_copyall,
    "COPYABOVE":  handle_copyabove,
    "COPY":       handle_copy,
    "CLIPBOARD":  handle_clipboard,
    "FIX":        handle_fix,
    "ASK":        handle_ask,
    "SOLVE":      handle_solve,
    "CHAT":       handle_chat,
    "PASTE":      handle_paste,
}


def dispatch(
    tag_type: str,
    content: str,
    full_text: str
):
    """Look up and run the handler for tag_type. Logs unknown tags."""

    handler = HANDLERS.get(tag_type)

    if handler is None:
        print(
            f"[Agent] Unknown tag type: {tag_type}"
        )
        return

    handler(
        content,
        full_text
    )