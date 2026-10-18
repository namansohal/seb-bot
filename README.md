# SEB Bot — AI Assistant for Safe Exam Browser

A background agent that helps students work efficiently within Safe Exam Browser (SEB) environments by providing AI-powered code assistance, clipboard management, screenshots, and other productivity features.

## Problem

Safe Exam Browser blocks essential features:
- Copy/Paste (Ctrl+C, Ctrl+V)
- Screenshots (PrintScreen)
- External applications

This makes working on coding tasks unnecessarily difficult.

## Solution

SEB Bot runs as a background Windows process and uses **Windows UIAutomation** to:
- Read your code directly from the editor
- Detect special tags (`@@ASK:`, `@@SOLVE:`, etc.)
- Send requests to an AI provider (Gemini, Groq, or Mistral)
- Return answers in a floating window
- Handle clipboard operations directly from the OS level
- Support persistent Gemini chats
- Send screenshots to Gemini as visual context

## Features

| Tag | Purpose | Example |
|-----|---------|---------|
| `@@ASK: question@@` | Get a short explanation | `@@ASK: How do I reverse a list?@@` |
| `@@SOLVE: task@@` | Generate complete code | `@@SOLVE: Write a function that calculates factorial@@` |
| `@@FIX: instruction@@` | Fix your code | `@@FIX: Make this more efficient@@` |
| `@@COPY: text@@` | Copy specific text | `@@COPY: my-password-123@@` |
| `@@COPYABOVE@@` | Copy everything above the tag | — |
| `@@COPYALL@@` | Copy entire field content | — |
| `@@SCREENSHOT@@` | Take a screenshot | — |
| `@@ASKALL: question@@` | Ask about code above | `@@ASKALL: Why isn't this working?@@` |
| `@@SOLVEALL@@` | Solve entire exercise | — |
| `@@CLIPBOARD@@` | Use clipboard content | `@@CLIPBOARD@@` |
| `@@PASTE@@` | Paste clipboard content | `@@PASTE@@` |
| `@@CHAT@@` | Open a persistent Gemini chat | `@@CHAT@@` |
| `@@SSTOCHAT@@` | Start Gemini chat with a screenshot | `@@SSTOCHAT@@` |
| `@@SSTOSS@@` | Add another screenshot to current chat | `@@SSTOSS@@` |

## Technologies Used

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | **Python 3.8+** | Core implementation |
| UI reading | **Windows UIAutomation** (`uiautomation`) | Reads editor text |
| AI providers | **Google Gemini**, **Groq**, **Mistral AI** | AI backends |
| Response UI | **tkinter** | Always-on-top floating response window |
| Clipboard | **pyperclip** | Clipboard operations |
| Keyboard simulation | **keyboard** / **pyautogui** | Keyboard input |
| Screenshots | **Pillow** + **pyautogui** | Screen capture |
| HTTP (Mistral) | **requests** | Mistral API requests |
| Config | **JSON** | Application configuration |

## Installation

### Prerequisites

