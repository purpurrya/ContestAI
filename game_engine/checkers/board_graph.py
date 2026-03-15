from typing import Any, Dict, List, Optional, Set, Tuple

from .capture_directions import (
    CAPTURE_LINE_PAIRS,
    build_capture_landings as _build_capture_landings_from_pairs,
)


class CheckersGraph:
    def __init__(
        self,
        neighbors: Dict[int, List[int]],
        side_cells: Dict[int, List[int]],
        promotion_by_side: Optional[Dict[int, List[int]]] = None,
        capture_landings: Optional[Dict[Tuple[int, int], List[int]]] = None,
        king_safe_by_side: Optional[Dict[int, Set[int]]] = None,
    ):
        self._neighbors = {v: list(ns) for v, ns in neighbors.items()}
        self._side_cells = {s: list(cells) for s, cells in side_cells.items()}
        self._promotion_by_side: Dict[int, Set[int]] = {1: set(), 2: set(), 3: set()}
        if promotion_by_side:
            for side, cells in promotion_by_side.items():
                self._promotion_by_side[side] = set(cells)
        else:
            for side in [1, 2, 3]:
                for o in [1, 2, 3]:
                    if o != side:
                        self._promotion_by_side[side].update(self._side_cells.get(o, []))
        self._capture_landings = dict(capture_landings) if capture_landings else {}
        self._king_safe_by_side = dict(king_safe_by_side) if king_safe_by_side else {}
        self._distance_by_side: Dict[int, Dict[int, int]] = {1: {}, 2: {}, 3: {}}
        self._forward_by_side: Dict[int, Dict[int, List[int]]] = {1: {}, 2: {}, 3: {}}

        for side in [1, 2, 3]:
            self._compute_distances(side)
            self._compute_forward(side)

    def _compute_distances(self, side: int) -> None:
        start = set(self._side_cells.get(side, []))
        dist: Dict[int, int] = {v: 0 for v in start}
        q = list(start)
        i = 0
        while i < len(q):
            v = q[i]
            i += 1
            d = dist[v]
            for u in self._neighbors.get(v, []):
                if u not in dist:
                    dist[u] = d + 1
                    q.append(u)
        self._distance_by_side[side] = dist

    def _compute_forward(self, side: int) -> None:
        dist = self._distance_by_side[side]
        for v, nb in self._neighbors.items():
            d_v = dist.get(v, 999)
            self._forward_by_side[side][v] = [
                u for u in nb if dist.get(u, 0) > d_v
            ]

    def get_neighbors(self, cell_id: int) -> List[int]:
        return self._neighbors.get(cell_id, []).copy()

    def is_valid_cell(self, cell_id: int) -> bool:
        return cell_id in self._neighbors

    def is_promotion_cell_for_side(self, cell_id: int, side: int) -> bool:
        return cell_id in self._promotion_by_side.get(side, set())

    def get_forward_neighbors(self, cell_id: int, player_side: int) -> List[int]:
        return self._forward_by_side.get(player_side, {}).get(cell_id, []).copy()

    def get_capture_landings(self, from_id: int, over_id: int) -> List[int]:
        return self._capture_landings.get((from_id, over_id), []).copy()

    def is_king_safe_cell(self, cell_id: int, player_side: int) -> bool:
        return cell_id in self._king_safe_by_side.get(player_side, set())

    @property
    def side_cells(self) -> Dict[int, List[int]]:
        return self._side_cells

    @property
    def cells(self) -> Dict[int, Any]:
        return {v: {} for v in self._neighbors}


def _rc_to_id(r: int, c: int) -> int:
    return r * (r + 1) // 2 + c


def build_lallement_graph() -> CheckersGraph:
    neighbors: Dict[int, List[int]] = {}
    deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]

    for r in range(12):
        for c in range(r + 1):
            v = _rc_to_id(r, c)
            neighbors[v] = []
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nc <= nr <= 11:
                    neighbors[v].append(_rc_to_id(nr, nc))

    side_cells: Dict[int, List[int]] = {
        1: [_rc_to_id(r, 0) for r in range(12)],
        2: [_rc_to_id(r, r) for r in range(1, 12)] + [_rc_to_id(2, 1)],
        3: [_rc_to_id(11, c) for c in range(1, 11)] + [_rc_to_id(10, 2), _rc_to_id(10, 3)],
    }

    return CheckersGraph(neighbors=neighbors, side_cells=side_cells)


