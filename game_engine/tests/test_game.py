import unittest
from game_engine.poker import GameState, GamePhase, MoveType, start_game, process_move, reset_for_next_hand
from game_engine.exceptions import InvalidMoveException, GameStateException


class TestGame(unittest.TestCase):
    def setUp(self):
        self.state = GameState(match_id="test_match")
        self.players = ["bot1", "bot2", "bot3"]

    def test_start_game(self):
        start_game(self.state, self.players)
        self.assertEqual(self.state.phase, GamePhase.BETTING)
        self.assertEqual(len(self.state.players), 3)
        for p in self.state.players:
            self.assertIsNotNone(p.card)
            self.assertEqual(p.chips, 100)

    def test_bet_and_call(self):
        start_game(self.state, self.players)
        current = self.state.get_current_player()
        
        process_move(self.state, current.bot_id, MoveType.BET, 10)
        self.assertEqual(self.state.current_bet, 10)
        self.assertEqual(current.current_bet, 10)
        
        next_player = self.state.get_current_player()
        process_move(self.state, next_player.bot_id, MoveType.CALL)
        self.assertEqual(next_player.current_bet, 10)

    def test_fold(self):
        start_game(self.state, self.players)
        current = self.state.get_current_player()
        process_move(self.state, current.bot_id, MoveType.FOLD)
        self.assertTrue(current.is_folded)

    def test_check(self):
        start_game(self.state, self.players)
        current = self.state.get_current_player()
        process_move(self.state, current.bot_id, MoveType.CHECK)
        self.assertEqual(current.current_bet, 0)

    def test_betting_round_complete(self):
        start_game(self.state, ["bot1", "bot2"])
        current = self.state.get_current_player()
        other = [p for p in self.state.players if p.bot_id != current.bot_id][0]
        
        process_move(self.state, current.bot_id, MoveType.BET, 5)
        if self.state.phase == GamePhase.BETTING:
            process_move(self.state, other.bot_id, MoveType.CALL)
        
        self.assertEqual(self.state.phase, GamePhase.FINISHED)
        self.assertIsNotNone(self.state.winner_id)

    def test_winner_selection(self):
        start_game(self.state, ["bot1", "bot2"])
        active = self.state.get_active_players()
        
        for p in active:
            p.current_bet = 10
            self.state.pot = 20
        
        from game_engine.poker.engine import _end_betting_round
        _end_betting_round(self.state)
        
        self.assertEqual(self.state.phase, GamePhase.FINISHED)
        self.assertIsNotNone(self.state.winner_id)

    def test_dealer_rotation(self):
        start_game(self.state, self.players)
        initial_dealer = self.state.dealer_index
        
        self.state.phase = GamePhase.FINISHED
        reset_for_next_hand(self.state)
        
        self.assertNotEqual(self.state.dealer_index, initial_dealer)
        self.assertEqual(self.state.phase, GamePhase.BETTING)

    def test_invalid_move_not_your_turn(self):
        start_game(self.state, self.players)
        current = self.state.get_current_player()
        other = [p for p in self.state.players if p.bot_id != current.bot_id][0]
        
        with self.assertRaises(InvalidMoveException):
            process_move(self.state, other.bot_id, MoveType.BET, 10)

    def test_invalid_bet_amount(self):
        start_game(self.state, self.players)
        current = self.state.get_current_player()
        
        with self.assertRaises(InvalidMoveException):
            process_move(self.state, current.bot_id, MoveType.BET, 1000)

    def test_all_fold(self):
        start_game(self.state, ["bot1", "bot2"])
        current = self.state.get_current_player()
        
        process_move(self.state, current.bot_id, MoveType.FOLD)
        self.assertEqual(self.state.phase, GamePhase.FINISHED)


if __name__ == '__main__':
    unittest.main()
