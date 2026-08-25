"""Main Textual Application for Terminal Mahjong (TMJ)."""

from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, Button, Label, Log
from textual.binding import Binding
from textual.screen import ModalScreen

from ..engine.game import MahjongGame, GamePhase, PLAYER_NAMES, WIND_NAMES
from ..engine.tiles import Tile
from ..engine.hand import MeldType
from .widgets import HandWidget, DiscardPoolWidget, InfoWidget, render_tile_card, KEYS


class GameResultModal(ModalScreen):
    """Modal displaying end of game win/draw results and fan scoring breakdown."""

    def __init__(self, game: MahjongGame, **kwargs):
        super().__init__(**kwargs)
        self.game = game

    def compose(self) -> ComposeResult:
        res = self.game.game_result
        yield Container(
            Static("🀄 對局結束 🀄", id="modal_title", classes="modal_header"),
            Static(self.format_result_body(), id="modal_body"),
            Horizontal(
                Button("下一局 (Space / Enter)", variant="primary", id="btn_next_round"),
                Button("退出遊戲 (Q)", variant="error", id="btn_quit"),
                classes="modal_buttons"
            ),
            id="modal_dialog"
        )

    def format_result_body(self) -> str:
        res = self.game.game_result
        if not res:
            return "對局已結束。"

        if res.is_draw_match:
            return "⚖️ [bold yellow]流局！牌牆已抽完，無人食胡。[/bold yellow]"

        winner = PLAYER_NAMES[res.winner_index] if res.winner_index is not None else "未知"
        lines = []
        if res.is_self_draw:
            lines.append(f"🎉 [bold green]勝者: {winner} (自摸！)[/bold green]")
        else:
            loser = PLAYER_NAMES[res.loser_index] if res.loser_index is not None else "未知"
            lines.append(f"🎉 [bold green]勝者: {winner} (出衝放銃者: {loser})[/bold green]")

        if res.winning_tile:
            lines.append(f"🀄 胡牌: {res.winning_tile.glyph} {res.winning_tile.name}")

        lines.append("\n[bold yellow]--- 番數明細 (HK Fan Breakdown) ---[/bold yellow]")
        for name, fan in res.breakdown.patterns:
            lines.append(f" • {name}: +{fan} 番")
        lines.append(f"👉 [bold magenta]總計: {res.breakdown.total_fan} 番 ({res.breakdown} 籌碼點數)[/bold magenta]")

        lines.append("\n[bold cyan]--- 籌碼變動 (Score Points) ---[/bold cyan]")
        for p, name in enumerate(PLAYER_NAMES):
            diff = res.point_transfers.get(p, 0)
            sign = "+" if diff >= 0 else ""
            lines.append(f" • {name}: {sign}{diff} pts  (現有: {self.game.scores[p]})")

        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_next_round":
            self.dismiss(True)
        elif event.button.id == "btn_quit":
            self.app.exit()

    def on_key(self, event) -> None:
        if event.key in ("space", "enter"):
            self.dismiss(True)
        elif event.key == "q":
            self.app.exit()


