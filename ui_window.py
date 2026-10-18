"""
Premium Developer UI for SEB Bot.

Provides:
- Compact premium dark response windows
- Compact Gemini chat window
- Copy button
- Countdown/type button
- Always-on-top behavior
- Ctrl+Enter to send chat messages
"""

import threading
import time
import tkinter as tk
from tkinter import scrolledtext
from typing import Optional

import keyboard_input
from clipboard_utils import copy_to_clipboard
from ai_provider import create_chat
from constants import (
    POPUP_GEOMETRY,
    TYPE_BUTTON_COUNTDOWN_SECONDS,
    FOCUS_REGAIN_DELAY,
)


_lock = threading.Lock()
_active_root: Optional[tk.Tk] = None


# ---------------------------------------------------------------------------
# Premium Developer theme
# ---------------------------------------------------------------------------

BG = "#0d1117"
SURFACE = "#151b23"
SURFACE_HOVER = "#1c2530"
BORDER = "#263241"

FG = "#e6edf3"
MUTED = "#7d8590"

ACCENT = "#58a6ff"
ACCENT_HOVER = "#79b8ff"

SUCCESS = "#3fb950"
ERROR = "#f85149"
WARNING = "#d29922"

TYPE_ELIGIBLE_TAGS = ("SOLVE", "FIX")


# ---------------------------------------------------------------------------
# Window helpers
# ---------------------------------------------------------------------------

def _configure_window(root: tk.Tk, title: str, geometry: str):
    root.title(title)
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.geometry(geometry)
    root.resizable(True, True)


