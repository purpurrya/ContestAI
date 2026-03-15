#!/usr/bin/env python3
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine.checkers import (
    CheckersGameState,
    start_checkers_game,
    process_checkers_move,
    get_valid_moves,
)
from game_engine.checkers import checkers_engine
from game_engine.checkers.board_graph import build_manual_graph
from game_engine.checkers.checkers_models import CheckersPiece, CheckersPlayer

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


def make_state(match_id="test", seed=None):
    state = CheckersGameState(match_id=match_id)
    start_checkers_game(state, ["bot1", "bot2", "bot3"])
    checkers_engine.get_player_side = lambda c: MANUAL_COLOR_TO_SIDE.get(c, 1)
    state.hex_board = build_manual_graph()
    setup_board_manual(state)
    if seed is not None:
        random.seed(seed)
    return state


def to_viz_move(m):
    out = {"from": m["from"], "to": m["to"]}
    if m.get("captured"):
        out["captured"] = m["captured"]
    return out


def _is_capture_move(state, from_cell, to_cell):
    for n in state.hex_board.get_neighbors(from_cell):
        if n in state.board and state.board[n].player != state.board[from_cell].player:
            landings = state.hex_board.get_capture_landings(from_cell, n)
            if to_cell in landings:
                return True
    return False


def run_full_game(state, max_moves=3000):
    for _ in range(max_moves):
        if state.phase.value == "finished":
            return True
        current = state.get_current_player()
        if not current:
            return False
        candidates = []
        for cid, piece in state.board.items():
            if piece.player != current.color:
                continue
            moves = get_valid_moves(state, cid)
            if not moves:
                continue
            captures = [m for m in moves if _is_capture_move(state, cid, m)]
            candidates.append((cid, captures if captures else moves))
        if not candidates:
            return False
        cid, moves = random.choice(candidates)
        to_cell = random.choice(moves)
        process_checkers_move(state, current.bot_id, cid, to_cell)
    return False


def build_export(state, initial_board):
    out = {
        "match_id": state.match_id,
        "phase": state.phase.value,
        "initial_board": {str(k): v.to_dict() for k, v in initial_board.items()},
        "move_history": [to_viz_move(m) for m in state.move_history],
        "board": {str(k): v.to_dict() for k, v in state.board.items()},
    }
    if state.winner_id is not None:
        out["winner_id"] = state.winner_id
    return out


def main():
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "checkers_viz", "test_games")
    os.makedirs(base, exist_ok=True)

    num_games = 3
    max_attempts_per_slot = 50
    max_moves = 3000

    for i in range(1, num_games + 1):
        name = "full_game_{}".format(i)
        path = os.path.join(base, name + ".json")
        for attempt in range(max_attempts_per_slot):
            state = make_state(name, seed=(i * 1000 + attempt))
            initial_board_dict = {str(k): v.to_dict() for k, v in state.board.items()}
            finished = run_full_game(state, max_moves=max_moves)
            if finished and state.winner_id:
                out = build_export(state, {int(k): CheckersPiece.from_dict(p) for k, p in initial_board_dict.items()})
                out["match_id"] = name
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(out, f, ensure_ascii=False, indent=2)
                print("{}: {} ходов, winner={}".format(name + ".json", len(state.move_history), state.winner_id))
                break
        else:
            state = make_state(name, seed=i * 999)
            initial_board_dict = {str(k): v.to_dict() for k, v in state.board.items()}
            run_full_game(state, max_moves=max_moves)
            out = build_export(state, {int(k): CheckersPiece.from_dict(p) for k, p in initial_board_dict.items()})
            out["match_id"] = name
            if state.winner_id:
                out["winner_id"] = state.winner_id
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print("{}: сохранено без победы ({} ходов)".format(name + ".json", len(state.move_history)))


if __name__ == "__main__":
    main()