class TMJApp(App):
    """Main Textual Application for TMJ Terminal Mahjong."""

    TITLE = "🀄 TMJ - Terminal Mahjong (4-Player HK Rules)"
    SUB_TITLE = "Python Textual & Rich Terminal Mahjong"

    CSS = """
    Screen {
        background: #1a1b26;
        color: #a9b1d6;
    }
    #top_info {
        height: 5;
        margin-bottom: 1;
    }
    #game_layout {
        height: 1fr;
    }
    #north_player {
        height: 3;
        content-align: center middle;
        background: #24283b;
        border: solid #7aa2f7;
    }
    #west_east_container {
        height: 1fr;
    }
    #west_player {
        width: 25;
        background: #24283b;
        border: solid #7aa2f7;
        content-align: center middle;
    }
    #east_player {
        width: 25;
        background: #24283b;
        border: solid #7aa2f7;
        content-align: center middle;
    }
    #center_table {
        width: 1fr;
    }
    #human_container {
        height: 9;
        margin-top: 1;
    }
    #action_bar {
        height: 3;
        content-align: center middle;
        background: #1f2335;
        border: solid #e0af68;
    }
    Button {
        margin: 0 1;
    }
    #modal_dialog {
        padding: 1 2;
        background: #24283b;
        border: thick #7aa2f7;
        width: 70;
        height: 22;
        align: center middle;
    }
    .modal_header {
        text-align: center;
        text-style: bold;
        color: #bb9af7;
    }
    .modal_buttons {
        margin-top: 1;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("1", "select_tile(0)", "Discard 1st", show=False),
        Binding("2", "select_tile(1)", "Discard 2nd", show=False),
        Binding("3", "select_tile(2)", "Discard 3rd", show=False),
        Binding("4", "select_tile(3)", "Discard 4th", show=False),
        Binding("5", "select_tile(4)", "Discard 5th", show=False),
        Binding("6", "select_tile(5)", "Discard 6th", show=False),
        Binding("7", "select_tile(6)", "Discard 7th", show=False),
        Binding("8", "select_tile(7)", "Discard 8th", show=False),
        Binding("9", "select_tile(8)", "Discard 9th", show=False),
        Binding("0", "select_tile(9)", "Discard 10th", show=False),
        Binding("q", "select_tile(10)", "Discard 11th", show=False),
        Binding("w", "select_tile(11)", "Discard 12th", show=False),
        Binding("e", "select_tile(12)", "Discard 13th", show=False),
        Binding("r", "select_tile(13)", "Discard Drawn", show=False),

        Binding("c", "action_chow", "吃 (Chow)"),
        Binding("p", "action_pong", "碰 (Pong)"),
        Binding("g", "action_gang", "槓 (Gang)"),
        Binding("h", "action_win", "胡 (Win)"),
        Binding("s", "action_pass", "過 (Pass)"),
        Binding("n", "new_game", "新一局 (New Round)"),
        Binding("ctrl+c", "quit_app", "Quit"),
    ]

    def __init__(self, seed: Optional[int] = None):
        super().__init__()
        self.game = MahjongGame(seed)
        self.game.start_new_hand()

    def compose(self) -> ComposeResult:
        yield Header()
        yield InfoWidget(
            wall_count=self.game.wall.remaining_count,
            prevalent_wind=WIND_NAMES.get(self.game.prevalent_wind, "東風圈"),
            dealer_name=PLAYER_NAMES[self.game.dealer_index],
            id="top_info"
        )
        yield Vertical(
            Static(f"對家: {PLAYER_NAMES[1]} (籌碼: {self.game.scores[1]})", id="north_player"),
            Horizontal(
                Static(f"上家: {PLAYER_NAMES[2]}\n(籌碼: {self.game.scores[2]})", id="west_player"),
                DiscardPoolWidget(self.game.discard_pool, id="center_table"),
                Static(f"下家: {PLAYER_NAMES[3]}\n(籌碼: {self.game.scores[3]})", id="east_player"),
                id="west_east_container"
            ),
            Container(
                HandWidget(self.game.hands[0], is_human=True, id="human_hand"),
                id="human_container"
            ),
            Horizontal(
                Button("吃 [C]", id="btn_chow", variant="success"),
                Button("碰 [P]", id="btn_pong", variant="primary"),
                Button("槓 [G]", id="btn_gang", variant="warning"),
                Button("胡牌 [H]", id="btn_win", variant="error"),
                Button("過 / 跳過 [S]", id="btn_pass", variant="default"),
                id="action_bar"
            ),
            id="game_layout"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        """Refreshes all TUI widgets with current game state."""
        # Check if game ended
        if self.game.phase == GamePhase.GAME_OVER:
            self.push_screen(GameResultModal(self.game), callback=self.on_modal_close)
            return

        # Advance AI turns if it's AI turn
        if self.game.current_turn != 0 or (self.game.phase == GamePhase.CLAIM_WINDOW and 0 not in self.game.active_claims):
            self.game.process_ai_turn_if_needed()
            if self.game.phase == GamePhase.GAME_OVER:
                self.push_screen(GameResultModal(self.game), callback=self.on_modal_close)
                return

        # Update Info Widget
        info_widget = self.query_one(InfoWidget)
        info_widget.wall_count = self.game.wall.remaining_count
        info_widget.prevalent_wind = WIND_NAMES.get(self.game.prevalent_wind, "東風圈")
        info_widget.dealer_name = PLAYER_NAMES[self.game.dealer_index]
        info_widget.refresh()

        # Update Discard Pool
        discard_widget = self.query_one(DiscardPoolWidget)
        discard_widget.discards = self.game.discard_pool
        discard_widget.refresh()

        # Update Human Hand
        hand_widget = self.query_one("#human_hand", HandWidget)
        hand_widget.hand = self.game.hands[0]
        hand_widget.refresh()

        # Action bar buttons state
        claims = self.game.active_claims.get(0)
        can_self_win = (self.game.current_turn == 0 and self.game.phase == GamePhase.DISCARD_TURN and self.game.hands[0].drawn and self.game.ai_players[0].should_claim_win(self.game.hands[0], self.game.hands[0].drawn, is_self_draw=True))

        self.query_one("#btn_chow", Button).disabled = not (claims and len(claims.chow_combos) > 0)
        self.query_one("#btn_pong", Button).disabled = not (claims and claims.can_pong)
        self.query_one("#btn_gang", Button).disabled = not (claims and claims.can_gang)
        self.query_one("#btn_win", Button).disabled = not ((claims and claims.can_win) or can_self_win)
        self.query_one("#btn_pass", Button).disabled = not (claims and claims.has_any)

    def action_select_tile(self, index: int) -> None:
        """Handles key press 1-9/q-r to select tile for discard."""
        if self.game.phase != GamePhase.DISCARD_TURN or self.game.current_turn != 0:
            return

        discarded = self.game.player_discard(0, index)
        if discarded:
            self.refresh_ui()

    def action_action_chow(self) -> None:
        claims = self.game.active_claims.get(0)
        if claims and claims.chow_combos:
            combo = claims.chow_combos[0]
            self.game.execute_claim_chow(0, combo[0], combo[1])
            self.refresh_ui()

    def action_action_pong(self) -> None:
        claims = self.game.active_claims.get(0)
        if claims and claims.can_pong:
            self.game.execute_claim_pong(0)
            self.refresh_ui()

    def action_action_win(self) -> None:
        claims = self.game.active_claims.get(0)
        if claims and claims.can_win:
            self.game.execute_claim_win(0)
            self.refresh_ui()
        elif self.game.current_turn == 0 and self.game.hands[0].drawn:
            self.game.execute_self_draw_win(0)
            self.refresh_ui()

    def action_action_pass(self) -> None:
        if 0 in self.game.active_claims:
            self.game.pass_claims()
            self.refresh_ui()

    def action_new_game(self) -> None:
        self.game.start_new_hand()
        self.refresh_ui()

    def action_quit_app(self) -> None:
        self.exit()

    def on_modal_close(self, result: bool) -> None:
        if result:
            self.game.start_new_hand()
            self.refresh_ui()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_chow":
            self.action_action_chow()
        elif btn_id == "btn_pong":
            self.action_action_pong()
        elif btn_id == "btn_gang":
            claims = self.game.active_claims.get(0)
            if claims and claims.can_gang:
                self.game.execute_claim_pong(0) # Simple gang claim
                self.refresh_ui()
        elif btn_id == "btn_win":
            self.action_action_win()
        elif btn_id == "btn_pass":
            self.action_action_pass()
