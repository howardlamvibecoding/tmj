"""Mahjong Wall management and tile dealing."""

import random
from typing import List, Optional, Tuple
from .tiles import Tile, create_full_deck


class Wall:
    """Manages the 136-tile wall, live drawing stack, and dead wall."""

    def __init__(self, seed: Optional[int] = None):
        self._tiles: List[Tile] = create_full_deck()
        self.seed = seed
        self.reset(seed)

    def reset(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self._tiles = create_full_deck()
        random.shuffle(self._tiles)
        self.dead_wall_count = 14

    @property
    def remaining_count(self) -> int:
        """Remaining tiles available for normal draws."""
        return max(0, len(self._tiles) - self.dead_wall_count)

    @property
    def total_remaining(self) -> int:
        return len(self._tiles)

    def draw(self) -> Optional[Tile]:
        """Draws one tile from the live wall."""
        if self.remaining_count <= 0:
            return None
        return self._tiles.pop(0)

    def draw_supplement(self) -> Optional[Tile]:
        """Draws a supplement tile from the dead wall (e.g. after a Gang)."""
        if len(self._tiles) <= 0:
            return None
        return self._tiles.pop()

    def deal_hands(self, dealer_index: int = 0) -> Tuple[List[List[Tile]], Tile]:
        """
        Deals initial 13 tiles to 4 players, plus 1 extra tile to dealer.
        Returns (hands_list, dealer_extra_tile).
        """
        hands = [[], [], [], []]
        # Deal 13 tiles to each of 4 players
        for _ in range(13):
            for p in range(4):
                tile = self.draw()
                if tile:
                    hands[p].append(tile)

        # Sort each hand
        for p in range(4):
            hands[p].sort()

        # Dealer draws 14th tile
        dealer_tile = self.draw()
        return hands, dealer_tile
