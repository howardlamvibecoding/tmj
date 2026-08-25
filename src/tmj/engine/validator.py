"""Mahjong Rule Validator and Claim Detector."""

from collections import Counter
from typing import List, Tuple, Optional
from .tiles import Tile, Suit
from .hand import PlayerHand, Meld, MeldType


def tiles_to_counts(tiles: List[Tile]) -> dict:
    """Converts a list of Tile objects into a dict mapping (suit, rank) tuple -> count."""
    counts = {}
    for t in tiles:
        key = (t.suit, t.rank)
        counts[key] = counts.get(key, 0) + 1
    return counts


def is_winning_hand(concealed_tiles: List[Tile], melds_count: int = 0) -> bool:
    """
    Checks if concealed_tiles forms a valid winning hand combined with existing melds.
    Target total melds + pairs: melds_count + remaining melds = 4, plus 1 pair.
    Concealed tile count must be 3*N + 2 (e.g. 14, 11, 8, 5, 2 tiles).
    """
    total = len(concealed_tiles)
    if total % 3 != 2:
        return False

    counts = tiles_to_counts(concealed_tiles)

    # Special win hands (only if 14 concealed tiles, i.e. 0 melds)
    if melds_count == 0 and total == 14:
        # Seven Pairs (七對子)
        if len(counts) == 7 and all(c == 2 for c in counts.values()):
            return True

        # Thirteen Orphans (十三幺)
        orphans = {
            (Suit.WAN, 1), (Suit.WAN, 9),
            (Suit.DOT, 1), (Suit.DOT, 9),
            (Suit.BAM, 1), (Suit.BAM, 9),
            (Suit.WIND, 1), (Suit.WIND, 2), (Suit.WIND, 3), (Suit.WIND, 4),
            (Suit.DRAGON, 1), (Suit.DRAGON, 2), (Suit.DRAGON, 3),
        }
        if set(counts.keys()).issubset(orphans) and len(counts) == 13 and max(counts.values()) == 2:
            return True

    # Standard 4 melds + 1 pair decomposition
    # Try each possible pair (eye)
    for key, count in counts.items():
        if count >= 2:
            # Remove pair
            counts[key] -= 2
            if check_melds(counts, (total - 2) // 3):
                counts[key] += 2
                return True
            counts[key] += 2

    return False


def check_melds(counts: dict, melds_needed: int) -> bool:
    """Recursively checks if counts can be fully decomposed into melds_needed Pongs or Chows."""
    if melds_needed == 0:
        return all(c == 0 for c in counts.values())

    # Find first tile key with count > 0
    first_key = None
    for k in sorted(counts.keys(), key=lambda x: (x[0], x[1])):
        if counts[k] > 0:
            first_key = k
            break

    if not first_key:
        return melds_needed == 0

    suit, rank = first_key

    # Try Pong (3 of a kind)
    if counts[first_key] >= 3:
        counts[first_key] -= 3
        if check_melds(counts, melds_needed - 1):
            counts[first_key] += 3
            return True
        counts[first_key] += 3

    # Try Chow (3 consecutive suit numbers, not honors)
    if suit not in (Suit.WIND, Suit.DRAGON) and rank <= 7:
        k2 = (suit, rank + 1)
        k3 = (suit, rank + 2)
        if counts.get(k2, 0) > 0 and counts.get(k3, 0) > 0:
            counts[first_key] -= 1
            counts[k2] -= 1
            counts[k3] -= 1
            if check_melds(counts, melds_needed - 1):
                counts[first_key] += 1
                counts[k2] += 1
                counts[k3] += 1
                return True
            counts[first_key] += 1
            counts[k2] += 1
            counts[k3] += 1

    return False


def get_chow_combinations(concealed: List[Tile], target: Tile) -> List[Tuple[Tile, Tile]]:
    """Returns pairs of tiles in concealed hand that can form a Chow (eat) with target tile."""
    if target.is_honor:
        return []

    res = []
    suit = target.suit
    r = target.rank

    # Option 1: target is lowest (r, r+1, r+2) -> needs r+1, r+2
    if r <= 7:
        t1 = [t for t in concealed if t.suit == suit and t.rank == r + 1]
        t2 = [t for t in concealed if t.suit == suit and t.rank == r + 2]
        if t1 and t2:
            res.append((t1[0], t2[0]))

    # Option 2: target is middle (r-1, r, r+1) -> needs r-1, r+1
    if 2 <= r <= 8:
        t1 = [t for t in concealed if t.suit == suit and t.rank == r - 1]
        t2 = [t for t in concealed if t.suit == suit and t.rank == r + 1]
        if t1 and t2:
            res.append((t1[0], t2[0]))

    # Option 3: target is highest (r-2, r-1, r) -> needs r-2, r-1
    if r >= 3:
        t1 = [t for t in concealed if t.suit == suit and t.rank == r - 2]
        t2 = [t for t in concealed if t.suit == suit and t.rank == r - 1]
        if t1 and t2:
            res.append((t1[0], t2[0]))

    return res


def can_win_on_discard(hand: PlayerHand, target: Tile) -> bool:
    """Checks if claiming discarded target tile results in a winning hand."""
    tiles = hand.all_concealed_tiles + [target]
    return is_winning_hand(tiles, len(hand.melds))


def can_win_on_self_draw(hand: PlayerHand) -> bool:
    """Checks if current hand (with drawn tile) is a winning hand."""
    tiles = hand.all_concealed_tiles
    return is_winning_hand(tiles, len(hand.melds))


def can_pong(hand: PlayerHand, target: Tile) -> bool:
    """Checks if player can Pong discarded target tile (has >= 2 copies in concealed hand)."""
    count = sum(1 for t in hand.concealed if t == target)
    return count >= 2


def can_gang_on_discard(hand: PlayerHand, target: Tile) -> bool:
    """Checks if player can Gang (大明槓) discarded target tile (has 3 copies in concealed hand)."""
    count = sum(1 for t in hand.concealed if t == target)
    return count == 3


def get_concealed_gang_candidates(hand: PlayerHand) -> List[Tile]:
    """Returns list of tiles for which player has 4 copies in concealed hand (暗槓)."""
    counts = tiles_to_counts(hand.all_concealed_tiles)
    res = []
    for (suit, rank), c in counts.items():
        if c == 4:
            res.append(Tile(suit, rank))
    return res


def get_add_gang_candidates(hand: PlayerHand) -> List[Tuple[Meld, Tile]]:
    """Returns list of (existing_pong_meld, drawn_tile) where drawn tile can upgrade a Pong to Gang (加槓)."""
    if not hand.drawn:
        return []
    candidates = []
    for meld in hand.melds:
        if meld.meld_type == MeldType.PONG and meld.tiles[0] == hand.drawn:
            candidates.append((meld, hand.drawn))
    return candidates
