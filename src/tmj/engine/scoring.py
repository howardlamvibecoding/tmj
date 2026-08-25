"""Hong Kong Mahjong Fan (番) Calculator and Scoring System with Localization."""

from typing import List, Dict, Tuple
from .tiles import Tile, Suit
from .hand import PlayerHand, Meld, MeldType

PATTERN_NAMES = {
    "thirteen_orphans": {"zh": "十三幺", "en": "Thirteen Orphans"},
    "all_honors": {"zh": "字一色", "en": "All Honors"},
    "great_dragons": {"zh": "大三元", "en": "Great Dragons"},
    "little_dragons": {"zh": "小三元", "en": "Little Dragons"},
    "pure_one_suit": {"zh": "清一色", "en": "Pure One Suit"},
    "mixed_one_suit": {"zh": "混一色", "en": "Mixed One Suit"},
    "seven_pairs": {"zh": "七對子", "en": "Seven Pairs"},
    "all_pongs": {"zh": "碰碰胡", "en": "All Pongs"},
    "common_hand": {"zh": "平胡", "en": "Common Hand (Ping Wu)"},
    "dragon_pong": {"zh": "刻", "en": " Pong"},
    "seat_wind_pong": {"zh": "門風刻", "en": "Seat Wind Pong"},
    "prevalent_wind_pong": {"zh": "圈風刻", "en": "Prevalent Wind Pong"},
    "self_draw": {"zh": "自摸", "en": "Self-Draw"},
    "concealed_hand": {"zh": "門清", "en": "Concealed Hand"},
    "chicken_hand": {"zh": "雞胡", "en": "Chicken Hand"},
}


class FanBreakdown:
    """Stores detailed breakdown of fan patterns achieved in a winning hand."""

    def __init__(self, lang: str = "zh"):
        self.lang = lang
        self.patterns: List[Tuple[str, int]] = []

    def add(self, key: str, fan: int, custom_name: str = ""):
        if custom_name:
            name = custom_name
        elif key in PATTERN_NAMES:
            name = PATTERN_NAMES[key].get(self.lang, PATTERN_NAMES[key]["en"])
        else:
            name = key
        self.patterns.append((name, fan))

    @property
    def total_fan(self) -> int:
        return sum(fan for _, fan in self.patterns)

    def __repr__(self) -> str:
        items = [f"{name} (+{fan} Fan)" for name, fan in self.patterns]
        return f"{', '.join(items)} -> Total: {self.total_fan} Fan"


def calculate_fan(
    hand: PlayerHand,
    winning_tile: Tile,
    is_self_draw: bool,
    seat_wind: int = 1,      # 1=East, 2=South, 3=West, 4=North
    prevalent_wind: int = 1, # 1=East, 2=South, 3=West, 4=North
    lang: str = "zh",
) -> FanBreakdown:
    """Calculates all Fan patterns for a winning hand in HK Mahjong."""

    breakdown = FanBreakdown(lang=lang)
    all_concealed = list(hand.concealed)
    if hand.drawn and hand.drawn == winning_tile:
        pass
    else:
        all_concealed.append(winning_tile)

    all_tiles = sorted(all_concealed + [t for m in hand.melds for t in m.tiles])

    suits_present = set(t.suit for t in all_tiles)
    numeric_suits = suits_present - {Suit.WIND, Suit.DRAGON}
    has_honors = any(s in (Suit.WIND, Suit.DRAGON) for s in suits_present)

    # 1. High Limit Patterns (Fan 8-10)
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
            breakdown.add("thirteen_orphans", 10)
            return breakdown

    if not numeric_suits:
        breakdown.add("all_honors", 10)
        return breakdown

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
        breakdown.add("great_dragons", 8)
    elif dragon_pongs == 2 and dragon_pairs == 1:
        breakdown.add("little_dragons", 5)

    if len(numeric_suits) == 1:
        if not has_honors:
            breakdown.add("pure_one_suit", 7)
        else:
            breakdown.add("mixed_one_suit", 3)

    # 2. Hand Structure Patterns
    if len(hand.melds) == 0 and len(all_tiles) == 14:
        counts = {}
        for t in all_tiles:
            counts[(t.suit, t.rank)] = counts.get((t.suit, t.rank), 0) + 1
        if len(counts) == 7 and all(c == 2 for c in counts.values()):
            breakdown.add("seven_pairs", 3)

    exposed_melds, concealed_pair = get_concealed_melds_and_pair(all_concealed)
    total_melds = hand.melds + exposed_melds
    if len(total_melds) == 4:
        is_all_pongs = all(len(m.tiles) >= 3 and m.meld_type != MeldType.CHOW for m in total_melds)
        is_all_chows = all(m.meld_type == MeldType.CHOW for m in total_melds)

        if is_all_pongs:
            breakdown.add("all_pongs", 3)
        elif is_all_chows:
            if concealed_pair and not concealed_pair[0].is_honor:
                breakdown.add("common_hand", 1)

    # 3. Honor Tile Pongs
    for m in total_melds:
        if len(m.tiles) >= 3 and m.meld_type != MeldType.CHOW:
            t = m.tiles[0]
            if t.suit == Suit.DRAGON and "great_dragons" not in [k for k, _ in breakdown.patterns] and "little_dragons" not in [k for k, _ in breakdown.patterns]:
                dname = t.get_name(lang)
                suffix = " Pong" if lang == "en" else "刻"
                breakdown.add("", 1, custom_name=f"{dname}{suffix}")
            elif t.suit == Suit.WIND:
                if t.rank == seat_wind:
                    breakdown.add("seat_wind_pong", 1)
                if t.rank == prevalent_wind:
                    breakdown.add("prevalent_wind_pong", 1)

    # 4. Modifiers
    if is_self_draw:
        breakdown.add("self_draw", 1)
    if len(hand.melds) == 0:
        breakdown.add("concealed_hand", 1)

    if len(breakdown.patterns) == 0:
        breakdown.add("chicken_hand", 0)

    return breakdown


def get_concealed_melds_and_pair(concealed: List[Tile]) -> Tuple[List[Meld], List[Tile]]:
    counts = {}
    for t in concealed:
        key = (t.suit, t.rank)
        counts[key] = counts.get(key, 0) + 1

    pair = []
    melds = []

    for key, c in counts.items():
        if c == 2 or c == 4:
            pair = [Tile(key[0], key[1]), Tile(key[0], key[1])]
            counts[key] -= 2
            break

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
        return 128
