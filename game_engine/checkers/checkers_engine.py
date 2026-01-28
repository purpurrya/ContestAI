from datetime import datetime
from ..exceptions import InvalidMoveException, GameStateException, GameOverException
from .checkers_models import CheckersGameState, CheckersPhase, CheckersPlayer, CheckersPiece, CheckersPlayerState
from .hex_board import create_hex_board


def start_checkers_game(state, player_ids):
    if state.phase != CheckersPhase.WAITING:
        raise GameStateException("Game already started")
    
    if len(player_ids) != 3:
        raise GameStateException("Need exactly 3 players")
    
    colors = [CheckersPlayer.WHITE, CheckersPlayer.RED, CheckersPlayer.BLACK]
    state.players = [CheckersPlayerState(bot_id=pid, color=colors[i]) for i, pid in enumerate(player_ids)]
    state.current_player_index = 0
    state.phase = CheckersPhase.PLAYING
    state.started_at = datetime.now()
    
    state.hex_board = create_hex_board()
    setup_board(state)


def setup_board(state):
    state.board = {}
    hex_board = state.hex_board
    
    side_to_color = {
        1: CheckersPlayer.WHITE,
        2: CheckersPlayer.RED,
        3: CheckersPlayer.BLACK
    }
    
    for side in [1, 2, 3]:
        color = side_to_color[side]
        side_cells = hex_board.side_cells[side]
        
        for i, cell_id in enumerate(side_cells):
            if i < 12:
                state.board[cell_id] = CheckersPiece(color)
    
    for player in state.players:
        player.pieces_count = state.count_pieces(player.color)
        player.kings_count = 0


def is_valid_position(state, cell_id):
    if state.hex_board:
        return state.hex_board.is_valid_cell(cell_id)
    return False


def get_player_side(player_color):
    if player_color == CheckersPlayer.WHITE:
        return 1
    elif player_color == CheckersPlayer.RED:
        return 2
    else:
        return 3


def get_valid_moves(state, from_cell_id):
    if from_cell_id not in state.board:
        return []
    
    piece = state.board[from_cell_id]
    current_player = state.get_current_player()
    
    if not current_player or piece.player != current_player.color:
        return []
    
    if piece.is_king:
        return []
    
    hex_board = state.hex_board
    player_side = get_player_side(piece.player)
    moves = []
    
    neighbors = hex_board.get_neighbors(from_cell_id)
    
    for neighbor_id in neighbors:
        if neighbor_id not in state.board:
            neighbor_side = hex_board.get_side(neighbor_id)
            if neighbor_side != player_side:
                moves.append(neighbor_id)
        else:
            neighbor_piece = state.board[neighbor_id]
            if neighbor_piece.player != piece.player:
                jump_neighbors = hex_board.get_neighbors(neighbor_id)
                for jump_id in jump_neighbors:
                    if (jump_id not in state.board and 
                        jump_id != from_cell_id and
                        hex_board.get_side(jump_id) != player_side):
                        moves.append(jump_id)
    
    return moves


def has_valid_moves(state, player_color):
    for cell_id, piece in state.board.items():
        if piece.player == player_color and not piece.is_king:
            moves = get_valid_moves(state, cell_id)
            if moves:
                return True
    return False


def check_game_end(state):
    blocked_count = 0
    for player in state.players:
        if player.pieces_count > 0:
            if not has_valid_moves(state, player.color):
                player.is_blocked = True
                blocked_count += 1
            else:
                player.is_blocked = False
    
    if blocked_count >= 2:
        determine_winner_by_kings(state)
        return True
    
    return False


def determine_winner_by_kings(state):
    best_players = []
    max_kings = -1
    
    for player in state.players:
        if player.pieces_count > 0:
            player.kings_count = state.count_kings(player.color)
            if player.kings_count > max_kings:
                max_kings = player.kings_count
                best_players = [player]
            elif player.kings_count == max_kings:
                best_players.append(player)
    
    if len(best_players) == 1:
        state.winner_id = best_players[0].bot_id
    elif len(best_players) > 1:
        max_regular = -1
        final_winners = []
        
        for player in best_players:
            regular = state.count_regular_pieces(player.color)
            if regular > max_regular:
                max_regular = regular
                final_winners = [player]
            elif regular == max_regular:
                final_winners.append(player)
        
        if len(final_winners) == 1:
            state.winner_id = final_winners[0].bot_id
        else:
            state.winner_id = None


def process_checkers_move(state, bot_id, from_cell_id, to_cell_id):
    if state.phase != CheckersPhase.PLAYING:
        raise GameStateException("Not in playing phase")
    
    current_player = state.get_current_player()
    if not current_player or current_player.bot_id != bot_id:
        raise InvalidMoveException("Not your turn")
    
    if current_player.is_blocked:
        raise InvalidMoveException("Player is blocked")
    
    if from_cell_id not in state.board:
        raise InvalidMoveException("No piece at from position")
    
    piece = state.board[from_cell_id]
    if piece.player != current_player.color:
        raise InvalidMoveException("Not your piece")
    
    if piece.is_king:
        raise InvalidMoveException("Kings cannot move")
    
    valid_moves = get_valid_moves(state, from_cell_id)
    if to_cell_id not in valid_moves:
        raise InvalidMoveException("Invalid move")
    
    hex_board = state.hex_board
    player_side = get_player_side(piece.player)
    opposite_side = hex_board.get_opposite_side(player_side)
    
    was_capture = False
    captured_cell_id = None
    
    neighbors = hex_board.get_neighbors(from_cell_id)
    if to_cell_id in neighbors:
        for neighbor_id in neighbors:
            if neighbor_id == to_cell_id:
                continue
            if neighbor_id in state.board:
                neighbor_piece = state.board[neighbor_id]
                if neighbor_piece.player != piece.player:
                    jump_neighbors = hex_board.get_neighbors(neighbor_id)
                    if to_cell_id in jump_neighbors:
                        was_capture = True
                        captured_cell_id = neighbor_id
                        break
    
    if not piece.is_king:
        to_side = hex_board.get_side(to_cell_id)
        should_become_king = (to_side == opposite_side)
        
        if should_become_king:
            piece.is_king = True
            state.board[to_cell_id] = piece
            del state.board[from_cell_id]
            current_player.kings_count = state.count_kings(current_player.color)
        else:
            state.board[to_cell_id] = piece
            del state.board[from_cell_id]
    else:
        state.board[to_cell_id] = piece
        del state.board[from_cell_id]
    
    if was_capture and captured_cell_id:
        captured_piece = state.board[captured_cell_id]
        del state.board[captured_cell_id]
        
        for player in state.players:
            if player.color == captured_piece.player:
                player.pieces_count = state.count_pieces(player.color)
                player.kings_count = state.count_kings(player.color)
    
    current_player.pieces_count = state.count_pieces(current_player.color)
    
    state.move_history.append({
        "bot_id": bot_id,
        "from": from_cell_id,
        "to": to_cell_id,
        "timestamp": datetime.now().isoformat()
    })
    
    if check_game_end(state):
        state.phase = CheckersPhase.FINISHED
        state.finished_at = datetime.now()
        return
    
    state.current_player_index = (state.current_player_index + 1) % 3
    attempts = 0
    while attempts < 3:
        next_player = state.players[state.current_player_index]
        if next_player.pieces_count > 0 and not next_player.is_blocked:
            break
        state.current_player_index = (state.current_player_index + 1) % 3
        attempts += 1
