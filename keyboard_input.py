"""
Keyboard input helpers for SEB Bot.

Uses Windows keyboard events for reliable keyboard simulation,
including Ctrl+V into the currently focused SEB control.
"""

import ctypes
import time

from config import Settings
from constants import KEY_PRESS_DELAY, KEY_PRESS_DELAY_SHORT


# Windows virtual-key codes
VK_CONTROL = 0x11
VK_V = 0x56
VK_END = 0x23
VK_RETURN = 0x0D

# Windows keyboard event flags
KEYEVENTF_KEYUP = 0x0002


user32 = ctypes.WinDLL("user32", use_last_error=True)

# keybd_event is the Windows keyboard-event API.
user32.keybd_event.argtypes = [
    ctypes.c_ubyte,
    ctypes.c_ubyte,
    ctypes.c_ulong,
    ctypes.c_void_p,
]

user32.keybd_event.restype = None


def _send_key(vk_code: int, key_up: bool = False) -> bool:
    """Send one keyboard event through Windows."""

    flags = KEYEVENTF_KEYUP if key_up else 0

    try:
        user32.keybd_event(
            vk_code,
            0,
            flags,
            None,
        )
        return True

    except Exception as e:
        print(
            f"[keyboard_input] Windows key event failed "
            f"for VK {vk_code}: {e}"
        )
        return False


def _press_key(vk_code: int) -> bool:
    """Press and release a key."""

    if not _send_key(vk_code):
        return False

    time.sleep(KEY_PRESS_DELAY_SHORT)

    return _send_key(vk_code, key_up=True)


def _ctrl_v() -> bool:
    """Send an actual Ctrl+V key combination."""

    # Press Ctrl.
    if not _send_key(VK_CONTROL):
        return False

    time.sleep(KEY_PRESS_DELAY_SHORT)

    # Press V.
    if not _send_key(VK_V):
        _send_key(VK_CONTROL, key_up=True)
        return False

    time.sleep(KEY_PRESS_DELAY_SHORT)

    # Release V.
    _send_key(VK_V, key_up=True)

    time.sleep(KEY_PRESS_DELAY_SHORT)

    # Release Ctrl.
    _send_key(VK_CONTROL, key_up=True)

    return True


def type_text(text: str):
    """Simulate keystrokes to type text into the active window."""

    delay = Settings.get("type_speed", 0.015)

    # Prefer the keyboard library for normal text typing.
    try:
        import keyboard

        keyboard.write(text, delay=delay)
        return

    except ImportError:
        pass

    except Exception as e:
        print(f"[keyboard_input] keyboard library failed: {e}")

    # Fallback to pyautogui.
    try:
        import pyautogui

        pyautogui.write(text, interval=delay)

    except ImportError:
        print(
            "[keyboard_input] Neither 'keyboard' nor "
            "'pyautogui' is installed."
        )

    except Exception as e:
        print(f"[keyboard_input] Could not type text: {e}")


def paste_from_clipboard():
    """Paste the current clipboard contents into the focused control."""

    try:
        return _ctrl_v()

    except Exception as e:
        print(f"[keyboard_input] Could not paste from clipboard: {e}")
        return False


def paste_from_clipboard_after_two_lines():
    """
    Move to the end of the @@PASTE@@ line,
    create two new lines,
    then perform the actual Ctrl+V.
    """

    try:
        # Move to the end of the current @@PASTE@@ line.
        if not _press_key(VK_END):
            return False

        time.sleep(KEY_PRESS_DELAY)

        # Create the first blank line.
        if not _press_key(VK_RETURN):
            return False

        time.sleep(KEY_PRESS_DELAY_SHORT)

        # Create the second blank line.
        if not _press_key(VK_RETURN):
            return False

        time.sleep(KEY_PRESS_DELAY_SHORT)

        # Perform the actual Ctrl+V.
        return _ctrl_v()

    except Exception as e:
        print(
            f"[keyboard_input] Could not paste after two lines: {e}"
        )
        return False


def append_below_tag(response: str):
    """
    Fallback mode when popup is blocked.

    Moves to the end of the tag line,
    creates two new lines,
    and types the response.
    """

    try:
        import keyboard

        keyboard.press_and_release("end")
        time.sleep(KEY_PRESS_DELAY)

        keyboard.press_and_release("enter")
        time.sleep(KEY_PRESS_DELAY_SHORT)

        keyboard.press_and_release("enter")
        time.sleep(KEY_PRESS_DELAY_SHORT)

        type_text(response)

    except ImportError:
        print(
            "[keyboard_input] 'keyboard' library is not installed "
            "— cannot append text."
        )

    except Exception as e:
        print(
            f"[keyboard_input] append_below_tag error: {e}"
        )