from datetime import datetime
from ..exceptions import InvalidMoveException, GameStateException
from .checkers_models import (
    CheckersGameState,
    CheckersPhase,
    CheckersPlayer,
    CheckersPiece,
    CheckersPlayerState,
)
from .hex_board import create_hex_board


def start_checkers_game(state, player_ids):
    if state.phase != CheckersPhase.WAITING:
        raise GameStateException("Game already started")
    if len(player_ids) != 3:
        raise GameStateException("Need exactly 3 players")
    colors = [CheckersPlayer.WHITE, CheckersPlayer.RED, CheckersPlayer.BLACK]
    state.players = [
        CheckersPlayerState(bot_id=pid, color=colors[i])
        for i, pid in enumerate(player_ids)
    ]
    state.current_player_index = 0
    state.phase = CheckersPhase.PLAYING
    state.started_at = datetime.now()
    state.hex_board = create_hex_board()
    setup_board(state)


def setup_board(state):
    state.board = {}
    hex_board = state.hex_board
    side_to_color = {1: CheckersPlayer.WHITE, 2: CheckersPlayer.RED, 3: CheckersPlayer.BLACK}
    for side in [1, 2, 3]:
        color = side_to_color[side]
        for cell_id in hex_board.side_cells[side]:
            state.board[cell_id] = CheckersPiece(color)
    for player in state.players:
        player.pieces_count = state.count_pieces(player.color)
        player.kings_count = state.count_kings(player.color)


def is_valid_position(state, cell_id):
    return bool(state.hex_board and state.hex_board.is_valid_cell(cell_id))


def get_player_side(player_color):
    if player_color == CheckersPlayer.WHITE:
        return 1
    if player_color == CheckersPlayer.RED:
        return 2
    return 3


def _simple_moves(state, from_cell_id, piece, player_side):
    hex_board = state.hex_board
    moves = []
    for neighbor_id in hex_board.get_forward_neighbors(from_cell_id, player_side):
        if neighbor_id not in state.board:
            moves.append(neighbor_id)
    return moves


def _simple_captures(state, from_cell_id, piece, player_side):
    hex_board = state.hex_board
    captures = []
    dist = hex_board.distance_by_side[player_side]
    from_d = dist.get(from_cell_id, 999)
    for neighbor_id in hex_board.get_neighbors(from_cell_id):
        if neighbor_id not in state.board:
            continue
        if state.board[neighbor_id].player == piece.player:
            continue
        for jump_id in hex_board.get_neighbors(neighbor_id):
            if jump_id == from_cell_id or jump_id in state.board:
                continue
            if dist.get(jump_id, 0) <= from_d:
                continue
            captures.append(jump_id)
    return captures


def _queen_quiet_moves(state, from_cell_id, piece):
    hex_board = state.hex_board
    moves = []
    for ray in hex_board.get_rays(from_cell_id):
        for cell_id in ray:
            if cell_id in state.board:
                break
            moves.append(cell_id)
    return moves


def _queen_captures(state, from_cell_id, piece):
    hex_board = state.hex_board
    captures = []
    for ray in hex_board.get_rays(from_cell_id):
        first_enemy = None
        first_enemy_idx = None
        for i, cell_id in enumerate(ray):
            if cell_id not in state.board:
                if first_enemy is not None:
                    captures.append(cell_id)
                continue
            p = state.board[cell_id]
            if p.player == piece.player:
                break
            if first_enemy is None:
                first_enemy = cell_id
                first_enemy_idx = i
            else:
                break
        if first_enemy is not None:
            for j in range(first_enemy_idx + 1, len(ray)):
                cell_id = ray[j]
                if cell_id in state.board:
                    break
                captures.append(cell_id)
    return captures


def get_valid_moves(state, from_cell_id):
    if from_cell_id not in state.board:
        return []
    piece = state.board[from_cell_id]
    current = state.get_current_player()
    if not current or piece.player != current.color:
        return []
    hex_board = state.hex_board
    player_side = get_player_side(piece.player)
    all_captures = []
    all_quiet = []
    if piece.is_king:
        all_captures = _queen_captures(state, from_cell_id, piece)
        all_quiet = _queen_quiet_moves(state, from_cell_id, piece)
    else:
        all_captures = _simple_captures(state, from_cell_id, piece, player_side)
        all_quiet = _simple_moves(state, from_cell_id, piece, player_side)
    any_capture = False
    for cid, p in state.board.items():
        if p.player != current.color:
            continue
        if p.is_king:
            caps = _queen_captures(state, cid, p)
        else:
            caps = _simple_captures(state, cid, p, get_player_side(p.player))
        if caps:
            any_capture = True
            break
    if any_capture:
        return list(dict.fromkeys(all_captures))
    return list(dict.fromkeys(all_captures + all_quiet))


