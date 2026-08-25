"""Textual UI widgets for rendering Mahjong tiles, hands, and tables."""

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


def render_tile_card(tile: Tile, key_label: Optional[str] = None, is_highlighted: bool = False) -> Text:
    """Renders a single Mahjong tile card with glyph, name, and color styling."""
    t = Text()
    style = tile.color_style
    if is_highlighted:
        style = f"{style} reverse"

    if key_label:
        t.append(f"({key_label})", style="bold green")

    t.append(f"[{tile.glyph} {tile.name}]", style=style)
    return t


class HandWidget(Static):
    """Renders a player's concealed hand, drawn tile, and melds."""

    def __init__(self, hand: PlayerHand, is_human: bool = True, current_selected: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.hand = hand
        self.is_human = is_human
        self.current_selected = current_selected

    def render(self) -> RenderableType:
        if not self.is_human:
            # Concealed AI tiles rendered as face-down blocks 🀫
            concealed_count = len(self.hand.concealed)
            ai_tiles = " ".join(["🀫"] * concealed_count)
            drawn_str = " 🀫" if self.hand.drawn else ""
            melds_str = "  ".join([f"[{m.name}]" for m in self.hand.melds])
            return Text(f"{ai_tiles}{drawn_str}   {melds_str}", style="dim cyan")

        # Human player hand rendering with key shortcuts
        t = Text()
        all_concealed = list(self.hand.concealed)

        # Render concealed tiles
        for i, tile in enumerate(all_concealed):
            key_shortcut = KEYS[i] if i < len(KEYS) else str(i + 1)
            is_sel = (i == self.current_selected)
            t.append_text(render_tile_card(tile, key_label=key_shortcut, is_highlighted=is_sel))
            t.append(" ")

        # Render drawn tile separately
        if self.hand.drawn:
            i = len(all_concealed)
            key_shortcut = KEYS[i] if i < len(KEYS) else "R"
            is_sel = (i == self.current_selected)
            t.append("  |  抽卡: ", style="bold yellow")
            t.append_text(render_tile_card(self.hand.drawn, key_label=key_shortcut, is_highlighted=is_sel))

        # Render exposed melds
        if self.hand.melds:
            t.append("\n  已碰/吃/槓: ", style="bold blue")
            for m in self.hand.melds:
                t.append(f"[{m.name}] ", style="bold white on blue")

        return Panel(t, title="[bold green]您的手牌 (選擇對應按鍵或 [1-9, q-r] 棄牌)[/bold green]", border_style="green")


class DiscardPoolWidget(Static):
    """Renders the central discard pool on the table."""

    def __init__(self, discards: List[tuple], **kwargs):
        super().__init__(**kwargs)
        self.discards = discards

    def render(self) -> RenderableType:
        table = Table(title="🀄 中央棄牌區 🀄", border_style="dim white", expand=True)
        table.add_column("最近棄牌", justify="center")

        if not self.discards:
            return Panel(Text("暫無棄牌", style="dim italic white", justify="center"), title="中央棄牌區", border_style="dim yellow")

        # Format discards in rows of 8
        items = []
        for p, tile in self.discards[-24:]: # Show last 24 discards
            t = render_tile_card(tile)
            items.append(t)

        rows_text = Text()
        for idx, item in enumerate(items):
            rows_text.append_text(item)
            rows_text.append("  ")
            if (idx + 1) % 8 == 0:
                rows_text.append("\n")

        return Panel(rows_text, title="🀄 中央棄牌區 (最近棄牌) 🀄", border_style="bold yellow")


class InfoWidget(Static):
    """Renders table top bar: remaining wall tiles, wind round, dealer info."""

    def __init__(self, wall_count: int, prevalent_wind: str, dealer_name: str, **kwargs):
        super().__init__(**kwargs)
        self.wall_count = wall_count
        self.prevalent_wind = prevalent_wind
        self.dealer_name = dealer_name

    def render(self) -> RenderableType:
        t = Text()
        t.append(f" 局風: ", style="bold yellow")
        t.append(f"{self.prevalent_wind} ", style="bold white on red")
        t.append(f"  |  莊家: ", style="bold yellow")
        t.append(f"{self.dealer_name} ", style="bold cyan")
        t.append(f"  |  牌牆剩餘: ", style="bold yellow")
        t.append(f"{self.wall_count} 張", style="bold green")
        return Panel(t, border_style="yellow")
