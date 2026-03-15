from datetime import datetime
from ..exceptions import InvalidMoveException, GameStateException
from .checkers_models import (
    CheckersGameState,
    CheckersPhase,
    CheckersPlayer,
    CheckersPiece,
    CheckersPlayerState,
)
from .board_graph import build_lallement_graph


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
    state.hex_board = build_lallement_graph()
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


def _king_moves(state, from_cell_id):
    hex_board = state.hex_board
    return [n for n in hex_board.get_neighbors(from_cell_id) if n not in state.board]


def _simple_captures(state, from_cell_id, piece, player_side):
    hex_board = state.hex_board
    captures = []
    is_king_safe = getattr(hex_board, "is_king_safe_cell", None)
    for neighbor_id in hex_board.get_neighbors(from_cell_id):
        if neighbor_id not in state.board:
            continue
        if state.board[neighbor_id].player == piece.player:
            continue
        opp = state.board[neighbor_id]
        if opp.is_king and is_king_safe and is_king_safe(neighbor_id, get_player_side(opp.player)):
            continue
        landings = getattr(hex_board, "get_capture_landings", None)
        if landings:
            allowed = landings(from_cell_id, neighbor_id)
        else:
            allowed = [j for j in hex_board.get_neighbors(neighbor_id) if j != from_cell_id]
        for jump_id in allowed:
            if jump_id in state.board:
                continue
            captures.append(jump_id)
    return captures


def get_valid_moves(state, from_cell_id, skip_turn_check=False):
    if from_cell_id not in state.board:
        return []
    piece = state.board[from_cell_id]
    current = state.get_current_player()
    if not skip_turn_check and (not current or piece.player != current.color):
        return []
    hex_board = state.hex_board
    player_side = get_player_side(piece.player)
    if piece.is_king and getattr(hex_board, "is_king_safe_cell", None) and hex_board.is_king_safe_cell(from_cell_id, player_side):
        return []
    all_captures = _simple_captures(state, from_cell_id, piece, player_side)
    if piece.is_king:
        all_quiet = _king_moves(state, from_cell_id)
    else:
        all_quiet = _simple_moves(state, from_cell_id, piece, player_side)
    check_color = piece.player if skip_turn_check else (current.color if current else piece.player)
    any_capture = False
    for cid, p in state.board.items():
        if p.player != check_color:
            continue
        if _simple_captures(state, cid, p, get_player_side(p.player)):
            any_capture = True
            break
    if any_capture:
        return list(dict.fromkeys(all_captures))
    return list(dict.fromkeys(all_captures + all_quiet))


def has_valid_moves(state, player_color):
    for cell_id, piece in state.board.items():
        if piece.player != player_color:
            continue
        if get_valid_moves(state, cell_id, skip_turn_check=True):
            return True
    return False


def _find_jumped_simple(hex_board, state, from_cell_id, to_cell_id, piece):
    landings = getattr(hex_board, "get_capture_landings", None)
    for n in hex_board.get_neighbors(from_cell_id):
        if n not in state.board or state.board[n].player == piece.player:
            continue
        if landings:
            if to_cell_id not in landings(from_cell_id, n):
                continue
        else:
            if to_cell_id not in hex_board.get_neighbors(n):
                continue
        return n
    return None


def check_game_end(state):
    for player in state.players:
        player.pieces_count = state.count_pieces(player.color)
        if player.pieces_count > 0:
            player.is_blocked = not has_valid_moves(state, player.color)
        else:
            player.is_blocked = True
    candidates = [p for p in state.players if p.pieces_count > 0]
    if len(candidates) == 1:
        state.winner_id = candidates[0].bot_id
        return True
    if all(state.count_regular_pieces(p.color) == 0 for p in state.players):
        determine_winner(state)
        return True
    active = [p for p in state.players if p.pieces_count > 0 and not p.is_blocked]
    if not active:
        determine_winner(state)
        return True
    still_has_moves = any(has_valid_moves(state, p.color) for p in state.players if p.pieces_count > 0)
    if not still_has_moves:
        determine_winner(state)
        return True
    return False


TIEBREAKER_ORDER = (CheckersPlayer.BLACK, CheckersPlayer.WHITE, CheckersPlayer.RED)


def determine_winner(state):
    candidates = [p for p in state.players if p.pieces_count > 0]
    if not candidates:
        state.winner_id = None
        return
    for p in candidates:
        p.kings_count = state.count_kings(p.color)
    by_kings = max(p.kings_count for p in candidates)
    best = [p for p in candidates if p.kings_count == by_kings]
    if len(best) == 1:
        state.winner_id = best[0].bot_id
        return
    by_simple = max(state.count_regular_pieces(p.color) for p in best)
    best = [p for p in best if state.count_regular_pieces(p.color) == by_simple]
    if len(best) == 1:
        state.winner_id = best[0].bot_id
        return
    for color in TIEBREAKER_ORDER:
        for p in best:
            if p.color == color:
                state.winner_id = p.bot_id
                return
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
    valid_moves = get_valid_moves(state, from_cell_id)
    if to_cell_id not in valid_moves:
        raise InvalidMoveException("Invalid move")
    hex_board = state.hex_board
    player_side = get_player_side(piece.player)
    jumped = _find_jumped_simple(hex_board, state, from_cell_id, to_cell_id, piece)
    captured_cells = [jumped] if jumped is not None else []
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
    if not piece.is_king and hex_board.is_promotion_cell_for_side(to_cell_id, player_side):
        piece.is_king = True
        current_player.kings_count = state.count_kings(current_player.color)
    current_player.pieces_count = state.count_pieces(current_player.color)
    state.move_history.append({
        "bot_id": bot_id,
        "from": from_cell_id,
        "to": to_cell_id,
        "captured": captured_cells if captured_cells else None,
        "timestamp": datetime.now().isoformat(),
    })
    if check_game_end(state):
        state.phase = CheckersPhase.FINISHED
        state.finished_at = datetime.now()
        return
    must_continue = bool(
        captured_cells
        and not piece.is_king
        and _simple_captures(state, to_cell_id, piece, player_side)
    )
    if not must_continue:
        state.current_player_index = (state.current_player_index + 1) % 3
        for _ in range(3):
            next_player = state.players[state.current_player_index]
            if next_player.pieces_count > 0 and not next_player.is_blocked:
                break
            state.current_player_index = (state.current_player_index + 1) % 3
