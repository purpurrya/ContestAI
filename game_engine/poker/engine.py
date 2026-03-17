from datetime import datetime
from .utils import Deck
from ..exceptions import InvalidMoveException, GameStateException, GameOverException
from .models import GameState, GamePhase, MoveType, PlayerState


def start_game(state, player_ids):
    # раздача по одной карте, первый ход после дилера
    if state.phase != GamePhase.WAITING:
        raise GameStateException("Game already started")
    
    if len(player_ids) < 2:
        raise GameStateException("Need at least 2 players")
    
    state.players = [PlayerState(bot_id=pid) for pid in player_ids]
    state.dealer_index = 0
    state.current_player_index = 0
    state.last_bettor_index = -1
    state.phase = GamePhase.BETTING
    state.started_at = datetime.now()
    
    deck = Deck()
    for player in state.players:
        player.card = deck.deal()
    
    next_player = state.get_next_active_player_index(state.dealer_index)
    if next_player is not None:
        state.current_player_index = next_player


def process_move(state, bot_id, move_type, amount=0):
    # фолд бет колл чек, потом переход хода или конец раунда
    if state.phase != GamePhase.BETTING:
        raise GameStateException("Not in betting phase")
    
    player = state.get_player(bot_id)
    if not player or player.is_folded or not player.is_active:
        raise InvalidMoveException("Invalid player")
    
    if state.current_player_index >= len(state.players):
        raise GameStateException("Invalid player index")
    
    current = state.players[state.current_player_index]
    if current.bot_id != bot_id:
        raise InvalidMoveException("Not your turn")
    
    if move_type == MoveType.FOLD:
        player.is_folded = True
        state.move_history.append({
            "bot_id": bot_id,
            "move": move_type.value,
            "timestamp": datetime.now().isoformat()
        })
    
    elif move_type == MoveType.BET:
        if amount < state.min_bet or amount > state.max_bet:
            raise InvalidMoveException("Invalid bet amount")
        if amount > player.chips:
            raise InvalidMoveException("Not enough chips")
        
        bet_diff = amount - player.current_bet
        if bet_diff <= 0:
            raise InvalidMoveException("Bet must be higher than current")
        
        player.chips -= bet_diff
        player.current_bet = amount
        player.total_bet += bet_diff
        state.current_bet = amount
        state.pot += bet_diff
        state.last_bettor_index = state.current_player_index
        
        state.move_history.append({
            "bot_id": bot_id,
            "move": move_type.value,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        })
    
    elif move_type == MoveType.CALL:
        call_amount = state.current_bet - player.current_bet
        if call_amount == 0:
            raise InvalidMoveException("Nothing to call")
        if call_amount > player.chips:
            raise InvalidMoveException("Not enough chips")
        
        player.chips -= call_amount
        player.current_bet = state.current_bet
        player.total_bet += call_amount
        state.pot += call_amount
        
        state.move_history.append({
            "bot_id": bot_id,
            "move": move_type.value,
            "amount": call_amount,
            "timestamp": datetime.now().isoformat()
        })
    
    elif move_type == MoveType.CHECK:
        if player.current_bet < state.current_bet:
            raise InvalidMoveException("Cannot check, must call")
        
        state.move_history.append({
            "bot_id": bot_id,
            "move": move_type.value,
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        raise InvalidMoveException("Invalid move type")
    
    _advance_turn(state)


def _advance_turn(state):
    # следующий активный или конец раунда
    if state.is_betting_round_complete():
        _end_betting_round(state)
        return
    
    active_count = len(state.get_active_players())
    if active_count <= 1:
        _end_betting_round(state)
        return
    
    next_idx = state.get_next_active_player_index(state.current_player_index)
    if next_idx is None:
        _end_betting_round(state)
        return
    
    state.current_player_index = next_idx


def _end_betting_round(state):
    # сравнение карт у активных, победитель забирает банк
    active = state.get_active_players()
    
    if len(active) == 0:
        state.phase = GamePhase.FINISHED
        state.finished_at = datetime.now()
        return
    
    if len(active) == 1:
        winner = active[0]
        winner.chips += state.pot
        state.winner_id = winner.bot_id
        state.phase = GamePhase.FINISHED
        state.finished_at = datetime.now()
        return
    
    winner = active[0]
    for player in active[1:]:
        if player.card.compare_to(winner.card) > 0:
            winner = player
    
    winner.chips += state.pot
    state.winner_id = winner.bot_id
    state.phase = GamePhase.FINISHED
    state.finished_at = datetime.now()


def reset_for_next_hand(state):
    # новый дилер, сброс ставок и пасов, новая раздача
    if state.phase != GamePhase.FINISHED:
        raise GameStateException("Game not finished")
    
    active = [p for p in state.players if p.is_active]
    if len(active) < 2:
        raise GameStateException("Not enough active players")
    
    state.rotate_dealer()
    
    for player in state.players:
        if player.is_active:
            player.current_bet = 0
            player.total_bet = 0
            player.is_folded = False
    
    state.pot = 0
    state.current_bet = 0
    state.last_bettor_index = -1
    state.winner_id = None
    state.move_history = []
    state.finished_at = None
    
    deck = Deck()
    for player in state.players:
        if player.is_active:
            player.card = deck.deal()
    
    next_player = state.get_next_active_player_index(state.dealer_index)
    if next_player is not None:
        state.current_player_index = next_player
    
    state.phase = GamePhase.BETTING

