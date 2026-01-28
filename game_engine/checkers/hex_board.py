from typing import Dict, List, Set, Tuple, Optional


class HexCell:
    def __init__(self, cell_id: int, side: int, position: int):
        self.cell_id = cell_id
        self.side = side
        self.position = position
        self.neighbors: List[int] = []
        self.is_center = False
    
    def add_neighbor(self, neighbor_id: int):
        if neighbor_id not in self.neighbors:
            self.neighbors.append(neighbor_id)


class HexagonalBoard:
    def __init__(self):
        self.cells: Dict[int, HexCell] = {}
        self.edges: Dict[Tuple[int, int], bool] = {}
        self.side_cells: Dict[int, List[int]] = {1: [], 2: [], 3: []}
        self.center_cells: Set[int] = set()
        self.build_board()
    
    def build_board(self):
        cell_id = 0
        
        for side in [1, 2, 3]:
            for pos in range(32):
                cell = HexCell(cell_id, side, pos)
                self.cells[cell_id] = cell
                self.side_cells[side].append(cell_id)
                cell_id += 1
        
        self.connect_sides()
        self.mark_center()
    
    def connect_sides(self):
        for side in [1, 2, 3]:
            side_cells = self.side_cells[side]
            
            for i, cell_id in enumerate(side_cells):
                cell = self.cells[cell_id]
                
                if i > 0:
                    prev_cell_id = side_cells[i - 1]
                    cell.add_neighbor(prev_cell_id)
                    self.cells[prev_cell_id].add_neighbor(cell_id)
                    self.edges[(prev_cell_id, cell_id)] = True
                    self.edges[(cell_id, prev_cell_id)] = True
                
                if i < len(side_cells) - 1:
                    next_cell_id = side_cells[i + 1]
                    cell.add_neighbor(next_cell_id)
                    self.cells[next_cell_id].add_neighbor(cell_id)
                    self.edges[(next_cell_id, cell_id)] = True
                    self.edges[(cell_id, next_cell_id)] = True
        
        self.connect_side_to_side(1, 2)
        self.connect_side_to_side(2, 3)
        self.connect_side_to_side(3, 1)
    
    def connect_side_to_side(self, side1: int, side2: int):
        cells1 = self.side_cells[side1]
        cells2 = self.side_cells[side2]
        
        for i in range(min(len(cells1), len(cells2))):
            if i < 16:
                cell1_id = cells1[i]
                cell2_id = cells2[31 - i]
                self.cells[cell1_id].add_neighbor(cell2_id)
                self.cells[cell2_id].add_neighbor(cell1_id)
                self.edges[(cell1_id, cell2_id)] = True
                self.edges[(cell2_id, cell1_id)] = True
    
    def mark_center(self):
        for side in [1, 2, 3]:
            center_start = 12
            center_end = 20
            for i in range(center_start, center_end):
                if i < len(self.side_cells[side]):
                    cell_id = self.side_cells[side][i]
                    self.center_cells.add(cell_id)
                    self.cells[cell_id].is_center = True
    
    def get_neighbors(self, cell_id: int) -> List[int]:
        if cell_id not in self.cells:
            return []
        return self.cells[cell_id].neighbors.copy()
    
    def is_valid_cell(self, cell_id: int) -> bool:
        return cell_id in self.cells
    
    def get_side(self, cell_id: int) -> Optional[int]:
        if cell_id not in self.cells:
            return None
        return self.cells[cell_id].side
    
    def is_center(self, cell_id: int) -> bool:
        return cell_id in self.center_cells
    
    def get_forward_neighbors(self, cell_id: int, player_side: int) -> List[int]:
        if cell_id not in self.cells:
            return []
        
        cell = self.cells[cell_id]
        forward = []
        
        for neighbor_id in cell.neighbors:
            neighbor = self.cells[neighbor_id]
            
            if neighbor.side == player_side:
                continue
            
            if neighbor.side == self.get_opposite_side(player_side):
                forward.append(neighbor_id)
            elif cell.is_center or neighbor.is_center:
                forward.append(neighbor_id)
        
        return forward
    
    def get_opposite_side(self, side: int) -> int:
        if side == 1:
            return 3
        elif side == 2:
            return 1
        else:
            return 2
    
    def get_all_diagonal_neighbors(self, cell_id: int) -> List[int]:
        return self.get_neighbors(cell_id)
    
    def get_three_diagonals_from_center(self, cell_id: int) -> List[List[int]]:
        if not self.is_center(cell_id):
            return []
        
        diagonals = []
        cell = self.cells[cell_id]
        
        for neighbor_id in cell.neighbors:
            diagonal = [cell_id, neighbor_id]
            current = neighbor_id
            
            while current in self.cells:
                next_neighbors = [n for n in self.cells[current].neighbors 
                                if n not in diagonal and self.cells[n].side != cell.side]
                if next_neighbors:
                    current = next_neighbors[0]
                    diagonal.append(current)
                else:
                    break
            
            if len(diagonal) > 2:
                diagonals.append(diagonal)
        
        return diagonals[:3]


def create_hex_board() -> HexagonalBoard:
    return HexagonalBoard()

