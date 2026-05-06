from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


WOLF_ROLES = {"狼人", "狼王", "白狼王", "狼美人", "机械狼"}
GOD_ROLES = {"预言家", "女巫", "猎人", "白痴", "守卫", "骑士", "熊"}


@dataclass
class Player:
    id: str
    name: str
    role: str
    faction: str
    alive: bool = True

    # revive_status:
    # 0 = normal
    # 1 = protected / can survive one death
    # 2 = protection conflicts / still dies
    revive_status: int = 0

    # flexible role statuses:
    # e.g. {"guard_selected_previous": True, "charmed_by": "p5"}
    statuses: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GameState:
    players: Dict[str, Player]

    # night info
    wolf_night_target: Optional[str] = None
    wolf_locks: Dict[str, str] = field(default_factory=dict)  # wolf_id -> target_id

    # role state
    guard_previous_target: Optional[str] = None
    idiot_revealed: bool = False
    witch_has_poison: bool = True
    witch_has_antidote: bool = True

    # mechanical wolf
    mechanical_copied_role: Optional[str] = None
    mechanical_copied_alignment_seen_by_seer: Optional[str] = None
    mechanical_guard_skill_used: bool = False
    mechanical_witch_poison_used: bool = False

    # wolf beauty
    wolf_beauty_charmed_target: Optional[str] = None

    # phase
    phase: str = "night"  # "night" or "day"


class BaseRole:
    role_name = ""
    faction = ""

    def __init__(self, player_id: str):
        self.player_id = player_id

    def me(self, game: GameState) -> Player:
        return game.players[self.player_id]

    def all_players(self, game: GameState) -> List[Player]:
        return list(game.players.values())

    def alive_players(self, game: GameState) -> List[Player]:
        return [p for p in game.players.values() if p.alive]

    def alive_players_except_self(self, game: GameState) -> List[Player]:
        return [p for p in game.players.values() if p.alive and p.id != self.player_id]

    def all_players_except_self(self, game: GameState) -> List[Player]:
        return [p for p in game.players.values() if p.id != self.player_id]

    def is_wolf_role(self, role: str) -> bool:
        return role in WOLF_ROLES

    def is_wolf_player(self, player: Player) -> bool:
        return player.role in WOLF_ROLES or player.faction == "wolve"

    def is_god_player(self, player: Player) -> bool:
        return player.role in GOD_ROLES or player.faction == "god"

    def remaining_wolves(self, game: GameState) -> List[Player]:
        return [p for p in game.players.values() if p.alive and self.is_wolf_player(p)]

    def remaining_gods(self, game: GameState) -> List[Player]:
        return [p for p in game.players.values() if p.alive and self.is_god_player(p)]

    def add_revive_status(self, game: GameState, target_id: str) -> Dict[str, Any]:
        target = game.players[target_id]
        target.revive_status += 1
        return {
            "ok": True,
            "target_id": target_id,
            "target_name": target.name,
            "revive_status": target.revive_status,
            "message": f"{target.name} revive_status +1",
        }

    def resolve_death(self, game: GameState, target_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Used during day death resolving.

        Rule based on your description:
        - revive_status == 1: revive / avoid death, then reset to 0
        - revive_status == 2 or more: die, then reset to 0
        - revive_status == 0: die
        """
        target = game.players[target_id]

        if not target.alive:
            return {
                "ok": False,
                "target_id": target_id,
                "message": f"{target.name} already dead.",
            }

        if target.revive_status == 1:
            target.revive_status = 0
            return {
                "ok": True,
                "target_id": target_id,
                "target_name": target.name,
                "dead": False,
                "revived": True,
                "reason": reason,
                "message": f"{target.name} revived / avoided death.",
            }

        target.alive = False
        target.revive_status = 0
        return {
            "ok": True,
            "target_id": target_id,
            "target_name": target.name,
            "dead": True,
            "revived": False,
            "reason": reason,
            "message": f"{target.name} died.",
        }

    def force_kill(self, game: GameState, target_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Direct death without revive-status checking.
        Useful for rules that should ignore protection.
        """
        target = game.players[target_id]
        target.alive = False
        return {
            "ok": True,
            "target_id": target_id,
            "target_name": target.name,
            "dead": True,
            "reason": reason,
            "message": f"{target.name} died.",
        }

    def player_list_payload(self, players: List[Player]) -> List[Dict[str, Any]]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "faction": p.faction,
                "alive": p.alive,
                "revive_status": p.revive_status,
                "statuses": p.statuses,
            }
            for p in players
        ]
