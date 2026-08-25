"""CLI Entrypoint for TMJ - Terminal Mahjong."""

import sys
import argparse
from .ui.app import TMJApp


def main():
    parser = argparse.ArgumentParser(description="TMJ - Terminal Mahjong (4-Player Hong Kong Rules)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible game deck shuffling")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="Language mode: 'zh' (Chinese, default) or 'en' (English)")
    args = parser.parse_args()

    app = TMJApp(seed=args.seed, lang=args.lang)
    app.run()


if __name__ == "__main__":
    main()
