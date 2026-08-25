"""Tests for MahjongGame match initialization and turn progression."""

import unittest
from tmj.engine.game import MahjongGame, GamePhase


class TestGame(unittest.TestCase):

    def test_game_initialization(self):
        game = MahjongGame(seed=42)
        game.start_new_hand()

        self.assertEqual(game.phase, GamePhase.DISCARD_TURN)
        self.assertEqual(len(game.hands), 4)
        self.assertEqual(game.hands[0].total_tile_count, 14)
        self.assertEqual(game.hands[1].total_tile_count, 13)
        self.assertEqual(game.hands[2].total_tile_count, 13)
        self.assertEqual(game.hands[3].total_tile_count, 13)
        self.assertEqual(game.wall.remaining_count, 69)

    def test_player_discard_and_turn(self):
        game = MahjongGame(seed=100)
        game.start_new_hand()

        discarded = game.player_discard(0, 0)
        self.assertIsNotNone(discarded)
        self.assertEqual(len(game.discard_pool), 1)


if __name__ == "__main__":
    unittest.main()
