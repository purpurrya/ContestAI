from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime


class CheckersPhase(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class CheckersPlayer(Enum):
    WHITE = "white"
    RED = "red"
    BLACK = "black"


@dataclass
class CheckersPiece:
    player: CheckersPlayer
    is_king: bool = False
    
    def to_dict(self):
        return {
            "player": self.player.value,
            "is_king": self.is_king
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            player=CheckersPlayer(data["player"]),
            is_king=data.get("is_king", False)
        )


@dataclass
class CheckersPlayerState:
    bot_id: str
    color: CheckersPlayer
    pieces_count: int = 12
    kings_count: int = 0
    is_active: bool = True
    is_blocked: bool = False
    
    def to_dict(self):
        return {
            "bot_id": self.bot_id,
            "color": self.color.value,
            "pieces_count": self.pieces_count,
            "kings_count": self.kings_count,
            "is_active": self.is_active,
            "is_blocked": self.is_blocked
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            bot_id=data["bot_id"],
            color=CheckersPlayer(data["color"]),
            pieces_count=data.get("pieces_count", 12),
            kings_count=data.get("kings_count", 0),
            is_active=data.get("is_active", True),
            is_blocked=data.get("is_blocked", False)
        )


@dataclass
class CheckersGameState:
    match_id: str
    phase: CheckersPhase = CheckersPhase.WAITING
    players: List[CheckersPlayerState] = field(default_factory=list)
    board: Dict[int, CheckersPiece] = field(default_factory=dict)
    current_player_index: int = 0
    move_history: List[Dict] = field(default_factory=list)
    winner_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    board_size: int = 12
    hex_board: Any = None
    
    def get_player(self, bot_id):
        for player in self.players:
            if player.bot_id == bot_id:
                return player
        return None
    
    def get_current_player(self):
        if not self.players or self.current_player_index >= len(self.players):
            return None
        return self.players[self.current_player_index]
    
    def get_active_players(self):
        return [p for p in self.players if p.is_active and p.pieces_count > 0]
    
    def count_kings(self, player_color):
        count = 0
        for piece in self.board.values():
            if piece.player == player_color and piece.is_king:
                count += 1
        return count
    
    def count_regular_pieces(self, player_color):
        count = 0
        for piece in self.board.values():
            if piece.player == player_color and not piece.is_king:
                count += 1
        return count
    
    
    def count_pieces(self, player_color):
        count = 0
        for piece in self.board.values():
            if piece.player == player_color:
                count += 1
        return count
    
    def to_dict(self):
        board_dict = {}
        for cell_id, piece in self.board.items():
            board_dict[str(cell_id)] = piece.to_dict()
        
        result = {
            "match_id": self.match_id,
            "phase": self.phase.value,
            "players": [p.to_dict() for p in self.players],
            "board": board_dict,
            "current_player_index": self.current_player_index,
            "move_history": self.move_history,
            "board_size": self.board_size
        }
        
        if self.winner_id:
            result["winner_id"] = self.winner_id
        if self.started_at:
            result["started_at"] = self.started_at.isoformat()
        if self.finished_at:
            result["finished_at"] = self.finished_at.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data):
        board = {}
        for cell_id_str, piece_data in data.get("board", {}).items():
            cell_id = int(cell_id_str)
            board[cell_id] = CheckersPiece.from_dict(piece_data)
        
        players = [CheckersPlayerState.from_dict(p) for p in data.get("players", [])]
        
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])
        
        finished_at = None
        if data.get("finished_at"):
            finished_at = datetime.fromisoformat(data["finished_at"])
        
        return cls(
            match_id=data["match_id"],
            phase=CheckersPhase(data["phase"]),
            players=players,
            board=board,
            current_player_index=data.get("current_player_index", 0),
            move_history=data.get("move_history", []),
            winner_id=data.get("winner_id"),
            started_at=started_at,
            finished_at=finished_at,
            board_size=data.get("board_size", 12)
        )