def has_valid_moves(state, player_color):
    for cell_id, piece in state.board.items():
        if piece.player != player_color:
            continue
        if get_valid_moves(state, cell_id):
            return True
    return False


def _find_captured_between(hex_board, state, from_cell_id, to_cell_id, piece):
    for ray in hex_board.get_rays(from_cell_id):
        if to_cell_id not in ray:
            continue
        captured = []
        for cid in ray:
            if cid == to_cell_id:
                break
            if cid in state.board and state.board[cid].player != piece.player:
                captured.append(cid)
        return captured
    return []


def _find_jumped_simple(hex_board, state, from_cell_id, to_cell_id, piece):
    for n in hex_board.get_neighbors(from_cell_id):
        if to_cell_id not in hex_board.get_neighbors(n):
            continue
        if n in state.board and state.board[n].player != piece.player:
            return n
    return None


def check_game_end(state):
    for player in state.players:
        if player.pieces_count > 0:
            player.is_blocked = not has_valid_moves(state, player.color)
        else:
            player.is_blocked = True
    active = [p for p in state.players if p.pieces_count > 0 and not p.is_blocked]
    if not active:
        determine_winner(state)
        return True
    still_has_moves = any(has_valid_moves(state, p.color) for p in state.players if p.pieces_count > 0)
    if not still_has_moves:
        determine_winner(state)
        return True
    return False


def determine_winner(state):
    candidates = [p for p in state.players if p.pieces_count > 0]
    if not candidates:
        state.winner_id = None
        return
    for p in candidates:
        p.kings_count = state.count_kings(p.color)
    best = []
    max_kings = max(p.kings_count for p in candidates)
    for p in candidates:
        if p.kings_count == max_kings:
            best.append(p)
    if len(best) == 1:
        state.winner_id = best[0].bot_id
        return
    max_regular = max(state.count_regular_pieces(p.color) for p in best)
    final = [p for p in best if state.count_regular_pieces(p.color) == max_regular]
    state.winner_id = final[0].bot_id if len(final) == 1 else None


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
    valid_moves = get_valid_moves(state, from_cell_id)
    if to_cell_id not in valid_moves:
        raise InvalidMoveException("Invalid move")
    hex_board = state.hex_board
    player_side = get_player_side(piece.player)
    captured_cells = []
    if piece.is_king:
        captured_cells = _find_captured_between(hex_board, state, from_cell_id, to_cell_id, piece)
    else:
        jumped = _find_jumped_simple(
            hex_board, state, from_cell_id, to_cell_id, piece
        )
        if jumped is not None:
            captured_cells = [jumped]
    state.board[to_cell_id] = piece
    del state.board[from_cell_id]
    for cid in captured_cells:
        if cid in state.board:
            captured_piece = state.board[cid]
            del state.board[cid]
            for p in state.players:
                if p.color == captured_piece.player:
                    p.pieces_count = state.count_pieces(p.color)
                    p.kings_count = state.count_kings(p.color)
    if not piece.is_king and hex_board.is_last_row_for_side(to_cell_id, player_side):
        piece.is_king = True
        current_player.kings_count = state.count_kings(current_player.color)
    current_player.pieces_count = state.count_pieces(current_player.color)
    state.move_history.append({
        "bot_id": bot_id,
        "from": from_cell_id,
        "to": to_cell_id,
        "timestamp": datetime.now().isoformat(),
    })
    if check_game_end(state):
        state.phase = CheckersPhase.FINISHED
        state.finished_at = datetime.now()
        return
    must_continue = False
    if captured_cells:
        if piece.is_king:
            must_continue = bool(_queen_captures(state, to_cell_id, piece))
        else:
            must_continue = bool(_simple_captures(state, to_cell_id, piece, player_side))
    if not must_continue:
        state.current_player_index = (state.current_player_index + 1) % 3
        for _ in range(3):
            next_player = state.players[state.current_player_index]
            if next_player.pieces_count > 0 and not next_player.is_blocked:
                break
            state.current_player_index = (state.current_player_index + 1) % 3
