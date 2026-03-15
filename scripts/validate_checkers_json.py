#!/usr/bin/env python3
import json
import sys

sys.path.insert(0, '.')

from game_engine.checkers.board_graph import BLACK_CELLS, HAND_PROMOTION_BY_SIDE

PROMO = {side: set(cells) for side, cells in HAND_PROMOTION_BY_SIDE.items()}
COLOR_TO_SIDE = {"red": 1, "black": 2, "white": 3}


def norm_board(board_dict):
    out = {}
    for k, v in (board_dict or {}).items():
        cid = int(k) if isinstance(k, str) else k
        out[cid] = v
    return out

def apply_move(board, move):
    board = dict(board)
    from_id = move["from"] if isinstance(move["from"], int) else int(move["from"])
    to_id = move["to"] if isinstance(move["to"], int) else int(move["to"])
    if from_id not in board:
        raise ValueError("Нет шашки на клетке from={}".format(from_id))
    piece = dict(board.pop(from_id))
    side = COLOR_TO_SIDE.get(piece.get("player"))
    if side and to_id in PROMO.get(side, set()) and not piece.get("is_king"):
        piece["is_king"] = True
    board[to_id] = piece
    captured = move.get("captured")
    if captured is not None:
        cap_list = captured if isinstance(captured, list) else [captured]
        for cid in cap_list:
            cid = int(cid) if not isinstance(cid, int) else cid
            board.pop(cid, None)
    return board

def validate_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    errors = []
    initial = norm_board(data.get("initial_board") or data.get("board"))
    if not initial:
        return ["Нет initial_board и board"]
    history = data.get("move_history") or []

    black_set = set(BLACK_CELLS)
    for cid in initial:
        if cid not in black_set:
            errors.append("Клетка {} не чёрная (initial)".format(cid))

    board = dict(initial)
    initial_count = {c: sum(1 for p in board.values() if p.get("player") == c) for c in ("red", "black", "white")}
    captured_count = {"red": 0, "black": 0, "white": 0}

    for i, move in enumerate(history):
        from_id = move.get("from")
        to_id = move.get("to")
        if from_id is None or to_id is None:
            errors.append("Ход {}: нет from или to".format(i))
            break
        from_id = int(from_id) if not isinstance(from_id, int) else from_id
        to_id = int(to_id) if not isinstance(to_id, int) else to_id
        if from_id not in black_set or to_id not in black_set:
            errors.append("Ход {}: from={} или to={} не чёрная клетка".format(i, from_id, to_id))
        if from_id not in board:
            errors.append("Ход {}: на from={} нет шашки".format(i, from_id))
        cap_list = move.get("captured")
        cap_list = list(cap_list) if isinstance(cap_list, list) else [cap_list] if cap_list is not None else []
        if to_id in board and to_id not in cap_list:
            errors.append("Ход {}: to={} уже занята".format(i, to_id))
        try:
            board = apply_move(board, move)
        except Exception as e:
            errors.append("Ход {}: {}".format(i, e))
            break
        cap = move.get("captured")
        if cap is not None:
            cap_list = cap if isinstance(cap, list) else [cap]
            for cid in cap_list:
                pass
        for cid in (move.get("captured") or []):
            cid = int(cid) if not isinstance(cid, int) else cid
            pass

    final_count = {c: sum(1 for p in board.values() if p.get("player") == c) for c in ("red", "black", "white")}
    for color in ("red", "black", "white"):
        if final_count[color] > initial_count[color]:
            errors.append("После всех ходов у {} больше шашек (было {}, стало {})".format(
                color, initial_count[color], final_count[color]))

    if history and "board" in data:
        expected = norm_board(data["board"])
        for cid, piece in board.items():
            if cid not in expected or expected[cid].get("player") != piece.get("player") or expected[cid].get("is_king") != piece.get("is_king"):
                errors.append("После replay на клетке {} состояние не совпадает с board в JSON".format(cid))
        for cid in expected:
            if cid not in board:
                errors.append("В board в JSON есть клетка {}, после replay её нет".format(cid))

    return errors

def main():
    paths = sys.argv[1:] or ["checkers_viz/test_games/test_initial.json", "checkers_viz/test_games/test_few_moves.json"]
    for path in paths:
        try:
            errs = validate_file(path)
            if errs:
                print("{}: ОШИБКИ:".format(path))
                for e in errs:
                    print("  -", e)
            else:
                print("{}: OK".format(path))
        except FileNotFoundError:
            print("{}: файл не найден".format(path))
        except json.JSONDecodeError as e:
            print("{}: ошибка JSON: {}".format(path, e))

if __name__ == "__main__":
    main()
