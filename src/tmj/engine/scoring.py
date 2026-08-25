"""Hong Kong Mahjong Fan (番) Calculator and Scoring System."""

from typing import List, Dict, Tuple
from .tiles import Tile, Suit
from .hand import PlayerHand, Meld, MeldType


class FanBreakdown:
    """Stores detailed breakdown of fan patterns achieved in a winning hand."""

    def __init__(self):
        self.patterns: List[Tuple[str, int]] = []

    def add(self, name: str, fan: int):
        self.patterns.append((name, fan))

    @property
    def total_fan(self) -> int:
        return sum(fan for _, fan in self.patterns)

    def __repr__(self) -> str:
        items = [f"{name} (+{fan}番)" for name, fan in self.patterns]
        return f"{', '.join(items)} -> 總計: {self.total_fan}番"


def calculate_fan(
    hand: PlayerHand,
    winning_tile: Tile,
    is_self_draw: bool,
    seat_wind: int = 1,      # 1=East, 2=South, 3=West, 4=North
    prevalent_wind: int = 1, # 1=East, 2=South, 3=West, 4=North
) -> FanBreakdown:
    """Calculates all Fan patterns for a winning hand in HK Mahjong."""

    breakdown = FanBreakdown()
    # Combine concealed tiles and winning tile if not already integrated
    all_concealed = list(hand.concealed)
    if hand.drawn and hand.drawn == winning_tile:
        pass
    else:
        all_concealed.append(winning_tile)

    all_tiles = sorted(all_concealed + [t for m in hand.melds for t in m.tiles])

    # Check suit composition
    suits_present = set(t.suit for t in all_tiles)
    numeric_suits = suits_present - {Suit.WIND, Suit.DRAGON}
    has_honors = any(s in (Suit.WIND, Suit.DRAGON) for s in suits_present)

    # 1. High Limit Patterns (Fan 8-10)
    # Thirteen Orphans (十三幺)
    if len(hand.melds) == 0 and len(all_tiles) == 14:
        orphans = {
            (Suit.WAN, 1), (Suit.WAN, 9), (Suit.DOT, 1), (Suit.DOT, 9), (Suit.BAM, 1), (Suit.BAM, 9),
            (Suit.WIND, 1), (Suit.WIND, 2), (Suit.WIND, 3), (Suit.WIND, 4),
            (Suit.DRAGON, 1), (Suit.DRAGON, 2), (Suit.DRAGON, 3),
        }
        counts = {(t.suit, t.rank): 0 for t in all_tiles}
        for t in all_tiles:
            counts[(t.suit, t.rank)] = counts.get((t.suit, t.rank), 0) + 1
        if set(counts.keys()).issubset(orphans) and len(counts) == 13:
            breakdown.add("十三幺", 10)
            return breakdown

    # All Honors (字一色)
    if not numeric_suits:
        breakdown.add("字一色", 10)
        return breakdown

    # Great Dragons (大三元)
    dragon_pongs = 0
    dragon_pairs = 0
    all_melds_list = hand.melds + get_concealed_melds_and_pair(all_concealed)[0]
    for m in all_melds_list:
        if m.tiles[0].suit == Suit.DRAGON:
            if len(m.tiles) >= 3:
                dragon_pongs += 1
            elif len(m.tiles) == 2:
                dragon_pairs += 1

    if dragon_pongs == 3:
        breakdown.add("大三元", 8)
    elif dragon_pongs == 2 and dragon_pairs == 1:
        breakdown.add("小三元", 5)

    # Pure One Suit (清一色) vs Mixed One Suit (混一色)
    if len(numeric_suits) == 1:
        if not has_honors:
            breakdown.add("清一色", 7)
        else:
            breakdown.add("混一色", 3)

    # 2. Hand Structure Patterns
    # Seven Pairs (七對子)
    if len(hand.melds) == 0 and len(all_tiles) == 14:
        counts = {}
        for t in all_tiles:
            counts[(t.suit, t.rank)] = counts.get((t.suit, t.rank), 0) + 1
        if len(counts) == 7 and all(c == 2 for c in counts.values()):
            breakdown.add("七對子", 3)

    # Check Pongs vs Chows
    exposed_melds, concealed_pair = get_concealed_melds_and_pair(all_concealed)
    total_melds = hand.melds + exposed_melds
    if len(total_melds) == 4:
        is_all_pongs = all(len(m.tiles) >= 3 and m.meld_type != MeldType.CHOW for m in total_melds)
        is_all_chows = all(m.meld_type == MeldType.CHOW for m in total_melds)

        if is_all_pongs:
            breakdown.add("碰碰胡", 3)
        elif is_all_chows:
            # Common Hand (平胡): all Chows + non-honor eye
            if concealed_pair and not concealed_pair[0].is_honor:
                breakdown.add("平胡", 1)

    # 3. Honor Tile Pongs
    for m in total_melds:
        if len(m.tiles) >= 3 and m.meld_type != MeldType.CHOW:
            t = m.tiles[0]
            if t.suit == Suit.DRAGON and "大三元" not in [name for name, _ in breakdown.patterns] and "小三元" not in [name for name, _ in breakdown.patterns]:
                breakdown.add(f"{t.name}刻", 1)
            elif t.suit == Suit.WIND:
                if t.rank == seat_wind:
                    breakdown.add("門風刻", 1)
                if t.rank == prevalent_wind:
                    breakdown.add("圈風刻", 1)

    # 4. Modifiers
    if is_self_draw:
        breakdown.add("自摸", 1)
    if len(hand.melds) == 0 and "十三幺" not in [name for name, _ in breakdown.patterns] and "七對子" not in [name for name, _ in breakdown.patterns]:
        breakdown.add("門清", 1)

    # If no patterns triggered, default to Chicken Hand (雞胡 0番)
    if len(breakdown.patterns) == 0:
        breakdown.add("雞胡", 0)

    return breakdown


