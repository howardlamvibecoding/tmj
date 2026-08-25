"""Main Textual Application for Terminal Mahjong (TMJ) with Localization."""

from typing import Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.widgets import Header, Footer, Static, Button, Label, Log
from textual.binding import Binding
from textual.screen import ModalScreen

from ..engine.game import MahjongGame, GamePhase, get_player_name, get_wind_name
from ..engine.tiles import Tile
from ..engine.hand import MeldType
from .widgets import HandWidget, DiscardPoolWidget, InfoWidget, render_tile_card, KEYS


class GameResultModal(ModalScreen):
    """Modal displaying end of game win/draw results and fan scoring breakdown."""

    def __init__(self, game: MahjongGame, lang: str = "zh", **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.lang = lang

    def compose(self) -> ComposeResult:
        title = "🀄 Match Over 🀄" if self.lang == "en" else "🀄 對局結束 🀄"
        next_btn = "Next Round (Space / Enter)" if self.lang == "en" else "下一局 (Space / Enter)"
        quit_btn = "Quit Game (Q)" if self.lang == "en" else "退出遊戲 (Q)"

        yield Container(
            Static(title, id="modal_title", classes="modal_header"),
            Static(self.format_result_body(), id="modal_body"),
            Horizontal(
                Button(next_btn, variant="primary", id="btn_next_round"),
                Button(quit_btn, variant="error", id="btn_quit"),
                classes="modal_buttons"
            ),
            id="modal_dialog"
        )

    def format_result_body(self) -> str:
        res = self.game.game_result
        if not res:
            return "Match finished." if self.lang == "en" else "對局已結束。"

        if res.is_draw_match:
            if self.lang == "en":
                return "⚖️ [bold yellow]Exhaustive Draw! All wall tiles drawn without a winner.[/bold yellow]"
            return "⚖️ [bold yellow]流局！牌牆已抽完，無人食胡。[/bold yellow]"

        winner = get_player_name(res.winner_index, self.lang) if res.winner_index is not None else "Unknown"
        lines = []
        if res.is_self_draw:
            if self.lang == "en":
                lines.append(f"🎉 [bold green]Winner: {winner} (Self-Draw / Tsumo!)[/bold green]")
            else:
                lines.append(f"🎉 [bold green]勝者: {winner} (自摸！)[/bold green]")
        else:
            loser = get_player_name(res.loser_index, self.lang) if res.loser_index is not None else "Unknown"
            if self.lang == "en":
                lines.append(f"🎉 [bold green]Winner: {winner} (Discarder: {loser})[/bold green]")
            else:
                lines.append(f"🎉 [bold green]勝者: {winner} (出衝放銃者: {loser})[/bold green]")

        if res.winning_tile:
            tname = res.winning_tile.get_name(self.lang)
            if self.lang == "en":
                lines.append(f"🀄 Winning Tile: {res.winning_tile.glyph} {tname}")
            else:
                lines.append(f"🀄 胡牌: {res.winning_tile.glyph} {tname}")

        fan_header = "\n[bold yellow]--- HK Fan Scoring Breakdown ---[/bold yellow]" if self.lang == "en" else "\n[bold yellow]--- 番數明細 (HK Fan Breakdown) ---[/bold yellow]"
        lines.append(fan_header)
        for name, fan in res.breakdown.patterns:
            unit_fan = "Fan" if self.lang == "en" else "番"
            lines.append(f" • {name}: +{fan} {unit_fan}")

        total_pts = fan_to_points_label = f"Total: {res.breakdown.total_fan} Fan" if self.lang == "en" else f"總計: {res.breakdown.total_fan}番"
        lines.append(f"👉 [bold magenta]{total_pts}[/bold magenta]")

        score_header = "\n[bold cyan]--- Score Point Transfers ---[/bold cyan]" if self.lang == "en" else "\n[bold cyan]--- 籌碼變動 (Score Points) ---[/bold cyan]"
        lines.append(score_header)
        for p in range(4):
            pname = get_player_name(p, self.lang)
            diff = res.point_transfers.get(p, 0)
            sign = "+" if diff >= 0 else ""
            lines.append(f" • {pname}: {sign}{diff} pts  (Current: {self.game.scores[p]})")

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

        Binding("c", "action_chow", "Chow (吃)"),
        Binding("p", "action_pong", "Pong (碰)"),
        Binding("g", "action_gang", "Gang (槓)"),
        Binding("h", "action_win", "Win (胡)"),
        Binding("s", "action_pass", "Pass (過)"),
        Binding("n", "new_game", "New Round"),
        Binding("ctrl+c", "quit_app", "Quit"),
    ]

    def __init__(self, seed: Optional[int] = None, lang: str = "zh"):
        super().__init__()
        self.lang = lang
        self.game = MahjongGame(seed=seed, lang=lang)
        self.game.start_new_hand()

    def compose(self) -> ComposeResult:
        lbl_chow = "Chow [C]" if self.lang == "en" else "吃 [C]"
        lbl_pong = "Pong [P]" if self.lang == "en" else "碰 [P]"
        lbl_gang = "Gang [G]" if self.lang == "en" else "槓 [G]"
        lbl_win = "Win [H]" if self.lang == "en" else "胡牌 [H]"
        lbl_pass = "Pass [S]" if self.lang == "en" else "過 / 跳過 [S]"

        north_label = f"Opponent: {get_player_name(1, self.lang)} (Score: {self.game.scores[1]})" if self.lang == "en" else f"對家: {get_player_name(1, self.lang)} (籌碼: {self.game.scores[1]})"
        west_label = f"Opponent: {get_player_name(2, self.lang)}\n(Score: {self.game.scores[2]})" if self.lang == "en" else f"上家: {get_player_name(2, self.lang)}\n(籌碼: {self.game.scores[2]})"
        east_label = f"Opponent: {get_player_name(3, self.lang)}\n(Score: {self.game.scores[3]})" if self.lang == "en" else f"下家: {get_player_name(3, self.lang)}\n(籌碼: {self.game.scores[3]})"

        yield Header()
        yield InfoWidget(
            wall_count=self.game.wall.remaining_count,
            prevalent_wind=get_wind_name(self.game.prevalent_wind, self.lang),
            dealer_name=get_player_name(self.game.dealer_index, self.lang),
            lang=self.lang,
            id="top_info"
        )
        yield Vertical(
            Static(north_label, id="north_player"),
            Horizontal(
                Static(west_label, id="west_player"),
                DiscardPoolWidget(self.game.discard_pool, lang=self.lang, id="center_table"),
                Static(east_label, id="east_player"),
                id="west_east_container"
            ),
            Container(
                HandWidget(self.game.hands[0], is_human=True, lang=self.lang, id="human_hand"),
                id="human_container"
            ),
            Horizontal(
                Button(lbl_chow, id="btn_chow", variant="success"),
                Button(lbl_pong, id="btn_pong", variant="primary"),
                Button(lbl_gang, id="btn_gang", variant="warning"),
                Button(lbl_win, id="btn_win", variant="error"),
                Button(lbl_pass, id="btn_pass", variant="default"),
                id="action_bar"
            ),
            id="game_layout"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_ui()

    def refresh_ui(self) -> None:
        if self.game.phase == GamePhase.GAME_OVER:
            self.push_screen(GameResultModal(self.game, lang=self.lang), callback=self.on_modal_close)
            return

        if self.game.current_turn != 0 or (self.game.phase == GamePhase.CLAIM_WINDOW and 0 not in self.game.active_claims):
            self.game.process_ai_turn_if_needed()
            if self.game.phase == GamePhase.GAME_OVER:
                self.push_screen(GameResultModal(self.game, lang=self.lang), callback=self.on_modal_close)
                return

        info_widget = self.query_one(InfoWidget)
        info_widget.wall_count = self.game.wall.remaining_count
        info_widget.prevalent_wind = get_wind_name(self.game.prevalent_wind, self.lang)
        info_widget.dealer_name = get_player_name(self.game.dealer_index, self.lang)
        info_widget.refresh()

        discard_widget = self.query_one(DiscardPoolWidget)
        discard_widget.discards = self.game.discard_pool
        discard_widget.refresh()

        hand_widget = self.query_one("#human_hand", HandWidget)
        hand_widget.hand = self.game.hands[0]
        hand_widget.refresh()

        claims = self.game.active_claims.get(0)
        can_self_win = (self.game.current_turn == 0 and self.game.phase == GamePhase.DISCARD_TURN and self.game.hands[0].drawn and self.game.ai_players[0].should_claim_win(self.game.hands[0], self.game.hands[0].drawn, is_self_draw=True))

        self.query_one("#btn_chow", Button).disabled = not (claims and len(claims.chow_combos) > 0)
        self.query_one("#btn_pong", Button).disabled = not (claims and claims.can_pong)
        self.query_one("#btn_gang", Button).disabled = not (claims and claims.can_gang)
        self.query_one("#btn_win", Button).disabled = not ((claims and claims.can_win) or can_self_win)
        self.query_one("#btn_pass", Button).disabled = not (claims and claims.has_any)

    def action_select_tile(self, index: int) -> None:
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
                self.game.execute_claim_pong(0)
                self.refresh_ui()
        elif btn_id == "btn_win":
            self.action_action_win()
        elif btn_id == "btn_pass":
            self.action_action_pass()