- Python 3.8+
- Windows
- An API key from one of:
  - [Google Gemini](https://aistudio.google.com/apikey)
  - [Groq](https://console.groq.com/keys)
  - [Mistral AI](https://console.mistral.ai/api-keys)

### Setup

1. **Clone or download** this repository
2. **Run installation**:
   ```bash
   scripts\install.bat
   ```
3. **Configure API key**:
   - Copy `settings.example.json` to `settings.json`
   - Add your API key to `settings.json`
4. **Start the bot**:
   ```bash
   scripts\start.bat
   ```

## Usage

Type a supported tag in the editor.

Example:

```text
@@ASK: How does binary search work?@@
```

For a persistent Gemini chat:

```text
@@CHAT@@
```

To start a Gemini chat with a screenshot:

```text
@@SSTOCHAT@@
```

To add another screenshot to the same chat:

```text
@@SSTOSS@@
```

`@@SSTOSS@@` adds the new screenshot to the currently active screenshot-aware Gemini chat.

## Configuration

Edit `settings.json`:

```json
{
  "api_key": "your-key-here",
  "provider": "",
  "model": "gemini-2.0-flash-lite",
  "response_mode": "auto",
  "poll_interval": 1.0,
  "type_speed": 0.015,
  "language": "he"
}
```

- **provider**: `""` (auto-detect), `"gemini"`, `"groq"`, or `"mistral"`
- **response_mode**: `"auto"` (pop-up window) or `"type"` (direct typing)
- **type_speed**: Delay between characters when typing
- **language**: `"he"` (Hebrew) or `"en"` (English)

Settings are validated at startup.

## How It Works

```text
1. You type @@TAG: content@@
      ↓
2. Main loop reads the focused window
      ↓
3. Detector finds the tag
      ↓
4. Debounce waits for typing to finish
      ↓
5. The appropriate handler is executed
      ↓
6. AI request is sent when required
      ↓
7. Response appears in the floating window
```

For screenshot-aware Gemini chat:

```text
@@SSTOCHAT@@
      ↓
Screenshot is captured
      ↓
Gemini chat is opened
      ↓
Screenshot is added as visual context
```

Then:

```text
@@SSTOSS@@
```

captures another screenshot and adds it to the existing chat.

## Key Technical Points

- Uses **Windows UIAutomation** for reading editor content
- Uses **regex** for tag detection
- Uses **debouncing** to prevent incomplete requests
- Uses **hash-based deduplication** to avoid duplicate requests
- Supports **repeatable tags**
- Supports multiple AI providers
- Supports persistent Gemini conversations
- Supports multiple screenshots in screenshot-aware Gemini chats

## Architecture

```text
main.py              — Main loop, debouncing, tag detection, dispatch
config.py            — Settings loading + validation
constants.py         — Application constants
reader.py            — Text reading via UIAutomation
detector.py          — Tag detection + deduplication
ai_provider.py       — Gemini / Groq / Mistral
tag_handlers.py      — Tag handlers
ui_window.py         — Response and chat windows
keyboard_input.py    — Automated typing
clipboard_utils.py   — Clipboard operations

settings.json         — Local configuration
settings.example.json — Configuration template

scripts/
├── install.bat      — One-time dependency installation
└── start.bat        — Start the bot

docs/
├── HOW_IT_WORKS.html   — Technical walkthrough
├── TAGS_GUIDE.txt      — Tag reference
├── PROJECT_SUMMARY.txt — Project overview
└── shortcut.txt        — Shortcut reference
```

Each module has a single responsibility: `reader.py` reads text, `detector.py` recognizes tags, `ai_provider.py` communicates with LLMs, `tag_handlers.py` handles tag actions, and `main.py` connects everything together.

## Security & Privacy

Important:
- `settings.json` is not pushed to GitHub
- Never share your API key
- Never commit `settings.json`
- API requests are sent to the selected AI provider
- Check the privacy policy of your selected provider

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Missing API key" | `settings.json` not configured | Add your API key |
| Missing dependency | Package not installed | Run `scripts\install.bat` |
| Tag not detected | Invalid tag format | Check the `@@TAG@@` format |
| No response | Tag is still being processed | Wait briefly |
| 429 Too Many Requests | Provider rate limit | The bot retries automatically |
| `SSTOCHAT` not working | Gemini is not selected | Select the Gemini provider |
| `SSTOSS` not working | No active screenshot chat | Start with `@@SSTOCHAT@@` |

## Development

To contribute or modify:

1. Clone the repository
2. Install dependencies:
   `pip install -r requirements.txt`
3. Modify the relevant module
4. Test the changes
5. Submit a pull request

To add a new tag, create a handler in `tag_handlers.py` and register it in the `HANDLERS` dictionary.

To add a new AI provider, add its implementation in `ai_provider.py` and register it with the provider selection logic.

## License

MIT License — See [LICENSE](LICENSE) file

## Disclaimer

This tool is designed for educational purposes with restricted browser environments. Users are responsible for ensuring compliance with their institution's policies and SEB usage agreements.

---

Made with ❤️ for students tired of browser restrictions.

Questions? Open an issue on GitHub.