def get_concealed_melds_and_pair(concealed: List[Tile]) -> Tuple[List[Meld], List[Tile]]:
    """Helper to extract melds and pair from concealed winning hand."""
    counts = {}
    for t in concealed:
        key = (t.suit, t.rank)
        counts[key] = counts.get(key, 0) + 1

    pair = []
    melds = []

    # Find pair first
    for key, c in counts.items():
        if c == 2 or c == 4:
            pair = [Tile(key[0], key[1]), Tile(key[0], key[1])]
            counts[key] -= 2
            break

    # Decompose remaining into melds
    for key in sorted(counts.keys(), key=lambda x: (x[0], x[1])):
        while counts[key] >= 3:
            melds.append(Meld(MeldType.PONG, [Tile(key[0], key[1])] * 3))
            counts[key] -= 3

    for key in sorted(counts.keys(), key=lambda x: (x[0], x[1])):
        suit, rank = key
        while counts[key] > 0 and suit not in (Suit.WIND, Suit.DRAGON) and rank <= 7:
            k2 = (suit, rank + 1)
            k3 = (suit, rank + 2)
            if counts.get(k2, 0) > 0 and counts.get(k3, 0) > 0:
                melds.append(Meld(MeldType.CHOW, [Tile(suit, rank), Tile(suit, rank + 1), Tile(suit, rank + 2)]))
                counts[key] -= 1
                counts[k2] -= 1
                counts[k3] -= 1
            else:
                break

    return melds, pair


def fan_to_points(fan: int) -> int:
    """Converts Fan count into HK Mahjong payout points."""
    if fan <= 0:
        return 1
    elif fan == 1:
        return 2
    elif fan == 2:
        return 4
    elif fan == 3:
        return 8
    elif fan == 4:
        return 16
    elif fan == 5:
        return 32
    elif fan == 6:
        return 64
    else:
        return 128  # Limit (爆番)
