"""Player Hand state and Meld definitions with localization support."""

from enum import Enum
from typing import List, Optional
from .tiles import Tile


class MeldType(str, Enum):
    CHOW = "CHOW"                 # 吃
    PONG = "PONG"                 # 碰
    EXPOSED_GANG = "EXPOSED_GANG" # 明槓 / 加槓
    CONCEALED_GANG = "CONCEALED_GANG" # 暗槓


class Meld:
    """Represents an exposed or concealed meld (Chow, Pong, or Gang)."""

    def __init__(self, meld_type: MeldType, tiles: List[Tile], target_tile: Optional[Tile] = None, source_player: Optional[int] = None):
        self.meld_type = meld_type
        self.tiles = sorted(tiles)
        self.target_tile = target_tile
        self.source_player = source_player

    def get_name(self, lang: str = "zh") -> str:
        t0 = self.tiles[0].get_name(lang)
        if lang == "en":
            if self.meld_type == MeldType.CHOW:
                t1 = self.tiles[1].get_name(lang)
                t2 = self.tiles[2].get_name(lang)
                return f"Chow [{t0} - {t1} - {t2}]"
            elif self.meld_type == MeldType.PONG:
                return f"Pong [{t0}]"
            elif self.meld_type == MeldType.EXPOSED_GANG:
                return f"Kong [{t0}]"
            elif self.meld_type == MeldType.CONCEALED_GANG:
                return f"Concealed Kong [{t0}]"
            return "Meld"
        else:
            if self.meld_type == MeldType.CHOW:
                return f"吃 [{self.tiles[0].name}-{self.tiles[1].name}-{self.tiles[2].name}]"
            elif self.meld_type == MeldType.PONG:
                return f"碰 [{self.tiles[0].name}]"
            elif self.meld_type == MeldType.EXPOSED_GANG:
                return f"明槓 [{self.tiles[0].name}]"
            elif self.meld_type == MeldType.CONCEALED_GANG:
                return f"暗槓 [{self.tiles[0].name}]"
            return "面子"

    @property
    def name(self) -> str:
        return self.get_name("zh")

    def __repr__(self) -> str:
        return self.name


class PlayerHand:
    """Represents a player's complete hand: concealed tiles, drawn tile, and declared melds."""

    def __init__(self, tiles: Optional[List[Tile]] = None):
        self.concealed: List[Tile] = sorted(tiles) if tiles else []
        self.drawn: Optional[Tile] = None
        self.melds: List[Meld] = []

    def sort(self):
        self.concealed.sort()

    def add_tile(self, tile: Tile):
        self.drawn = tile

    def integrate_drawn(self):
        if self.drawn:
            self.concealed.append(self.drawn)
            self.drawn = None
            self.sort()

    def discard(self, tile_index: int) -> Optional[Tile]:
        all_tiles = self.all_concealed_tiles
        if tile_index < 0 or tile_index >= len(all_tiles):
            return None

        if self.drawn and tile_index == len(self.concealed):
            discarded = self.drawn
            self.drawn = None
            return discarded

        self.integrate_drawn()
        discarded = self.concealed.pop(tile_index)
        self.sort()
        return discarded

    def remove_tiles(self, target: Tile, count: int) -> List[Tile]:
        self.integrate_drawn()
        removed = []
        new_concealed = []
        for t in self.concealed:
            if t == target and len(removed) < count:
                removed.append(t)
            else:
                new_concealed.append(t)
        self.concealed = new_concealed
        return removed

    @property
    def all_concealed_tiles(self) -> List[Tile]:
        res = list(self.concealed)
        if self.drawn:
            res.append(self.drawn)
        return sorted(res)

    @property
    def total_tile_count(self) -> int:
        meld_tiles = sum(len(m.tiles) for m in self.melds)
        return len(self.concealed) + (1 if self.drawn else 0) + meld_tiles
