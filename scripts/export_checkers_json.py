#!/usr/bin/env python3
import json
import sys

sys.path.insert(0, '.')

from game_engine.checkers import (
    CheckersGameState,
    start_checkers_game,
    process_checkers_move,
    get_valid_moves,
)
from game_engine.checkers import checkers_engine
from game_engine.checkers.board_graph import build_lallement_graph, build_manual_graph
from game_engine.checkers.checkers_models import CheckersPiece, CheckersPlayer

USE_MANUAL_GRAPH = True

MANUAL_SIDE_TO_COLOR = {1: CheckersPlayer.RED, 2: CheckersPlayer.BLACK, 3: CheckersPlayer.WHITE}
MANUAL_COLOR_TO_SIDE = {CheckersPlayer.RED: 1, CheckersPlayer.BLACK: 2, CheckersPlayer.WHITE: 3}


def setup_board_manual(state):
    state.board = {}
    for side in [1, 2, 3]:
        color = MANUAL_SIDE_TO_COLOR[side]
        for cell_id in state.hex_board.side_cells[side]:
            state.board[cell_id] = CheckersPiece(color)
    for player in state.players:
        player.pieces_count = state.count_pieces(player.color)
        player.kings_count = state.count_kings(player.color)


def main():
    state = CheckersGameState(match_id="export")
    start_checkers_game(state, ["bot1", "bot2", "bot3"])
    if USE_MANUAL_GRAPH:
        import game_engine.checkers.checkers_engine as eng
        eng.get_player_side = lambda c: MANUAL_COLOR_TO_SIDE.get(c, 1)
        state.hex_board = build_manual_graph()
        setup_board_manual(state)

    initial_board = {str(k): v.to_dict() for k, v in state.board.items()}

    for _ in range(8):
        current = state.get_current_player()
        if not current:
            break
        moved = False
        for cid, piece in list(state.board.items()):
            if piece.player != current.color or piece.is_king:
                continue
            moves = get_valid_moves(state, cid)
            if moves:
                process_checkers_move(state, current.bot_id, cid, moves[0])
                moved = True
                break
        if not moved:
            break

    out = state.to_dict()
    out["initial_board"] = initial_board
    h = state.hex_board
    if getattr(h, "get_cell_positions", None):
        out["cell_positions"] = {str(k): list(v) for k, v in h.get_cell_positions().items()}
    for key in ("started_at", "finished_at"):
        if key in out and out[key]:
            out[key] = out[key][:19].replace("T", " ")

    json_str = json.dumps(out, ensure_ascii=False, indent=2)
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as f:
            f.write(json_str)
        print("Записано:", sys.argv[1])
    else:
        print(json_str)


if __name__ == "__main__":
    main()
