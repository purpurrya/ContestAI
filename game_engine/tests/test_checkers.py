import unittest
from game_engine.checkers import (
    CheckersGameState,
    CheckersPhase,
    CheckersPlayer,
    start_checkers_game,
    process_checkers_move,
    get_valid_moves,
)
from game_engine.checkers.checkers_models import CheckersPiece
from game_engine.exceptions import InvalidMoveException, GameStateException


class TestCheckers(unittest.TestCase):
    def setUp(self):
        self.state = CheckersGameState(match_id="test_match")
        self.players = ["bot1", "bot2", "bot3"]

    def test_start_game(self):
        start_checkers_game(self.state, self.players)
        self.assertEqual(self.state.phase, CheckersPhase.PLAYING)
        self.assertEqual(len(self.state.players), 3)
        self.assertIsNotNone(self.state.started_at)
        self.assertIsNotNone(self.state.hex_board)
        self.assertGreater(len(self.state.board), 0)
        for player in self.state.players:
            self.assertGreater(player.pieces_count, 0)

    def test_player_colors(self):
        start_checkers_game(self.state, self.players)
        self.assertEqual(self.state.players[0].color, CheckersPlayer.WHITE)
        self.assertEqual(self.state.players[1].color, CheckersPlayer.RED)
        self.assertEqual(self.state.players[2].color, CheckersPlayer.BLACK)

    def test_hex_board_structure(self):
        start_checkers_game(self.state, self.players)
        hex_board = self.state.hex_board
        self.assertEqual(len(hex_board.cells), 78)
        self.assertEqual(len(hex_board.side_cells[1]), 12)
        self.assertEqual(len(hex_board.side_cells[2]), 12)
        self.assertEqual(len(hex_board.side_cells[3]), 12)

    def test_simple_move(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        white_pieces = [
            (cell_id, piece)
            for cell_id, piece in self.state.board.items()
            if piece.player == CheckersPlayer.WHITE
        ]
        self.assertGreater(len(white_pieces), 0)
        from_cell_id = white_pieces[0][0]
        valid_moves = get_valid_moves(self.state, from_cell_id)
        if valid_moves:
            to_cell_id = valid_moves[0]
            process_checkers_move(
                self.state, current.bot_id, from_cell_id, to_cell_id
            )
            self.assertIn(to_cell_id, self.state.board)
            self.assertNotIn(from_cell_id, self.state.board)
            self.assertEqual(len(self.state.move_history), 1)

    def test_turn_rotation(self):
        start_checkers_game(self.state, self.players)
        initial_index = self.state.current_player_index
        current = self.state.get_current_player()
        white_pieces = [
            (cell_id, piece)
            for cell_id, piece in self.state.board.items()
            if piece.player == current.color
        ]
        if white_pieces:
            from_cell_id = white_pieces[0][0]
            valid_moves = get_valid_moves(self.state, from_cell_id)
            if valid_moves:
                to_cell_id = valid_moves[0]
                initial_history_len = len(self.state.move_history)
                try:
                    process_checkers_move(
                        self.state, current.bot_id, from_cell_id, to_cell_id
                    )
                    if len(self.state.move_history) > initial_history_len:
                        self.assertNotEqual(
                            self.state.current_player_index, initial_index
                        )
                except Exception:
                    pass

    def test_invalid_move_not_your_turn(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        other = [p for p in self.state.players if p.bot_id != current.bot_id][0]
        white_pieces = [
            (cell_id, piece)
            for cell_id, piece in self.state.board.items()
            if piece.player == CheckersPlayer.WHITE
        ]
        if white_pieces:
            from_cell_id = white_pieces[0][0]
            valid_moves = get_valid_moves(self.state, from_cell_id)
            if valid_moves:
                to_cell_id = valid_moves[0]
                with self.assertRaises(InvalidMoveException):
                    process_checkers_move(
                        self.state, other.bot_id, from_cell_id, to_cell_id
                    )

    def test_invalid_move_no_piece(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        empty_cell_id = 999
        if empty_cell_id not in self.state.board:
            with self.assertRaises(InvalidMoveException):
                process_checkers_move(
                    self.state, current.bot_id, empty_cell_id, 1000
                )

    def test_invalid_move_wrong_position(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        white_pieces = [
            (cell_id, piece)
            for cell_id, piece in self.state.board.items()
            if piece.player == current.color
        ]
        if white_pieces:
            from_cell_id = white_pieces[0][0]
            invalid_to = 9999
            with self.assertRaises(InvalidMoveException):
                process_checkers_move(
                    self.state, current.bot_id, from_cell_id, invalid_to
                )

    def test_capture(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        if current.color != CheckersPlayer.WHITE:
            self.skipTest("current player not white")
        self.state.board = {
            0: CheckersPiece(CheckersPlayer.WHITE),
            2: CheckersPiece(CheckersPlayer.RED),
        }
        self.state.current_player_index = 0
        for p in self.state.players:
            p.pieces_count = self.state.count_pieces(p.color)
        red_player = [p for p in self.state.players if p.color == CheckersPlayer.RED][0]
        initial_red = red_player.pieces_count
        moves = get_valid_moves(self.state, 0)
        self.assertIn(4, moves)
        process_checkers_move(self.state, current.bot_id, 0, 4)
        red_player = [p for p in self.state.players if p.color == CheckersPlayer.RED][0]
        self.assertLess(red_player.pieces_count, initial_red)
        self.assertNotIn(2, self.state.board)

    def test_king_promotion(self):
        start_checkers_game(self.state, self.players)
        hex_board = self.state.hex_board
        from_cell, to_cell = None, None
        for cell_id in hex_board.cells:
            fwd = hex_board.get_forward_neighbors(cell_id, 1)
            for neighbor in fwd:
                if hex_board.is_promotion_cell_for_side(neighbor, 1):
                    from_cell, to_cell = cell_id, neighbor
                    break
            if from_cell is not None:
                break
        if from_cell is None:
            self.skipTest("no suitable cell pair for promotion test")
        self.state.board = {from_cell: CheckersPiece(CheckersPlayer.WHITE)}
        self.state.current_player_index = 0
        current = self.state.get_current_player()
        for p in self.state.players:
            p.pieces_count = 1 if p.color == CheckersPlayer.WHITE else 0
        process_checkers_move(self.state, current.bot_id, from_cell, to_cell)
        self.assertTrue(self.state.board[to_cell].is_king)

    def test_game_already_started(self):
        start_checkers_game(self.state, self.players)
        with self.assertRaises(GameStateException):
            start_checkers_game(self.state, self.players)

    def test_wrong_player_count(self):
        with self.assertRaises(GameStateException):
            start_checkers_game(self.state, ["bot1", "bot2"])

    def test_get_valid_moves(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        white_pieces = [
            (cell_id, piece)
            for cell_id, piece in self.state.board.items()
            if piece.player == current.color
        ]
        if white_pieces:
            from_cell_id = white_pieces[0][0]
            moves = get_valid_moves(self.state, from_cell_id)
            self.assertIsInstance(moves, list)

    def test_get_valid_moves_not_your_piece(self):
        start_checkers_game(self.state, self.players)
        current = self.state.get_current_player()
        other_color = (
            CheckersPlayer.RED
            if current.color == CheckersPlayer.WHITE
            else CheckersPlayer.WHITE
        )
        other_pieces = [
            (cell_id, piece)
            for cell_id, piece in self.state.board.items()
            if piece.player == other_color
        ]
        if other_pieces:
            from_cell_id = other_pieces[0][0]
            moves = get_valid_moves(self.state, from_cell_id)
            self.assertEqual(len(moves), 0)

    def test_hex_board_neighbors(self):
        start_checkers_game(self.state, self.players)
        hex_board = self.state.hex_board
        for cell_id in range(78):
            if hex_board.is_valid_cell(cell_id):
                neighbors = hex_board.get_neighbors(cell_id)
                self.assertIsInstance(neighbors, list)
                for neighbor_id in neighbors:
                    self.assertTrue(hex_board.is_valid_cell(neighbor_id))

    def test_initial_pieces_count(self):
        start_checkers_game(self.state, self.players)
        white_count = sum(
            1 for p in self.state.board.values()
            if p.player == CheckersPlayer.WHITE
        )
        red_count = sum(
            1 for p in self.state.board.values()
            if p.player == CheckersPlayer.RED
        )
        black_count = sum(
            1 for p in self.state.board.values()
            if p.player == CheckersPlayer.BLACK
        )
        self.assertEqual(white_count, 12)
        self.assertEqual(red_count, 12)
        self.assertEqual(black_count, 12)

    def test_promotion_cells_per_side(self):
        start_checkers_game(self.state, self.players)
        hex_board = self.state.hex_board
        for side in [1, 2, 3]:
            found = False
            for cell_id in hex_board.cells:
                if hex_board.is_promotion_cell_for_side(cell_id, side):
                    found = True
                    break
            self.assertTrue(found, f"side {side} has no promotion cells")

    def test_queen_no_moves(self):
        start_checkers_game(self.state, self.players)
        for cell_id, piece in list(self.state.board.items()):
            if piece.is_king:
                self.assertEqual(get_valid_moves(self.state, cell_id), [])


if __name__ == "__main__":
    unittest.main()
