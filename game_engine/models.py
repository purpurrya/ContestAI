from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from .utils import Card


class GamePhase(Enum):
    WAITING = "waiting"
    BETTING = "betting"
    FINISHED = "finished"


class MoveType(Enum):
    FOLD = "fold"
    BET = "bet"
    CHECK = "check"
    CALL = "call"


@dataclass
class PlayerState:
    bot_id: str
    card: Optional[Card] = None
    chips: int = 100
    current_bet: int = 0
    total_bet: int = 0
    is_folded: bool = False
    is_active: bool = True
    
    def to_dict(self):
        result = {
            "bot_id": self.bot_id,
            "chips": self.chips,
            "current_bet": self.current_bet,
            "total_bet": self.total_bet,
            "is_folded": self.is_folded,
            "is_active": self.is_active
        }
        if self.card:
            result["card"] = self.card.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data):
        card = None
        if data.get("card"):
            card = Card.from_dict(data["card"])
        return cls(
            bot_id=data["bot_id"],
            card=card,
            chips=data["chips"],
            current_bet=data["current_bet"],
            total_bet=data["total_bet"],
            is_folded=data["is_folded"],
            is_active=data["is_active"]
        )


@dataclass
class GameState:
    match_id: str
    phase: GamePhase = GamePhase.WAITING
    players: List[PlayerState] = field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    current_player_index: int = 0
    dealer_index: int = 0
    last_bettor_index: int = -1
    move_history: List[Dict] = field(default_factory=list)
    winner_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    min_bet: int = 1
    max_bet: int = 100
    
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
        return [p for p in self.players if not p.is_folded and p.is_active]
    
    def is_betting_round_complete(self):
        active_players = self.get_active_players()
        if len(active_players) <= 1:
            return True
        
        if not active_players:
            return True
        
        if self.last_bettor_index == -1:
            if not all(p.current_bet == 0 for p in active_players):
                return False
            start_idx = self.dealer_index
            next_after_dealer = self.get_next_active_player_index(start_idx)
            return next_after_dealer is not None and self.current_player_index == next_after_dealer
        
        if self.last_bettor_index >= len(self.players):
            return True
        
        last_bettor = self.players[self.last_bettor_index]
        if last_bettor.is_folded or not last_bettor.is_active:
            return True
        
        target_bet = last_bettor.current_bet
        for p in active_players:
            if p.current_bet != target_bet:
                return False
        
        if self.current_player_index == self.last_bettor_index:
            return True
        
        next_after_last = self.get_next_active_player_index(self.last_bettor_index)
        return next_after_last is not None and self.current_player_index == next_after_last
    
    def rotate_dealer(self):
        active_players = [p for p in self.players if p.is_active]
        if not active_players:
            return

        next_dealer = None
        for i in range(len(self.players)):
            idx = (self.dealer_index + 1 + i) % len(self.players)
            if self.players[idx].is_active:
                next_dealer = idx
                break

        if next_dealer is not None:
            self.dealer_index = next_dealer
            self.current_player_index = next_dealer

    def get_dealer(self):
        if not self.players or self.dealer_index >= len(self.players):
            return None
        return self.players[self.dealer_index]
    
    def get_next_active_player_index(self, start_index):
        active_players = self.get_active_players()
        if not active_players:
            return None

        for i in range(len(self.players)):
            idx = (start_index + 1 + i) % len(self.players)
            if idx < len(self.players) and not self.players[idx].is_folded and self.players[idx].is_active:
                return idx
        return None

    def to_dict(self):
        result = {
            "match_id": self.match_id,
            "phase": self.phase.value,
            "players": [p.to_dict() for p in self.players],
            "pot": self.pot,
            "current_bet": self.current_bet,
            "current_player_index": self.current_player_index,
            "dealer_index": self.dealer_index,
            "last_bettor_index": self.last_bettor_index,
            "move_history": self.move_history,
            "winner_id": self.winner_id,
            "min_bet": self.min_bet,
            "max_bet": self.max_bet
        }
        if self.started_at:
            result["started_at"] = self.started_at.isoformat()
        if self.finished_at:
            result["finished_at"] = self.finished_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data):
        players = [PlayerState.from_dict(p) for p in data.get("players", [])]
        
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])
        
        finished_at = None
        if data.get("finished_at"):
            finished_at = datetime.fromisoformat(data["finished_at"])
        
        return cls(
            match_id=data["match_id"],
            phase=GamePhase(data["phase"]),
            players=players,
            pot=data.get("pot", 0),
            current_bet=data.get("current_bet", 0),
            current_player_index=data.get("current_player_index", 0),
            dealer_index=data.get("dealer_index", 0),
            last_bettor_index=data.get("last_bettor_index", -1),
            move_history=data.get("move_history", []),
            winner_id=data.get("winner_id"),
            started_at=started_at,
            finished_at=finished_at,
            min_bet=data.get("min_bet", 1),
            max_bet=data.get("max_bet", 100)
        )
