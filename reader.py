"""
Read text from the active window via Windows UIAutomation.

The reader prefers the largest accessible text containing @@ tags.
This prevents SEB/UIAutomation child controls from returning only
a single character, line, or small fragment of the actual content.
"""

from typing import Optional
from constants import MAX_TREE_SEARCH_DEPTH, MAX_PARENT_WALK_UP


_IGNORE_TITLES = (
    "seb agent",
    "seb bot",
    "cmd.exe",
    "command prompt",
    "powershell",
    "windows terminal",
    "visual studio code",
    "notepad++",
    "notepad",
    "wordpad",
    ".txt",
    ".py",
    "tags_guide",
    "project_summary",
)


def _should_ignore(title: str) -> bool:
    t = (title or "").lower()
    return any(x in t for x in _IGNORE_TITLES)


def _extract(ctrl) -> Optional[str]:
    """
    Extract the best available text from one UIAutomation control.
    """
    values = []

    for getter in [
        lambda c: c.GetValuePattern().Value,
        lambda c: c.GetTextPattern().DocumentRange.GetText(-1),
        lambda c: c.Name,
    ]:
        try:
            v = getter(ctrl)

            if v and v.strip():
                values.append(v)

        except Exception:
            pass

    if not values:
        return None

    # Prefer the longest accessible representation.
    return max(values, key=len)


def _search_tree(ctrl, depth: int) -> Optional[str]:
    """
    Search the UIAutomation tree and return the longest text
    containing @@ rather than the first matching child.
    """
    if depth > MAX_TREE_SEARCH_DEPTH:
        return None

    best = None

    try:
        v = _extract(ctrl)

        if v and "@@" in v:
            best = v

        for child in ctrl.GetChildren():
            result = _search_tree(child, depth + 1)

            if result and "@@" in result:
                if best is None or len(result) > len(best):
                    best = result

    except Exception:
        pass

    return best


def read_focused_text() -> Optional[str]:
    """
    Read the largest accessible text containing @@ from the
    currently focused/foreground control.

    1. Check the focused control.
    2. Walk up its parents.
    3. Search the foreground window tree if necessary.
    4. Prefer the longest matching text.
    5. Ignore the bot's own terminal/windows.
    """

    try:
        import uiautomation as auto
    except ImportError:
        print(
            "[reader] uiautomation not installed. "
            "Run: pip install uiautomation"
        )
        return None

    try:
        fg = auto.GetForegroundControl()

        if fg and _should_ignore(fg.Name):
            return None

        best = None

        # ---------------------------------------------------------------
        # Step 1: focused control
        # ---------------------------------------------------------------

        ctrl = auto.GetFocusedControl()

        if ctrl:
            v = _extract(ctrl)

            if v and "@@" in v:
                best = v

            # -----------------------------------------------------------
            # Step 2: walk up parent controls
            # -----------------------------------------------------------

            parent = ctrl.GetParentControl()

            for _ in range(MAX_PARENT_WALK_UP):
                if parent is None:
                    break

                v = _extract(parent)

                if v and "@@" in v:
                    if best is None or len(v) > len(best):
                        best = v

                try:
                    parent = parent.GetParentControl()
                except Exception:
                    break

        if best:
            return best

        # ---------------------------------------------------------------
        # Step 3: full foreground tree search
        # ---------------------------------------------------------------

        if fg:
            return _search_tree(fg, depth=0)

    except Exception as e:
        if "Catastrophic" not in str(e):
            print(f"[reader] error: {e}")

    return None