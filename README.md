# Renamica

A macOS batch file renaming tool with drag-and-drop support, preview, undo, and safety checks.

[![GitHub release](https://img.shields.io/github/v/release/Vasoura/Renamica)](https://github.com/Vasoura/Renamica/releases)
[![macOS](https://img.shields.io/badge/platform-macOS-blue)](https://github.com/Vasoura/Renamica)

## Features

- **Drag & Drop** – Drag files or folders directly into the list
- **Find & Replace** – Replace text or use regex patterns
- **Delete** – Remove keywords or delete N characters at a position
- **Prefix & Suffix** – Add text before or after filenames
- **Numbering** – Auto-number files (001, 002… or a, b, c…)
- **Sorting** – Sort by name, date, size, type with ascending/descending
- **Live Preview** – See results before executing
- **Conflict Detection** – Detects duplicate names, illegal characters, existing files
- **Undo** – Revert the last batch rename
- **Rename Log** – All operations logged to `~/.renamica/rename_log.csv`
- **Dark Mode** – Toggle light/dark appearance

## Screenshots

![app](dist/Renamica.app)

## Installation

### Prerequisites

- macOS (arm64 or x86_64)
- Python 3.8+
- PyInstaller (for building .app)

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run as script
python3 Renamica.py

# Or build .app
pip install pyinstaller
pyinstaller Renamica.spec
open dist/Renamica.app
```

### Build .app Manually

```bash
pip install pyinstaller
pyinstaller Renamica.spec --clean --noconfirm
open dist/Renamica.app
```

## Project Structure

```
Renamica/
├── Renamica.py            # Main application
├── Renamica.spec          # PyInstaller build spec
├── renamica.icns          # App icon
├── renamica_icon.png      # 1024x1024 source icon
├── convert_icon.py        # Icon generation script
├── requirements.txt       # Python dependencies
├── dist/
│   └── Renamica.app       # Built macOS application
├── issues.md              # Known issues & improvements
└── README.md
```

## Usage

1. **Add files** – Drag files onto the window, or use File → Add Files
2. **Configure rules** – Set find/replace, prefix/suffix, numbering, etc.
3. **Preview** – The list updates live to show before → after
4. **Execute** – Click Execute, or use Edit → Undo to revert

Conflict warnings appear below the file list. If there are issues, the Execute button is disabled until they're resolved.

## License

MIT
