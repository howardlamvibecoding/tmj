"""Mahjong Game State Machine and Match Engine."""

from enum import Enum
from typing import List, Dict, Optional, Tuple
from .tiles import Tile, Suit
from .hand import PlayerHand, Meld, MeldType
from .wall import Wall
from .ai import MahjongAI
from .validator import (
    can_win_on_discard, can_win_on_self_draw, can_pong, can_gang_on_discard,
    get_chow_combinations, get_concealed_gang_candidates, get_add_gang_candidates
)
from .scoring import calculate_fan, fan_to_points, FanBreakdown


class GamePhase(str, Enum):
    IDLE = "IDLE"
    DEALING = "DEALING"
    DRAW_TURN = "DRAW_TURN"
    DISCARD_TURN = "DISCARD_TURN"
    CLAIM_WINDOW = "CLAIM_WINDOW"
    GAME_OVER = "GAME_OVER"


PLAYER_NAMES = ["您 (東/下家)", "電腦 北 (對家)", "電腦 西 (上家)", "電腦 南 (下家)"]
WIND_NAMES = {1: "東風圈", 2: "南風圈", 3: "西風圈", 4: "北風圈"}
PLAYER_WINDS = {0: "東", 1: "北", 2: "西", 3: "南"}


class GameResult:
    """Stores result of a finished hand/match."""

    def __init__(
        self,
        winner_index: Optional[int],
        loser_index: Optional[int],  # Discarder (if Ron) or None (if Self-Draw or Exhausted)
        winning_tile: Optional[Tile],
        is_self_draw: bool,
        is_draw_match: bool,
        breakdown: Optional[FanBreakdown] = None,
        point_transfers: Optional[Dict[int, int]] = None,
    ):
        self.winner_index = winner_index
        self.loser_index = loser_index
        self.winning_tile = winning_tile
        self.is_self_draw = is_self_draw
        self.is_draw_match = is_draw_match
        self.breakdown = breakdown or FanBreakdown()
        self.point_transfers = point_transfers or {0: 0, 1: 0, 2: 0, 3: 0}


class ClaimOpportunity:
    """Represents claim options available to a player for a discarded tile."""

    def __init__(self, player_index: int, can_win: bool = False, can_pong: bool = False, can_gang: bool = False, chow_combos: Optional[List[Tuple[Tile, Tile]]] = None):
        self.player_index = player_index
        self.can_win = can_win
        self.can_pong = can_pong
        self.can_gang = can_gang
        self.chow_combos = chow_combos or []

    @property
    def has_any(self) -> bool:
        return self.can_win or self.can_pong or self.can_gang or len(self.chow_combos) > 0


