"""Tests for HK Mahjong Fan scoring and points conversion."""

import unittest
from tmj.engine.tiles import Tile, Suit
from tmj.engine.hand import PlayerHand, Meld, MeldType
from tmj.engine.scoring import calculate_fan, fan_to_points


class TestScoring(unittest.TestCase):

    def test_pure_one_suit_fan(self):
        hand = PlayerHand([
            Tile(Suit.WAN, 1), Tile(Suit.WAN, 2), Tile(Suit.WAN, 3),
            Tile(Suit.WAN, 4), Tile(Suit.WAN, 5), Tile(Suit.WAN, 6),
            Tile(Suit.WAN, 7), Tile(Suit.WAN, 8), Tile(Suit.WAN, 9),
            Tile(Suit.WAN, 1), Tile(Suit.WAN, 1), Tile(Suit.WAN, 1),
            Tile(Suit.WAN, 5)
        ])
        win_tile = Tile(Suit.WAN, 5)
        breakdown = calculate_fan(hand, win_tile, is_self_draw=True)

        pattern_names = [name for name, _ in breakdown.patterns]
        self.assertIn("清一色", pattern_names)
        self.assertGreaterEqual(breakdown.total_fan, 7)

    def test_all_pongs_fan(self):
        hand = PlayerHand([
            Tile(Suit.WAN, 1), Tile(Suit.WAN, 1), Tile(Suit.WAN, 1),
            Tile(Suit.DOT, 5), Tile(Suit.DOT, 5), Tile(Suit.DOT, 5),
            Tile(Suit.BAM, 9), Tile(Suit.BAM, 9), Tile(Suit.BAM, 9),
            Tile(Suit.WIND, 1), Tile(Suit.WIND, 1), Tile(Suit.WIND, 1),
            Tile(Suit.DRAGON, 1)
        ])
        win_tile = Tile(Suit.DRAGON, 1)
        breakdown = calculate_fan(hand, win_tile, is_self_draw=False)

        pattern_names = [name for name, _ in breakdown.patterns]
        self.assertIn("碰碰胡", pattern_names)

    def test_fan_to_points(self):
        self.assertEqual(fan_to_points(0), 1)
        self.assertEqual(fan_to_points(1), 2)
        self.assertEqual(fan_to_points(3), 8)
        self.assertEqual(fan_to_points(7), 128)
        self.assertEqual(fan_to_points(10), 128)


if __name__ == "__main__":
    unittest.main()
