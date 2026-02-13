from typing import Dict, List, Set, Tuple, Optional


def _rc_to_id(r: int, c: int) -> int:
    return r * (r + 1) // 2 + c


def _id_to_rc(cell_id: int) -> Tuple[int, int]:
    r = 0
    while (r + 1) * (r + 2) // 2 <= cell_id:
        r += 1
    c = cell_id - r * (r + 1) // 2
    return (r, c)


class HexCell:
    def __init__(self, cell_id: int, r: int, c: int):
        self.cell_id = cell_id
        self.r = r
        self.c = c
        self.neighbors: List[int] = []
        self.rays: List[List[int]] = []

    def add_neighbor(self, neighbor_id: int):
        if neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)


class HexagonalBoard:
    def __init__(self):
        self.cells: Dict[int, HexCell] = {}
        self.side_cells: Dict[int, List[int]] = {1: [], 2: [], 3: []}
        self.last_row_by_side: Dict[int, Set[int]] = {1: set(), 2: set(), 3: set()}
        self.forward_by_side: Dict[int, Dict[int, List[int]]] = {1: {}, 2: {}, 3: {}}
        self.distance_by_side: Dict[int, Dict[int, int]] = {1: {}, 2: {}, 3: {}}
        self.build_board()

    def build_board(self):
        for r in range(12):
            for c in range(r + 1):
                cell_id = _rc_to_id(r, c)
                self.cells[cell_id] = HexCell(cell_id, r, c)

        for cell_id, cell in self.cells.items():
            r, c = cell.r, cell.c
            for dr, dc in [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nc <= nr <= 11:
                    self.cells[cell_id].add_neighbor(_rc_to_id(nr, nc))

        for side in [1, 2, 3]:
            self._fill_side_cells(side)
            self._fill_distances_and_last_row(side)
            self._fill_forward(side)

        for cell in self.cells.values():
            self._build_rays(cell)

    def _fill_side_cells(self, side: int):
        if side == 1:
            self.side_cells[1] = [_rc_to_id(r, 0) for r in range(11)]
        elif side == 2:
            self.side_cells[2] = [_rc_to_id(r, r) for r in range(1, 12)]
        else:
            self.side_cells[3] = [_rc_to_id(11, c) for c in range(11)]

    def _fill_distances_and_last_row(self, side: int):
        start = set(self.side_cells[side])
        dist: Dict[int, int] = {cid: 0 for cid in start}
        q = list(start)
        qi = 0
        while qi < len(q):
            cid = q[qi]
            qi += 1
            d = dist[cid]
            for n in self.cells[cid].neighbors:
                if n not in dist:
                    dist[n] = d + 1
                    q.append(n)
        self.distance_by_side[side] = dist
        self.last_row_by_side[side] = {cid for cid, d in dist.items() if d == 7}

    def _fill_forward(self, side: int):
        dist = self.distance_by_side[side]
        last = self.last_row_by_side[side]
        for cell_id, cell in self.cells.items():
            if cell_id in last:
                self.forward_by_side[side][cell_id] = []
                continue
            my_d = dist.get(cell_id, 999)
            fwd = [n for n in cell.neighbors if dist.get(n, 0) > my_d]
            self.forward_by_side[side][cell_id] = fwd

    def _build_rays(self, cell: HexCell):
        r, c = cell.r, cell.c
        directions = [
            (1, 0), (1, 1), (0, 1), (0, -1), (-1, 0), (-1, -1)
        ]
        for dr, dc in directions:
            ray = []
            nr, nc = r + dr, c + dc
            while 0 <= nc <= nr <= 11:
                ray.append(_rc_to_id(nr, nc))
                nr, nc = nr + dr, nc + dc
            if ray:
                cell.rays.append(ray)

    def get_neighbors(self, cell_id: int) -> List[int]:
        if cell_id not in self.cells:
            return []
        return self.cells[cell_id].neighbors.copy()

    def get_rays(self, cell_id: int) -> List[List[int]]:
        if cell_id not in self.cells:
            return []
        return [list(ray) for ray in self.cells[cell_id].rays]

    def is_valid_cell(self, cell_id: int) -> bool:
        return cell_id in self.cells

    def get_side(self, cell_id: int) -> Optional[int]:
        if cell_id not in self.cells:
            return None
        r, c = self.cells[cell_id].r, self.cells[cell_id].c
        if c == 0:
            return 1
        if r == c:
            return 2
        if r == 11:
            return 3
        return None

    def is_last_row_for_side(self, cell_id: int, side: int) -> bool:
        return cell_id in self.last_row_by_side.get(side, set())

    def get_forward_neighbors(self, cell_id: int, player_side: int) -> List[int]:
        return self.forward_by_side.get(player_side, {}).get(cell_id, []).copy()

    def get_opposite_side(self, side: int) -> int:
        if side == 1:
            return 3
        if side == 2:
            return 1
        return 2


def create_hex_board() -> HexagonalBoard:
    return HexagonalBoard()
