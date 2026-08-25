"""Tests for Tile class and deck generation."""

import unittest
from tmj.engine.tiles import Tile, Suit, create_full_deck


class TestTiles(unittest.TestCase):

    def test_full_deck_creation(self):
        deck = create_full_deck()
        self.assertEqual(len(deck), 136)

        wan_tiles = [t for t in deck if t.suit == Suit.WAN]
        self.assertEqual(len(wan_tiles), 36)

        dot_tiles = [t for t in deck if t.suit == Suit.DOT]
        self.assertEqual(len(dot_tiles), 36)

        bam_tiles = [t for t in deck if t.suit == Suit.BAM]
        self.assertEqual(len(bam_tiles), 36)

        wind_tiles = [t for t in deck if t.suit == Suit.WIND]
        self.assertEqual(len(wind_tiles), 16)

        dragon_tiles = [t for t in deck if t.suit == Suit.DRAGON]
        self.assertEqual(len(dragon_tiles), 12)

    def test_tile_properties(self):
        t1 = Tile(Suit.WAN, 1)
        self.assertTrue(t1.is_terminal)
        self.assertFalse(t1.is_honor)
        self.assertEqual(t1.name, "一萬")
        self.assertEqual(t1.glyph, "🀇")

        red_dragon = Tile(Suit.DRAGON, 1)
        self.assertTrue(red_dragon.is_honor)
        self.assertEqual(red_dragon.name, "中")
        self.assertEqual(red_dragon.glyph, "🀄")

    def test_tile_sorting(self):
        t_wan9 = Tile(Suit.WAN, 9)
        t_dot1 = Tile(Suit.DOT, 1)
        t_bam5 = Tile(Suit.BAM, 5)
        t_wind_east = Tile(Suit.WIND, 1)

        tiles = [t_wind_east, t_dot1, t_wan9, t_bam5]
        tiles.sort()
        self.assertEqual(tiles, [t_wan9, t_dot1, t_bam5, t_wind_east])


if __name__ == "__main__":
    unittest.main()