def _add_top_bar(root: tk.Tk, title: str, subtitle: str = ""):
    top = tk.Frame(
        root,
        bg=BG,
        height=52,
    )
    top.pack(
        fill="x",
        padx=18,
        pady=(10, 0),
    )
    top.pack_propagate(False)

    left = tk.Frame(top, bg=BG)
    left.pack(side="left", fill="y")

    tk.Label(
        left,
        text=title,
        bg=BG,
        fg=FG,
        font=("Segoe UI Semibold", 13),
    ).pack(anchor="w")

    if subtitle:
        tk.Label(
            left,
            text=subtitle,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w")

    close_button = tk.Button(
        top,
        text="×",
        command=root.destroy,
        bg=BG,
        fg=MUTED,
        activebackground=BG,
        activeforeground=FG,
        relief="flat",
        bd=0,
        font=("Segoe UI", 19),
        padx=6,
        cursor="hand2",
    )
    close_button.pack(
        side="right",
        anchor="n",
    )


# ---------------------------------------------------------------------------
# Normal response window
# ---------------------------------------------------------------------------

def _build_window(tag_type: str, content: str) -> tk.Tk:
    root = tk.Tk()

    _configure_window(
        root,
        f"SEB Bot · {tag_type}",
        POPUP_GEOMETRY,
    )

    accent = ACCENT

    if tag_type == "FIX":
        accent = WARNING
    elif tag_type == "SOLVE":
        accent = SUCCESS
    elif tag_type == "ERROR":
        accent = ERROR

    _add_top_bar(
        root,
        "SEB Bot",
        f"{tag_type} · Response",
    )

    card = tk.Frame(
        root,
        bg=SURFACE,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    card.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=(4, 10),
    )

    txt = scrolledtext.ScrolledText(
        card,
        wrap=tk.WORD,
        bg=SURFACE,
        fg=FG,
        insertbackground=FG,
        selectbackground="#264f78",
        selectforeground=FG,
        font=("Cascadia Code", 10),
        relief="flat",
        bd=0,
        padx=14,
        pady=14,
        spacing1=2,
        spacing3=6,
    )

    txt.pack(
        fill="both",
        expand=True,
    )

    txt.insert("1.0", content)
    txt.config(state="disabled")

    controls = tk.Frame(
        root,
        bg=BG,
    )
    controls.pack(
        fill="x",
        padx=18,
        pady=(0, 12),
    )

    def copy_clip():
        copy_to_clipboard(content)

    copy_button = tk.Button(
        controls,
        text="Copy",
        command=copy_clip,
        bg=SURFACE,
        fg=FG,
        activebackground=SURFACE_HOVER,
        activeforeground=FG,
        relief="flat",
        bd=0,
        highlightbackground=BORDER,
        highlightthickness=1,
        padx=16,
        pady=7,
        font=("Segoe UI Semibold", 9),
        cursor="hand2",
    )
    copy_button.pack(side="left")

    def make_type_btn():
        btn = tk.Button(
            controls,
            text=f"Type in editor · {TYPE_BUTTON_COUNTDOWN_SECONDS}s",
            bg=accent,
            fg="#ffffff",
            activebackground=ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=16,
            pady=7,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

        btn.pack(
            side="left",
            padx=(7, 0),
        )

        def countdown():
            for i in range(TYPE_BUTTON_COUNTDOWN_SECONDS - 1, 0, -1):
                time.sleep(1)

                try:
                    btn.config(
                        text=f"Type in editor · {i}s"
                    )
                except Exception:
                    return

            time.sleep(1)

            try:
                root.destroy()
            except Exception:
                pass

            time.sleep(FOCUS_REGAIN_DELAY)

            keyboard_input.type_text(content)

        def on_click():
            btn.config(
                state="disabled",
                text="Preparing...",
            )

            threading.Thread(
                target=countdown,
                daemon=True,
            ).start()

        btn.config(command=on_click)

    if tag_type in TYPE_ELIGIBLE_TAGS:
        make_type_btn()

    return root


def show(tag_type: str, content: str):
    """Open or replace the floating response window."""

    global _active_root

    def _run():
        global _active_root

        with _lock:
            if _active_root:
                try:
                    _active_root.destroy()
                except Exception:
                    pass

            root = _build_window(tag_type, content)
            _active_root = root

        root.mainloop()

        with _lock:
            if _active_root is root:
                _active_root = None

    threading.Thread(
        target=_run,
        daemon=True,
    ).start()


# ---------------------------------------------------------------------------
# Gemini chat window
# ---------------------------------------------------------------------------

def show_chat():
    """Open a compact dedicated Gemini chat window."""

    def _run():
        try:
            chat = create_chat()

        except Exception as e:
            root = tk.Tk()

            _configure_window(
                root,
                "SEB Bot · Error",
                "520x300",
            )

            _add_top_bar(
                root,
                "SEB Bot",
                "Unable to start chat",
            )

            card = tk.Frame(
                root,
                bg=SURFACE,
                highlightbackground=BORDER,
                highlightthickness=1,
            )
            card.pack(
                fill="both",
                expand=True,
                padx=18,
                pady=(4, 18),
            )

            tk.Label(
                card,
                text="Chat could not be started",
                bg=SURFACE,
                fg=ERROR,
                font=("Segoe UI Semibold", 11),
            ).pack(
                anchor="w",
                padx=16,
                pady=(18, 6),
            )

            tk.Label(
                card,
                text=str(e),
                bg=SURFACE,
                fg=FG,
                font=("Segoe UI", 9),
                wraplength=460,
                justify="left",
            ).pack(
                anchor="w",
                padx=16,
                pady=(0, 14),
            )

            tk.Button(
                card,
                text="Close",
                command=root.destroy,
                bg=SURFACE_HOVER,
                fg=FG,
                activebackground=BORDER,
                activeforeground=FG,
                relief="flat",
                bd=0,
                padx=16,
                pady=7,
                font=("Segoe UI Semibold", 9),
                cursor="hand2",
            ).pack(
                anchor="w",
                padx=16,
            )

            root.mainloop()
            return

        # ---------------------------------------------------------------
        # Compact chat window
        # ---------------------------------------------------------------

        root = tk.Tk()

        _configure_window(
            root,
            "SEB Bot · Gemini",
            "600x480",
        )

        root.minsize(
            500,
            380,
        )

        # Main window uses GRID so the input area can never be pushed
        # below the visible window.
        root.grid_rowconfigure(0, weight=0)
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=0)

        root.grid_columnconfigure(0, weight=1)

        # ---------------------------------------------------------------
        # Header
        # ---------------------------------------------------------------

        header = tk.Frame(
            root,
            bg=BG,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=18,
            pady=(10, 8),
        )

        header.grid_columnconfigure(0, weight=1)

        left = tk.Frame(
            header,
            bg=BG,
        )
        left.grid(
            row=0,
            column=0,
            sticky="w",
        )

        tk.Label(
            left,
            text="SEB Bot",
            bg=BG,
            fg=FG,
            font=("Segoe UI Semibold", 13),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Gemini · Developer Assistant",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="w")

        tk.Button(
            header,
            text="×",
            command=root.destroy,
            bg=BG,
            fg=MUTED,
            activebackground=BG,
            activeforeground=FG,
            relief="flat",
            bd=0,
            font=("Segoe UI", 19),
            padx=6,
            cursor="hand2",
        ).grid(
            row=0,
            column=1,
            sticky="ne",
        )

        # ---------------------------------------------------------------
        # Conversation
        # ---------------------------------------------------------------

        conversation_card = tk.Frame(
            root,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )

        conversation_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=(0, 8),
        )

        conversation = scrolledtext.ScrolledText(
            conversation_card,
            wrap=tk.WORD,
            bg=SURFACE,
            fg=FG,
            insertbackground=FG,
            selectbackground="#264f78",
            selectforeground=FG,
            font=("Cascadia Code", 9),
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            spacing1=2,
            spacing3=6,
            state="disabled",
        )

        conversation.pack(
            fill="both",
            expand=True,
        )

        conversation.tag_config(
            "user_label",
            foreground=ACCENT,
            font=("Segoe UI Semibold", 9),
        )

        conversation.tag_config(
            "gemini_label",
            foreground=SUCCESS,
            font=("Segoe UI Semibold", 9),
        )

        conversation.tag_config(
            "error_label",
            foreground=ERROR,
            font=("Segoe UI Semibold", 9),
        )

        conversation.tag_config(
            "message",
            foreground=FG,
            font=("Cascadia Code", 9),
        )

        def add_message(sender: str, message: str):
            conversation.config(state="normal")

            if sender == "You":
                label_tag = "user_label"
            elif sender == "Gemini":
                label_tag = "gemini_label"
            else:
                label_tag = "error_label"

            conversation.insert(
                "end",
                f"{sender}\n",
                label_tag,
            )

            conversation.insert(
                "end",
                f"{message}\n\n",
                "message",
            )

            conversation.config(state="disabled")
            conversation.see("end")

        # ---------------------------------------------------------------
        # Input area
        # ---------------------------------------------------------------

        input_card = tk.Frame(
            root,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )

        input_card.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 12),
        )

        input_card.grid_columnconfigure(
            0,
            weight=1,
        )

        user_input = tk.Text(
            input_card,
            height=2,
            wrap=tk.WORD,
            bg=SURFACE,
            fg=FG,
            insertbackground=ACCENT,
            selectbackground="#264f78",
            selectforeground=FG,
            font=("Cascadia Code", 9),
            relief="flat",
            bd=0,
            padx=12,
            pady=9,
        )

        user_input.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 0),
        )

        send_button = tk.Button(
            input_card,
            text="Send ↑",
            bg=ACCENT,
            fg="#ffffff",
            activebackground=ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

        send_button.grid(
            row=0,
            column=1,
            padx=8,
            pady=8,
        )

        # ---------------------------------------------------------------
        # Sending
        # ---------------------------------------------------------------

        def send_message():
            message = user_input.get(
                "1.0",
                "end",
            ).strip()

            if not message:
                return

            user_input.delete(
                "1.0",
                "end",
            )

            send_button.config(
                state="disabled",
                text="...",
            )

            user_input.config(
                state="disabled",
            )

            add_message(
                "You",
                message,
            )

            def worker():
                try:
                    response = chat.send_message(message)

                    reply = getattr(
                        response,
                        "text",
                        None,
                    )

                    if not reply:
                        reply = str(response)

                    def update_ui():
                        add_message(
                            "Gemini",
                            reply,
                        )

                        send_button.config(
                            state="normal",
                            text="Send ↑",
                        )

                        user_input.config(
                            state="normal",
                        )

                        user_input.focus_set()

                    root.after(
                        0,
                        update_ui,
                    )

                except Exception as e:

                    def show_error():
                        add_message(
                            "ERROR",
                            str(e),
                        )

                        send_button.config(
                            state="normal",
                            text="Send ↑",
                        )

                        user_input.config(
                            state="normal",
                        )

                        user_input.focus_set()

                    root.after(
                        0,
                        show_error,
                    )

            threading.Thread(
                target=worker,
                daemon=True,
            ).start()

        send_button.config(
            command=send_message,
        )

        def enter_handler(event):
            if event.state & 0x0001:
                return

            send_message()
            return "break"

        user_input.bind(
            "<Control-Return>",
            enter_handler,
        )

        add_message(
            "Gemini",
            "Ready. Ask me anything about your code or project.",
        )

        user_input.focus_set()

        root.mainloop()

    threading.Thread(
        target=_run,
        daemon=True,
    ).start()