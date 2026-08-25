"""Textual UI widgets for rendering Mahjong tiles, hands, and tables with localization."""

from typing import List, Optional
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import RenderableType

from ..engine.tiles import Tile, Suit
from ..engine.hand import PlayerHand, Meld


KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "q", "w", "e", "r"]


def render_tile_card(tile: Tile, key_label: Optional[str] = None, is_highlighted: bool = False, lang: str = "zh") -> Text:
    """Renders a single Mahjong tile card with glyph, localized name, and color styling."""
    t = Text()
    style = tile.color_style
    if is_highlighted:
        style = f"{style} reverse"

    if key_label:
        t.append(f"({key_label})", style="bold green")

    tile_name = tile.get_name(lang)
    t.append(f"[{tile.glyph} {tile_name}]", style=style)
    return t


class HandWidget(Static):
    """Renders a player's concealed hand, drawn tile, and melds."""

    def __init__(self, hand: PlayerHand, is_human: bool = True, current_selected: int = 0, lang: str = "zh", **kwargs):
        super().__init__(**kwargs)
        self.hand = hand
        self.is_human = is_human
        self.current_selected = current_selected
        self.lang = lang

    def render(self) -> RenderableType:
        if not self.is_human:
            concealed_count = len(self.hand.concealed)
            ai_tiles = " ".join(["🀫"] * concealed_count)
            drawn_str = " 🀫" if self.hand.drawn else ""
            melds_str = "  ".join([f"[{m.get_name(self.lang)}]" for m in self.hand.melds])
            return Text(f"{ai_tiles}{drawn_str}   {melds_str}", style="dim cyan")

        t = Text()
        all_concealed = list(self.hand.concealed)

        for i, tile in enumerate(all_concealed):
            key_shortcut = KEYS[i] if i < len(KEYS) else str(i + 1)
            is_sel = (i == self.current_selected)
            t.append_text(render_tile_card(tile, key_label=key_shortcut, is_highlighted=is_sel, lang=self.lang))
            t.append(" ")

        if self.hand.drawn:
            i = len(all_concealed)
            key_shortcut = KEYS[i] if i < len(KEYS) else "R"
            is_sel = (i == self.current_selected)
            drawn_label = "  |  Drawn: " if self.lang == "en" else "  |  摸牌: "
            t.append(drawn_label, style="bold yellow")
            t.append_text(render_tile_card(self.hand.drawn, key_label=key_shortcut, is_highlighted=is_sel, lang=self.lang))

        if self.hand.melds:
            meld_label = "\n  Exposed Melds: " if self.lang == "en" else "\n  已碰/吃/槓: "
            t.append(meld_label, style="bold blue")
            for m in self.hand.melds:
                t.append(f"[{m.get_name(self.lang)}] ", style="bold white on blue")

        panel_title = "[bold green]Your Hand (Press [1-9, q-r] to Discard)[/bold green]" if self.lang == "en" else "[bold green]您的手牌 (選擇對應按鍵或 [1-9, q-r] 棄牌)[/bold green]"
        return Panel(t, title=panel_title, border_style="green")


class DiscardPoolWidget(Static):
    """Renders the central discard pool on the table."""

    def __init__(self, discards: List[tuple], lang: str = "zh", **kwargs):
        super().__init__(**kwargs)
        self.discards = discards
        self.lang = lang

    def render(self) -> RenderableType:
        title = "🀄 Central Discards 🀄" if self.lang == "en" else "🀄 中央棄牌區 🀄"
        empty_msg = "No discards yet" if self.lang == "en" else "暫無棄牌"

        if not self.discards:
            return Panel(Text(empty_msg, style="dim italic white", justify="center"), title=title, border_style="dim yellow")

        items = []
        for p, tile in self.discards[-24:]:
            t = render_tile_card(tile, lang=self.lang)
            items.append(t)

        rows_text = Text()
        for idx, item in enumerate(items):
            rows_text.append_text(item)
            rows_text.append("  ")
            if (idx + 1) % 8 == 0:
                rows_text.append("\n")

        return Panel(rows_text, title=title, border_style="bold yellow")


class InfoWidget(Static):
    """Renders table top bar: remaining wall tiles, wind round, dealer info."""

    def __init__(self, wall_count: int, prevalent_wind: str, dealer_name: str, lang: str = "zh", **kwargs):
        super().__init__(**kwargs)
        self.wall_count = wall_count
        self.prevalent_wind = prevalent_wind
        self.dealer_name = dealer_name
        self.lang = lang

    def render(self) -> RenderableType:
        t = Text()
        label_wind = " Round: " if self.lang == "en" else " 局風: "
        label_dealer = "  |  Dealer: " if self.lang == "en" else "  |  莊家: "
        label_wall = "  |  Wall Left: " if self.lang == "en" else "  |  牌牆剩餘: "
        unit_tiles = " tiles" if self.lang == "en" else " 張"

        t.append(label_wind, style="bold yellow")
        t.append(f"{self.prevalent_wind} ", style="bold white on red")
        t.append(label_dealer, style="bold yellow")
        t.append(f"{self.dealer_name} ", style="bold cyan")
        t.append(label_wall, style="bold yellow")
        t.append(f"{self.wall_count}{unit_tiles}", style="bold green")
        return Panel(t, border_style="yellow")
