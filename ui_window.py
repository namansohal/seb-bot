"""
Floating response window (always-on-top).
Works alongside SEB when the exam allows other windows.
Includes a countdown button that types the response into the focused editor.
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

TAG_COLORS = {
    "ASK":   "#89dceb",  # light blue
    "SOLVE": "#a6e3a1",  # green
    "FIX":   "#fab387",  # orange
    "COPY":  "#cba6f7",  # purple
    "ERROR": "#f38ba8",  # red
}

BG      = "#1e1e2e"
SURFACE = "#313244"
FG      = "#cdd6f4"
MUTED   = "#6c7086"

TYPE_ELIGIBLE_TAGS = ("SOLVE", "FIX")


def _build_window(tag_type: str, content: str) -> tk.Tk:
    root = tk.Tk()
    root.title(f"SEB Bot · {tag_type}")
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    root.geometry(POPUP_GEOMETRY)
    root.resizable(True, True)

    accent = TAG_COLORS.get(tag_type, FG)

    # ── Header ───────────────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=SURFACE, pady=6)
    hdr.pack(fill="x")
    tk.Label(hdr, text=f"  [{tag_type}]", bg=SURFACE, fg=accent,
             font=("Consolas", 11, "bold")).pack(side="left")
    tk.Button(hdr, text="✖", command=root.destroy,
              bg=SURFACE, fg=MUTED, relief="flat",
              font=("Consolas", 10), bd=0, padx=8).pack(side="right")

    # ── Content ───────────────────────────────────────────────────────────────
    txt = scrolledtext.ScrolledText(
        root, wrap=tk.WORD, bg=BG, fg=FG,
        font=("Consolas", 10), relief="flat",
        padx=10, pady=8, insertbackground=FG,
    )
    txt.pack(fill="both", expand=True, padx=4, pady=4)
    txt.insert("1.0", content)
    txt.config(state="disabled")

    # ── Buttons ───────────────────────────────────────────────────────────────
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(fill="x", padx=6, pady=(0, 6))

    def copy_clip():
        copy_to_clipboard(content)

    def make_type_btn():
        """Button that counts down then types the content into the editor."""
        btn = tk.Button(
            btn_frame,
            text=f"⌨️  כתוב בעורך ({TYPE_BUTTON_COUNTDOWN_SECONDS}...)",
            bg=SURFACE, fg=accent, relief="flat", padx=10,
            font=("Consolas", 9),
        )
        btn.pack(side="left", padx=3)

        def countdown():
            for i in range(TYPE_BUTTON_COUNTDOWN_SECONDS - 1, 0, -1):
                time.sleep(1)
                try:
                    btn.config(text=f"⌨️  כתוב בעורך ({i}...)")
                except Exception:
                    return
            time.sleep(1)
            try:
                root.destroy()
            except Exception:
                pass
            time.sleep(FOCUS_REGAIN_DELAY)  # let SEB editor regain focus
            keyboard_input.type_text(content)

        def on_click():
            btn.config(state="disabled")
            threading.Thread(target=countdown, daemon=True).start()

        btn.config(command=on_click)

    tk.Button(btn_frame, text="📋 העתק", command=copy_clip,
              bg=SURFACE, fg=FG, relief="flat", padx=10,
              font=("Consolas", 9)).pack(side="left", padx=3)

    if tag_type in TYPE_ELIGIBLE_TAGS:
        make_type_btn()

    return root


def show(tag_type: str, content: str):
    """Open (or replace) the floating popup. Thread-safe."""
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

    threading.Thread(target=_run, daemon=True).start()

def show_chat():
    """Open a dedicated Gemini chat window."""
    def _run():
        try:
            chat = create_chat()
        except Exception as e:
            root = tk.Tk()
            root.title("SEB Bot · CHAT")
            root.configure(bg=BG)
            root.attributes("-topmost", True)
            root.geometry(POPUP_GEOMETRY)

            tk.Label(
                root,
                text="CHAT ERROR",
                bg=BG,
                fg=TAG_COLORS["ERROR"],
                font=("Consolas", 11, "bold"),
            ).pack(pady=(15, 5))

            tk.Label(
                root,
                text=str(e),
                bg=BG,
                fg=FG,
                font=("Consolas", 10),
                wraplength=500,
                justify="left",
            ).pack(padx=20, pady=10)

            tk.Button(
                root,
                text="Close",
                command=root.destroy,
                bg=SURFACE,
                fg=FG,
                relief="flat",
                padx=15,
            ).pack(pady=10)

            root.mainloop()
            return

        root = tk.Tk()
        root.title("SEB Bot · CHAT")
        root.configure(bg=BG)
        root.attributes("-topmost", True)
        root.geometry("700x600")
        root.minsize(500, 400)

        # Header
        hdr = tk.Frame(root, bg=SURFACE, pady=6)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text="  [CHAT · GEMINI]",
            bg=SURFACE,
            fg=TAG_COLORS.get("ASK", FG),
            font=("Consolas", 11, "bold"),
        ).pack(side="left")

        tk.Button(
            hdr,
            text="✖",
            command=root.destroy,
            bg=SURFACE,
            fg=MUTED,
            relief="flat",
            font=("Consolas", 10),
            bd=0,
            padx=8,
        ).pack(side="right")

        # Conversation area
        conversation = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            bg=BG,
            fg=FG,
            font=("Consolas", 10),
            relief="flat",
            padx=10,
            pady=8,
            state="disabled",
        )
        conversation.pack(
            fill="both",
            expand=True,
            padx=4,
            pady=4,
        )

        # Input area
        input_frame = tk.Frame(root, bg=BG)
        input_frame.pack(fill="x", padx=6, pady=6)

        user_input = tk.Text(
            input_frame,
            height=4,
            wrap=tk.WORD,
            bg=SURFACE,
            fg=FG,
            insertbackground=FG,
            font=("Consolas", 10),
            relief="flat",
            padx=8,
            pady=8,
        )
        user_input.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 6),
        )

        send_button = tk.Button(
            input_frame,
            text="Send",
            bg=SURFACE,
            fg=TAG_COLORS.get("ASK", FG),
            relief="flat",
            padx=15,
            font=("Consolas", 10, "bold"),
        )
        send_button.pack(side="right", fill="y")

        def add_message(sender: str, message: str):
            conversation.config(state="normal")
            conversation.insert("end", f"{sender}:\n", "sender")
            conversation.insert("end", f"{message}\n\n")
            conversation.config(state="disabled")
            conversation.see("end")

        conversation.tag_config("sender", foreground=TAG_COLORS.get("ASK", FG))

        def send_message():
            message = user_input.get("1.0", "end").strip()

            if not message:
                return

            user_input.delete("1.0", "end")
            send_button.config(state="disabled")
            user_input.config(state="disabled")

            add_message("You", message)

            def worker():
                try:
                    response = chat.send_message(message)

                    reply = getattr(response, "text", None)

                    if not reply:
                        reply = str(response)

                    def update_ui():
                        add_message("Gemini", reply)
                        send_button.config(state="normal")
                        user_input.config(state="normal")
                        user_input.focus_set()

                    root.after(0, update_ui)

                except Exception as e:
                    def show_error():
                        add_message("ERROR", str(e))
                        send_button.config(state="normal")
                        user_input.config(state="normal")
                        user_input.focus_set()

                    root.after(0, show_error)

            threading.Thread(
                target=worker,
                daemon=True,
            ).start()

        send_button.config(command=send_message)

        def enter_handler(event):
            if event.state & 0x0001:
                return

            send_message()
            return "break"

        user_input.bind("<Control-Return>", enter_handler)

        add_message(
            "Gemini",
            "Chat started. Type your message and press Send.\n"
            "Ctrl+Enter also sends the message."
        )

        user_input.focus_set()
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()