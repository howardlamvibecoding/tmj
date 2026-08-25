"""AI Opponent decision engine for Terminal Mahjong."""

import random
from typing import List, Tuple, Optional
from .tiles import Tile, Suit
from .hand import PlayerHand, MeldType
from .validator import tiles_to_counts, can_win_on_discard, can_win_on_self_draw, can_pong, get_chow_combinations, can_gang_on_discard


class MahjongAI:
    """Decision maker for computer-controlled Mahjong players."""

    def __init__(self, player_index: int, name: str = "AI"):
        self.player_index = player_index
        self.name = name

    def choose_discard(self, hand: PlayerHand) -> int:
        """
        Selects best tile index to discard from hand.
        Prioritizes discarding isolated honors, isolated terminals, then duplicate or sequence tiles.
        """
        all_tiles = hand.all_concealed_tiles
        if not all_tiles:
            return 0

        counts = tiles_to_counts(all_tiles)

        best_score = 999
        best_idx = 0

        for idx, t in enumerate(all_tiles):
            c = counts.get((t.suit, t.rank), 1)
            # Evaluate tile isolatedness score (lower score = higher priority to discard)
            score = 0
            if t.is_honor:
                score += (c * 10)  # Isolated honor (c=1) gets score 10, pair gets 20
            else:
                score += (c * 15)
                # Check for adjacent numbers in same suit
                has_neighbor_1 = counts.get((t.suit, t.rank - 1), 0) > 0
                has_neighbor_2 = counts.get((t.suit, t.rank + 1), 0) > 0
                has_gap_1 = counts.get((t.suit, t.rank - 2), 0) > 0
                has_gap_2 = counts.get((t.suit, t.rank + 2), 0) > 0

                if has_neighbor_1 or has_neighbor_2:
                    score += 25
                if has_gap_1 or has_gap_2:
                    score += 10

            if score < best_score:
                best_score = score
                best_idx = idx

        return best_idx

    def should_claim_win(self, hand: PlayerHand, target: Tile, is_self_draw: bool = False) -> bool:
        """AI always claims Win if eligible."""
        if is_self_draw:
            return can_win_on_self_draw(hand)
        return can_win_on_discard(hand, target)

    def should_claim_pong(self, hand: PlayerHand, target: Tile) -> bool:
        """AI claims Pong if target creates a Pong and hand isn't purely Chow-focused."""
        if not can_pong(hand, target):
            return False
        # Randomize slightly for realistic play (80% chance)
        return random.random() < 0.80

    def should_claim_chow(self, hand: PlayerHand, target: Tile) -> Optional[Tuple[Tile, Tile]]:
        """AI claims Chow if target completes a sequence (50% chance)."""
        combos = get_chow_combinations(hand.concealed, target)
        if not combos:
            return None
        if random.random() < 0.50:
            return combos[0]
        return None

    def should_claim_gang(self, hand: PlayerHand, target: Tile) -> bool:
        """AI claims Gang if eligible."""
        return can_gang_on_discard(hand, target)
