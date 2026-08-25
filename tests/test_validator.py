"""Tests for Mahjong win validator and claim detection."""

import unittest
from tmj.engine.tiles import Tile, Suit
from tmj.engine.hand import PlayerHand
from tmj.engine.validator import (
    is_winning_hand, can_win_on_discard, can_pong, can_gang_on_discard, get_chow_combinations
)


class TestValidator(unittest.TestCase):

    def test_standard_winning_hand(self):
        tiles = [
            Tile(Suit.WAN, 1), Tile(Suit.WAN, 2), Tile(Suit.WAN, 3),
            Tile(Suit.DOT, 4), Tile(Suit.DOT, 5), Tile(Suit.DOT, 6),
            Tile(Suit.BAM, 7), Tile(Suit.BAM, 8), Tile(Suit.BAM, 9),
            Tile(Suit.WIND, 1), Tile(Suit.WIND, 1), Tile(Suit.WIND, 1),
            Tile(Suit.DRAGON, 1), Tile(Suit.DRAGON, 1)
        ]
        self.assertTrue(is_winning_hand(tiles))

    def test_non_winning_hand(self):
        tiles = [
            Tile(Suit.WAN, 1), Tile(Suit.WAN, 2), Tile(Suit.WAN, 3),
            Tile(Suit.DOT, 4), Tile(Suit.DOT, 5), Tile(Suit.DOT, 7),
            Tile(Suit.BAM, 7), Tile(Suit.BAM, 8), Tile(Suit.BAM, 9),
            Tile(Suit.WIND, 1), Tile(Suit.WIND, 1), Tile(Suit.WIND, 1),
            Tile(Suit.DRAGON, 1), Tile(Suit.DRAGON, 1)
        ]
        self.assertFalse(is_winning_hand(tiles))

    def test_seven_pairs_win(self):
        tiles = []
        for i in range(1, 8):
            tiles.append(Tile(Suit.WAN, i))
            tiles.append(Tile(Suit.WAN, i))
        self.assertEqual(len(tiles), 14)
        self.assertTrue(is_winning_hand(tiles))

    def test_thirteen_orphans_win(self):
        tiles = [
            Tile(Suit.WAN, 1), Tile(Suit.WAN, 9),
            Tile(Suit.DOT, 1), Tile(Suit.DOT, 9),
            Tile(Suit.BAM, 1), Tile(Suit.BAM, 9),
            Tile(Suit.WIND, 1), Tile(Suit.WIND, 2), Tile(Suit.WIND, 3), Tile(Suit.WIND, 4),
            Tile(Suit.DRAGON, 1), Tile(Suit.DRAGON, 2), Tile(Suit.DRAGON, 3),
            Tile(Suit.DRAGON, 3)
        ]
        self.assertEqual(len(tiles), 14)
        self.assertTrue(is_winning_hand(tiles))

    def test_claim_detection(self):
        hand = PlayerHand([Tile(Suit.WAN, 1), Tile(Suit.WAN, 1), Tile(Suit.BAM, 3), Tile(Suit.BAM, 4)])
        target_pong = Tile(Suit.WAN, 1)
        self.assertTrue(can_pong(hand, target_pong))

        target_gang = Tile(Suit.WAN, 1)
        self.assertFalse(can_gang_on_discard(hand, target_gang))

        target_chow = Tile(Suit.BAM, 5)
        combos = get_chow_combinations(hand.concealed, target_chow)
        self.assertEqual(len(combos), 1)


if __name__ == "__main__":
    unittest.main()
