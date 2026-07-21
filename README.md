# 🧹 擬人化 Gijinkai — language-aware AI fingerprint removal

*Personification.* Strips AI-generated patterns from source code — per language,
per extension. Python docstrings get different treatment than JSDoc blocks.
Shell comments get different treatment than CSS blocks. No one-size-fits-all regex.

## Quick start

```bash
git clone https://github.com/takorunikatora/gijinkai.git
cd gijinkai
pip install -r requirements.txt

# Preview changes
python3 main.py dir /path/to/project --dry-run

# Apply
python3 main.py dir /path/to/project --write
```

## Languages supported

| Language | Extensions | What gets stripped |
|---|---|---|
| **Python** | `.py` `.pyw` | AI docstrings, `__all__`, `from __future__`, `# noqa`, `# type: ignore`, obvious `#` comments, ASCII dividers, type hints (aggressive) |
| **JavaScript** | `.js` `.mjs` `.cjs` | JSDoc blocks, `'use strict'`, `// eslint-disable`, `@ts-ignore`, obvious `//` comments |
| **TypeScript** | `.ts` `.tsx` `.mts` `.cts` | Same as JS + type annotations (aggressive) |
| **HTML** | `.html` `.htm` `.xhtml` | `<!-- Status -->`, `<!-- Setup -->`, AI section comments |
| **CSS** | `.css` `.scss` `.sass` `.less` | `/* Layout - */`, `/* Component: */`, AI section headers |
| **Shell** | `.sh` `.bash` `.zsh` `.ksh` | Over-commented `#` blocks, divider lines |

## Modes

| Mode | Flag | Effect |
|---|---|---|
| `--light` | `-l` | Whitespace only (trailing spaces, blank line collapse) |
| `--medium` | *(default)* | Docstrings + comments + pragmas + dividers |
| `--aggressive` | `-a` | Above + type hints + shebangs + `__version__`/`__author__` |

## Usage

```bash
# List supported languages
python3 main.py langs

# Single file → stdout
python3 main.py file main.py

# Single file → overwrite
python3 main.py file main.py --write

# Directory, aggressive mode
python3 main.py dir ~/project --aggressive --dry-run

# Apply to everything
python3 main.py dir ~/project --write
```

## Example

Before:
```python
"""This module provides the core engine for hotspot management.

It handles hostapd lifecycle, dnsmasq DHCP, nftables firewall,
and the self-healing watchdog failover.
"""

from __future__ import annotations

__all__ = ["Engine", "EngineConfig", "EngineState"]
__version__ = "0.1.0"

# ── Engine ─────────────────────────────────────────────────────

class Engine:
    """The main orchestrator for the WiFi hotspot."""
    
    def start(self, config: EngineConfig) -> bool:
        # initialize the interface
        iface = self._detect_interface()
        ...
```

After (`--medium`):
```python
class Engine:
    
    def start(self, config: EngineConfig) -> bool:
        iface = self._detect_interface()
        ...
```

After (`--aggressive`):
```python
class Engine:
    
    def start(self, config) -> bool:
        iface = self._detect_interface()
        ...
```

## License

MIT © takorunikatora
