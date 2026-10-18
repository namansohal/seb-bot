"""
Premium Developer UI for SEB Bot.

Provides:
- Premium dark response windows
- Gemini chat window
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
from constants import POPUP_GEOMETRY, TYPE_BUTTON_COUNTDOWN_SECONDS, FOCUS_REGAIN_DELAY


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
SUBTLE = "#484f58"

ACCENT = "#58a6ff"
ACCENT_HOVER = "#79b8ff"

SUCCESS = "#3fb950"
ERROR = "#f85149"
WARNING = "#d29922"

TYPE_ELIGIBLE_TAGS = ("SOLVE", "FIX")


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def _configure_window(root: tk.Tk, title: str, geometry: str):
    root.title(title)
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.geometry(geometry)
    root.minsize(520, 420)


def _add_top_bar(root: tk.Tk, title: str, subtitle: str = ""):
    top = tk.Frame(
        root,
        bg=BG,
        height=62,
    )
    top.pack(fill="x", padx=22, pady=(16, 0))
    top.pack_propagate(False)

    left = tk.Frame(top, bg=BG)
    left.pack(side="left", fill="y")

    tk.Label(
        left,
        text=title,
        bg=BG,
        fg=FG,
        font=("Segoe UI Semibold", 14),
    ).pack(anchor="w")

    if subtitle:
        tk.Label(
            left,
            text=subtitle,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

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
        font=("Segoe UI", 20),
        padx=8,
        cursor="hand2",
    )
    close_button.pack(side="right", anchor="n")


def _create_separator(parent):
    return tk.Frame(
        parent,
        bg=BORDER,
        height=1,
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

    # Main content card
    card = tk.Frame(
        root,
        bg=SURFACE,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    card.pack(
        fill="both",
        expand=True,
        padx=22,
        pady=(4, 14),
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
        padx=18,
        pady=18,
        spacing1=2,
        spacing3=6,
    )

    txt.pack(
        fill="both",
        expand=True,
    )

    txt.insert("1.0", content)
    txt.config(state="disabled")

    # Bottom controls
    controls = tk.Frame(
        root,
        bg=BG,
    )
    controls.pack(
        fill="x",
        padx=22,
        pady=(0, 18),
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
        padx=18,
        pady=8,
        font=("Segoe UI Semibold", 9),
        cursor="hand2",
    )
    copy_button.pack(side="left")

    def make_type_btn():
        """Button that counts down then types the content into the editor."""

        btn = tk.Button(
            controls,
            text=f"Type in editor  ·  {TYPE_BUTTON_COUNTDOWN_SECONDS}s",
            bg=ACCENT,
            fg="#ffffff",
            activebackground=ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

        btn.pack(side="left", padx=(8, 0))

        def countdown():
            for i in range(TYPE_BUTTON_COUNTDOWN_SECONDS - 1, 0, -1):
                time.sleep(1)

                try:
                    btn.config(
                        text=f"Type in editor  ·  {i}s"
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
                text="Preparing..."
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
    """Open a dedicated Gemini chat window."""

    def _run():
        try:
            chat = create_chat()

        except Exception as e:
            root = tk.Tk()

            _configure_window(
                root,
                "SEB Bot · Error",
                "520x320",
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
                padx=22,
                pady=(4, 22),
            )

            tk.Label(
                card,
                text="Chat could not be started",
                bg=SURFACE,
                fg=ERROR,
                font=("Segoe UI Semibold", 12),
            ).pack(
                anchor="w",
                padx=20,
                pady=(24, 8),
            )

            tk.Label(
                card,
                text=str(e),
                bg=SURFACE,
                fg=FG,
                font=("Segoe UI", 10),
                wraplength=460,
                justify="left",
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 20),
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
                padx=18,
                pady=8,
                font=("Segoe UI Semibold", 9),
                cursor="hand2",
            ).pack(
                anchor="w",
                padx=20,
            )

            root.mainloop()
            return

        # ---------------------------------------------------------------
        # Chat window
        # ---------------------------------------------------------------

        root = tk.Tk()

        _configure_window(
            root,
            "SEB Bot · Gemini",
            "820x680",
        )

        _add_top_bar(
            root,
            "SEB Bot",
            "Gemini · Developer Assistant",
        )

        # Online/status indicator
        status = tk.Frame(
            root,
            bg=BG,
        )
        status.pack(
            fill="x",
            padx=22,
            pady=(0, 12),
        )

        tk.Label(
            status,
            text="●",
            bg=BG,
            fg=SUCCESS,
            font=("Segoe UI", 9),
        ).pack(side="left")

        tk.Label(
            status,
            text=" Gemini",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(side="left")

        # ---------------------------------------------------------------
        # Conversation card
        # ---------------------------------------------------------------

        conversation_card = tk.Frame(
            root,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        conversation_card.pack(
            fill="both",
            expand=True,
            padx=22,
            pady=(0, 12),
        )

        conversation = scrolledtext.ScrolledText(
            conversation_card,
            wrap=tk.WORD,
            bg=SURFACE,
            fg=FG,
            insertbackground=FG,
            selectbackground="#264f78",
            selectforeground=FG,
            font=("Cascadia Code", 10),
            relief="flat",
            bd=0,
            padx=20,
            pady=18,
            spacing1=3,
            spacing3=8,
            state="disabled",
        )

        conversation.pack(
            fill="both",
            expand=True,
        )

        # Message styles
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
            font=("Cascadia Code", 10),
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
        input_card.pack(
            fill="x",
            padx=22,
            pady=(0, 18),
        )

        user_input = tk.Text(
            input_card,
            height=3,
            wrap=tk.WORD,
            bg=SURFACE,
            fg=FG,
            insertbackground=ACCENT,
            selectbackground="#264f78",
            selectforeground=FG,
            font=("Cascadia Code", 10),
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
        )

        user_input.pack(
            side="left",
            fill="both",
            expand=True,
        )

        send_button = tk.Button(
            input_card,
            text="Send  ↑",
            bg=ACCENT,
            fg="#ffffff",
            activebackground=ACCENT_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

        send_button.pack(
            side="right",
            padx=10,
            pady=10,
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
                text="Thinking..."
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
                            text="Send  ↑",
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
                            text="Send  ↑",
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
            # Ctrl+Enter sends the message.
            # Normal Enter creates a new line.
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