BLACK_CELLS: List[int] = [
    0, 2, 4, 6, 9, 11, 13, 15, 16, 18, 20, 22,
    25, 27, 29, 31,
    32, 34, 36, 38, 41, 43, 45, 47, 48, 50, 52, 54,
    57, 59, 61, 63,
    64, 66, 68, 70, 73, 75, 77, 79, 80, 82, 84, 86,
    89, 91, 93, 95,
]

# Соседи по чёрным клеткам (один ход). В checkers_viz/board-graph.js MOVES — то же для визуализации
HAND_NEIGHBORS: Dict[int, List[int]] = {
    0: [9],
    2: [9, 11],
    4: [11, 13],
    6: [13, 15],
    9: [0, 2, 16, 18],
    11: [2, 4, 18, 20],
    13: [4, 6, 20, 22],
    15: [6, 22],
    16: [9, 25],
    18: [9, 11, 25, 27],
    20: [11, 13, 27, 29],
    22: [13, 15, 29, 31],
    25: [18, 16, 63, 61],
    27: [18, 20, 59, 61, 91],
    29: [20, 22, 89, 91],
    31: [22, 89],
    32: [41],
    34: [41, 43],
    36: [43, 45],
    38: [45, 47],
    41: [32, 34, 48, 50],
    43: [34, 36, 50, 52],
    45: [36, 38, 52, 54],
    47: [38, 54],
    48: [41, 57],
    50: [41, 43, 57, 59],
    52: [43, 45, 59, 61],
    54: [45, 47, 61, 63],
    57: [48, 50, 93, 95],
    59: [27, 50, 52, 91, 93],
    61: [25, 27, 52, 54],
    63: [25, 54],
    64: [73],
    66: [73, 75],
    68: [75, 77],
    70: [77, 79],
    73: [64, 66, 80, 82],
    75: [66, 68, 82, 84],
    77: [68, 70, 84, 86],
    79: [86],
    80: [73, 89],
    82: [73, 75, 89, 91],
    84: [75, 77, 91, 93],
    86: [77, 79, 93, 95],
    89: [29, 31, 80, 82],
    91: [29, 27, 59, 82, 84],
    93: [57, 59, 84, 86],
    95: [57, 86],
}

#начальные положения шашек
HAND_SIDE_CELLS: Dict[int, List[int]] = {
    1: [0, 2, 4, 6, 9, 11, 13, 15, 16, 18, 20, 22],
    2: [32, 34, 36, 38, 41, 43, 45, 47, 48, 50, 52, 54],
    3: [64, 66, 68, 70, 73, 75, 77, 79, 80, 82, 84, 86],
}

#края каждой стороны
HAND_PROMOTION_BY_SIDE: Dict[int, List[int]] = {
    1: [0, 2, 4, 6],
    2: [32, 34, 36, 38],
    3: [64, 66, 68, 70],
}

KING_SAFE_BY_SIDE: Dict[int, Set[int]] = {
    1: set(HAND_PROMOTION_BY_SIDE[2]) | set(HAND_PROMOTION_BY_SIDE[3]),
    2: set(HAND_PROMOTION_BY_SIDE[1]) | set(HAND_PROMOTION_BY_SIDE[3]),
    3: set(HAND_PROMOTION_BY_SIDE[1]) | set(HAND_PROMOTION_BY_SIDE[2]),
}

HAND_CAPTURE_LANDINGS: Dict[Tuple[int, int], List[int]] = _build_capture_landings_from_pairs(
    CAPTURE_LINE_PAIRS
)


def build_manual_graph() -> CheckersGraph:
    if not HAND_NEIGHBORS:
        return build_lallement_graph()
    return CheckersGraph(
        neighbors=HAND_NEIGHBORS,
        side_cells=HAND_SIDE_CELLS,
        promotion_by_side=HAND_PROMOTION_BY_SIDE,
        capture_landings=HAND_CAPTURE_LANDINGS,
        king_safe_by_side=KING_SAFE_BY_SIDE,
    )