class MahjongGame:
    """Core game state and logic controller for 4-player HK Mahjong."""

    def __init__(self, seed: Optional[int] = None):
        self.wall = Wall(seed)
        self.hands: List[PlayerHand] = [PlayerHand() for _ in range(4)]
        self.ai_players: List[MahjongAI] = [MahjongAI(i, PLAYER_NAMES[i]) for i in range(4)]
        self.discard_pool: List[Tuple[int, Tile]] = []  # (player_index, tile)
        self.scores: List[int] = [500, 500, 500, 500]   # Starting score chips
        self.dealer_index: int = 0
        self.current_turn: int = 0
        self.prevalent_wind: int = 1                     # 1=East
        self.phase: GamePhase = GamePhase.IDLE
        self.last_discarded_tile: Optional[Tile] = None
        self.last_discarder: Optional[int] = None
        self.active_claims: Dict[int, ClaimOpportunity] = {}
        self.game_result: Optional[GameResult] = None

    def start_new_hand(self, seed: Optional[int] = None):
        """Initializes a new hand: resets wall, deals tiles, sets initial turn."""
        self.wall.reset(seed)
        self.hands = [PlayerHand() for _ in range(4)]
        self.discard_pool = []
        self.game_result = None

        # Deal initial tiles
        dealt_hands, dealer_extra = self.wall.deal_hands(self.dealer_index)
        for i in range(4):
            self.hands[i] = PlayerHand(dealt_hands[i])

        # Dealer gets 14th tile
        self.current_turn = self.dealer_index
        self.hands[self.dealer_index].add_tile(dealer_extra)

        self.phase = GamePhase.DISCARD_TURN

    def player_draw(self, player_idx: int) -> Optional[Tile]:
        """Draws tile from wall for current player turn."""
        tile = self.wall.draw()
        if tile is None:
            # Wall exhausted -> Exhaustive Draw (流局)
            self._handle_exhaustive_draw()
            return None
        self.hands[player_idx].add_tile(tile)
        self.phase = GamePhase.DISCARD_TURN
        return tile

    def player_discard(self, player_idx: int, tile_index: int) -> Optional[Tile]:
        """Player discards tile at index."""
        if self.phase != GamePhase.DISCARD_TURN or player_idx != self.current_turn:
            return None

        discarded = self.hands[player_idx].discard(tile_index)
        if not discarded:
            return None

        self.last_discarded_tile = discarded
        self.last_discarder = player_idx
        self.discard_pool.append((player_idx, discarded))

        # Check claim opportunities for other players
        self._evaluate_claims(player_idx, discarded)

        if any(c.has_any for c in self.active_claims.values()):
            self.phase = GamePhase.CLAIM_WINDOW
        else:
            # Advance turn to next player
            self.next_turn()

        return discarded

    def _evaluate_claims(self, discarder_idx: int, discarded_tile: Tile):
        """Evaluates claim opportunities for players 0-3 (excluding discarder)."""
        self.active_claims = {}
        for p in range(4):
            if p == discarder_idx:
                continue

            hand = self.hands[p]
            win = can_win_on_discard(hand, discarded_tile)
            pong = can_pong(hand, discarded_tile)
            gang = can_gang_on_discard(hand, discarded_tile)
            # Chow only available to next player (right of discarder)
            is_next = (p == (discarder_idx + 1) % 4)
            chows = get_chow_combinations(hand.concealed, discarded_tile) if is_next else []

            opp = ClaimOpportunity(p, win, pong, gang, chows)
            if opp.has_any:
                self.active_claims[p] = opp

    def execute_claim_win(self, player_idx: int) -> GameResult:
        """Executes a Win claim on discarded tile (Ron 胡)."""
        winner = player_idx
        loser = self.last_discarder
        tile = self.last_discarded_tile

        # Remove tile from discard pool
        if self.discard_pool and self.discard_pool[-1][1] == tile:
            self.discard_pool.pop()

        breakdown = calculate_fan(
            self.hands[winner], tile, is_self_draw=False,
            seat_wind=((winner - self.dealer_index) % 4) + 1, prevalent_wind=self.prevalent_wind
        )

        pts = fan_to_points(breakdown.total_fan)
        transfers = {0: 0, 1: 0, 2: 0, 3: 0}
        # In HK Mahjong, discarder pays total points to winner
        transfers[winner] += (pts * 3)
        transfers[loser] -= (pts * 3)

        for p in range(4):
            self.scores[p] += transfers[p]

        self.game_result = GameResult(
            winner_index=winner, loser_index=loser, winning_tile=tile,
            is_self_draw=False, is_draw_match=False, breakdown=breakdown,
            point_transfers=transfers
        )
        self.phase = GamePhase.GAME_OVER

        # Rotate dealer if human dealer lost or non-dealer won
        if winner != self.dealer_index:
            self.dealer_index = (self.dealer_index + 1) % 4

        return self.game_result

    def execute_self_draw_win(self, player_idx: int) -> GameResult:
        """Executes a Self-Draw Win (自摸)."""
        winner = player_idx
        tile = self.hands[winner].drawn or self.hands[winner].concealed[-1]

        breakdown = calculate_fan(
            self.hands[winner], tile, is_self_draw=True,
            seat_wind=((winner - self.dealer_index) % 4) + 1, prevalent_wind=self.prevalent_wind
        )

        pts = fan_to_points(breakdown.total_fan)
        transfers = {0: 0, 1: 0, 2: 0, 3: 0}
        # All 3 opponents pay pts to winner
        for p in range(4):
            if p == winner:
                transfers[p] += (pts * 3)
            else:
                transfers[p] -= pts

        for p in range(4):
            self.scores[p] += transfers[p]

        self.game_result = GameResult(
            winner_index=winner, loser_index=None, winning_tile=tile,
            is_self_draw=True, is_draw_match=False, breakdown=breakdown,
            point_transfers=transfers
        )
        self.phase = GamePhase.GAME_OVER

        if winner != self.dealer_index:
            self.dealer_index = (self.dealer_index + 1) % 4

        return self.game_result

    def execute_claim_pong(self, player_idx: int) -> bool:
        """Executes a Pong claim on discarded tile."""
        tile = self.last_discarded_tile
        if not tile:
            return False

        if self.discard_pool and self.discard_pool[-1][1] == tile:
            self.discard_pool.pop()

        removed = self.hands[player_idx].remove_tiles(tile, 2)
        meld = Meld(MeldType.PONG, removed + [tile], target_tile=tile, source_player=self.last_discarder)
        self.hands[player_idx].melds.append(meld)

        self.current_turn = player_idx
        self.phase = GamePhase.DISCARD_TURN
        self.active_claims = {}
        return True

    def execute_claim_chow(self, player_idx: int, t1: Tile, t2: Tile) -> bool:
        """Executes a Chow claim on discarded tile."""
        tile = self.last_discarded_tile
        if not tile:
            return False

        if self.discard_pool and self.discard_pool[-1][1] == tile:
            self.discard_pool.pop()

        removed1 = self.hands[player_idx].remove_tiles(t1, 1)
        removed2 = self.hands[player_idx].remove_tiles(t2, 1)
        meld = Meld(MeldType.CHOW, removed1 + removed2 + [tile], target_tile=tile, source_player=self.last_discarder)
        self.hands[player_idx].melds.append(meld)

        self.current_turn = player_idx
        self.phase = GamePhase.DISCARD_TURN
        self.active_claims = {}
        return True

    def pass_claims(self):
        """Passes all claim opportunities and advances turn."""
        self.active_claims = {}
        self.next_turn()

    def next_turn(self):
        """Advances turn to next player and draws a tile."""
        self.current_turn = (self.current_turn + 1) % 4
        self.player_draw(self.current_turn)

    def process_ai_turn_if_needed(self):
        """Automatically processes AI logic when turn is an AI player (players 1, 2, 3)."""
        if self.phase == GamePhase.DISCARD_TURN and self.current_turn != 0:
            ai = self.ai_players[self.current_turn]
            hand = self.hands[self.current_turn]

            # AI self-draw win check
            if can_win_on_self_draw(hand):
                self.execute_self_draw_win(self.current_turn)
                return

            # AI chooses discard
            discard_idx = ai.choose_discard(hand)
            self.player_discard(self.current_turn, discard_idx)

        elif self.phase == GamePhase.CLAIM_WINDOW:
            # Resolve AI claims automatically
            # Check if any AI player can win
            win_claimants = [p for p, opp in self.active_claims.items() if opp.can_win]
            if win_claimants:
                self.execute_claim_win(win_claimants[0])
                return

            # If Human player (0) has active claims, pause for human input
            if 0 in self.active_claims:
                return

            # Process AI Pong/Chow claims
            for p, opp in list(self.active_claims.items()):
                if p != 0:
                    ai = self.ai_players[p]
                    if opp.can_pong and ai.should_claim_pong(self.hands[p], self.last_discarded_tile):
                        self.execute_claim_pong(p)
                        return
                    chow_pair = ai.should_claim_chow(self.hands[p], self.last_discarded_tile)
                    if chow_pair:
                        self.execute_claim_chow(p, chow_pair[0], chow_pair[1])
                        return

            # No claims triggered -> pass claims
            self.pass_claims()

    def _handle_exhaustive_draw(self):
        """Handles wall exhaustion (流局)."""
        self.game_result = GameResult(
            winner_index=None, loser_index=None, winning_tile=None,
            is_self_draw=False, is_draw_match=True
        )
        self.phase = GamePhase.GAME_OVER
        # Rotate dealer on draw match
        self.dealer_index = (self.dealer_index + 1) % 4
