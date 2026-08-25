"""Player Hand state and Meld definitions."""

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
        self.source_player = source_player  # Index of player from whom tile was claimed

    @property
    def name(self) -> str:
        if self.meld_type == MeldType.CHOW:
            return f"吃 [{self.tiles[0].name}-{self.tiles[1].name}-{self.tiles[2].name}]"
        elif self.meld_type == MeldType.PONG:
            return f"碰 [{self.tiles[0].name}]"
        elif self.meld_type == MeldType.EXPOSED_GANG:
            return f"明槓 [{self.tiles[0].name}]"
        elif self.meld_type == MeldType.CONCEALED_GANG:
            return f"暗槓 [{self.tiles[0].name}]"
        return "面子"

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
        """Sets drawn tile."""
        self.drawn = tile

    def integrate_drawn(self):
        """Moves drawn tile into concealed list and sorts."""
        if self.drawn:
            self.concealed.append(self.drawn)
            self.drawn = None
            self.sort()

    def discard(self, tile_index: int) -> Optional[Tile]:
        """
        Discards tile at index in concealed hand, or the drawn tile if tile_index == len(concealed).
        Returns discarded tile.
        """
        all_tiles = self.all_concealed_tiles
        if tile_index < 0 or tile_index >= len(all_tiles):
            return None

        # If drawn tile is present and selected
        if self.drawn and tile_index == len(self.concealed):
            discarded = self.drawn
            self.drawn = None
            return discarded

        # Otherwise remove from concealed array
        self.integrate_drawn()
        discarded = self.concealed.pop(tile_index)
        self.sort()
        return discarded

    def remove_tiles(self, target: Tile, count: int) -> List[Tile]:
        """Removes up to count matching tiles from concealed hand."""
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
        """Returns sorted concealed tiles including drawn tile if present."""
        res = list(self.concealed)
        if self.drawn:
            res.append(self.drawn)
        return sorted(res)

    @property
    def total_tile_count(self) -> int:
        """Total tiles in hand including melds."""
        meld_tiles = sum(len(m.tiles) for m in self.melds)
        return len(self.concealed) + (1 if self.drawn else 0) + meld_tiles
