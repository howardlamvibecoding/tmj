# 🀄 TMJ - Terminal Mahjong

**TMJ (Terminal Mahjong)** is a sleek, terminal-based 4-Player Traditional Chinese / Hong Kong Mahjong TUI application built with **Python**, **Textual**, and **Rich**.

![TMJ Terminal Interface](https://img.shields.io/badge/Interface-Textual%20TUI-blue)
![Python Version](https://img.shields.io/badge/Python-3.9%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🀀 Features

- **Traditional Hong Kong Rules**: 136 standard tiles (+ optional flowers), 4 players, 13 concealed tiles per hand.
- **Full Action Claims**: Call *Chow* (吃), *Pong* (碰), *Gang* (槓), *Win* (胡 / Self-Draw 自摸), or Pass (過).
- **Interactive TUI**: Built with Textual widgets featuring UTF-8 Mahjong tile glyphs, color coding, and keyboard shortcuts.
- **Smart AI Opponents**: Play against 3 computer players with hand efficiency discard and claim logic.
- **HK Mahjong Fan (番) Scoring**: Automatic fan calculation (Common Hand 平胡, All Pongs 碰碰胡, Mixed One Suit 混一色, Pure One Suit 清一色, Dragons/Winds, etc.) and score distribution.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/USERNAME/tmj.git
cd tmj

# Install dependencies
pip install -e .
```

### Running the Game

Launch the TUI game:

```bash
tmj
```

Or run directly with Python:

```bash
python -m tmj.cli
```

## 🎮 Keyboard Controls

- `1`-`9`, `q`-`r`: Select tile to discard or claim action
- `c`: Call Chow (吃)
- `p`: Call Pong (碰)
- `g`: Call Gang (槓)
- `w`: Call Win (胡)
- `s`: Skip / Pass (過)
- `q`: Quit Game

## 🧪 Testing

Run automated tests:

```bash
pytest -v
```

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
