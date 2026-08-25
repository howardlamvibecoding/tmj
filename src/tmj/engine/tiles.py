"""Mahjong Tile representation and utilities."""

from enum import Enum
from typing import List, Tuple


class Suit(str, Enum):
    WAN = "WAN"       # Characters (萬)
    DOT = "DOT"       # Dots (筒)
    BAM = "BAM"       # Bamboo (索)
    WIND = "WIND"     # Winds (風: 東南西北)
    DRAGON = "DRAGON" # Dragons (龍: 中發白)


SUIT_NAMES = {
    Suit.WAN: "萬",
    Suit.DOT: "筒",
    Suit.BAM: "索",
    Suit.WIND: "風",
    Suit.DRAGON: "龍",
}

NUM_NAMES = {
    1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
    6: "六", 7: "七", 8: "八", 9: "九"
}

WIND_NAMES = {1: "東", 2: "南", 3: "西", 4: "北"}
DRAGON_NAMES = {1: "中", 2: "發", 3: "白"}

# Unicode glyph mappings
GLYPHS = {
    # Wan 🀇-🀏
    (Suit.WAN, 1): "🀇", (Suit.WAN, 2): "🀈", (Suit.WAN, 3): "🀉",
    (Suit.WAN, 4): "🀊", (Suit.WAN, 5): "🀋", (Suit.WAN, 6): "🀌",
    (Suit.WAN, 7): "🀍", (Suit.WAN, 8): "🀎", (Suit.WAN, 9): "🀏",
    # Dot 🀙-🀡
    (Suit.DOT, 1): "🀙", (Suit.DOT, 2): "🀚", (Suit.DOT, 3): "🀛",
    (Suit.DOT, 4): "🀜", (Suit.DOT, 5): "🀝", (Suit.DOT, 6): "🀞",
    (Suit.DOT, 7): "🀟", (Suit.DOT, 8): "🀠", (Suit.DOT, 9): "🀡",
    # Bam 🀐-🀘
    (Suit.BAM, 1): "🀐", (Suit.BAM, 2): "🀑", (Suit.BAM, 3): "🀒",
    (Suit.BAM, 4): "🀓", (Suit.BAM, 5): "🀔", (Suit.BAM, 6): "🀕",
    (Suit.BAM, 7): "🀖", (Suit.BAM, 8): "🀗", (Suit.BAM, 9): "🀘",
    # Winds 🀀-🀃
    (Suit.WIND, 1): "🀀", (Suit.WIND, 2): "🀁", (Suit.WIND, 3): "🀂", (Suit.WIND, 4): "🀃",
    # Dragons 🀄-🀆
    (Suit.DRAGON, 1): "🀄", (Suit.DRAGON, 2): "🀅", (Suit.DRAGON, 3): "🀆",
}


class Tile:
    """Represents a single Mahjong tile."""

    def __init__(self, suit: Suit, rank: int, tile_id: int = 0):
        self.suit = suit
        self.rank = rank
        self.tile_id = tile_id  # Unique ID (0 to 135) to distinguish duplicate tiles

    @property
    def is_honor(self) -> bool:
        return self.suit in (Suit.WIND, Suit.DRAGON)

    @property
    def is_terminal(self) -> bool:
        return not self.is_honor and (self.rank == 1 or self.rank == 9)

    @property
    def is_terminal_or_honor(self) -> bool:
        return self.is_honor or self.is_terminal

    @property
    def glyph(self) -> str:
        return GLYPHS.get((self.suit, self.rank), "🀫")

    @property
    def name(self) -> str:
        if self.suit == Suit.WAN:
            return f"{NUM_NAMES[self.rank]}萬"
        elif self.suit == Suit.DOT:
            return f"{NUM_NAMES[self.rank]}筒"
        elif self.suit == Suit.BAM:
            return f"{NUM_NAMES[self.rank]}索"
        elif self.suit == Suit.WIND:
            return f"{WIND_NAMES[self.rank]}風"
        elif self.suit == Suit.DRAGON:
            return f"{DRAGON_NAMES[self.rank]}"
        return "未知"

    @property
    def short_code(self) -> str:
        if self.suit == Suit.WAN:
            return f"{self.rank}m"
        elif self.suit == Suit.DOT:
            return f"{self.rank}p"
        elif self.suit == Suit.BAM:
            return f"{self.rank}s"
        elif self.suit == Suit.WIND:
            return ["", "1z", "2z", "3z", "4z"][self.rank]
        elif self.suit == Suit.DRAGON:
            return ["", "5z", "6z", "7z"][self.rank]
        return "??"

    @property
    def color_style(self) -> str:
        if self.suit == Suit.WAN:
            return "bold red"
        elif self.suit == Suit.DOT:
            return "bold cyan"
        elif self.suit == Suit.BAM:
            return "bold green"
        elif self.suit == Suit.WIND:
            return "bold yellow"
        elif self.suit == Suit.DRAGON:
            if self.rank == 1:
                return "bold bright_red" # Red Dragon
            elif self.rank == 2:
                return "bold bright_green" # Green Dragon
            else:
                return "bold white" # White Dragon
        return "white"

    def __repr__(self) -> str:
        return f"[{self.glyph} {self.name}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tile):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))

    def __lt__(self, other: "Tile") -> bool:
        order = [Suit.WAN, Suit.DOT, Suit.BAM, Suit.WIND, Suit.DRAGON]
        if order.index(self.suit) != order.index(other.suit):
            return order.index(self.suit) < order.index(other.suit)
        return self.rank < other.rank


def create_full_deck() -> List[Tile]:
    """Creates a standard 136-tile Hong Kong Mahjong deck (4 copies of each tile)."""
    tiles = []
    tid = 0
    # Wan, Dot, Bam (1-9 each)
    for suit in [Suit.WAN, Suit.DOT, Suit.BAM]:
        for rank in range(1, 10):
            for _ in range(4):
                tiles.append(Tile(suit, rank, tid))
                tid += 1
    # Winds (1-4)
    for rank in range(1, 5):
        for _ in range(4):
            tiles.append(Tile(Suit.WIND, rank, tid))
            tid += 1
    # Dragons (1-3)
    for rank in range(1, 4):
        for _ in range(4):
            tiles.append(Tile(Suit.DRAGON, rank, tid))
            tid += 1
    return tiles
