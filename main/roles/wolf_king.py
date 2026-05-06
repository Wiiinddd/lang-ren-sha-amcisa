from role_base import BaseRole, GameState
from werewolf import Werewolf


class WolfKing(Werewolf):
    role_name = "狼王"
    faction = "wolve"

    def can_death_kill(self, game: GameState):
        """
        When leaving, can kill one player.
        If 狼王 is the last wolf, he cannot use skill.
        """
        alive_wolves = self.remaining_wolves(game)
        return len(alive_wolves) > 1

    def leave_options(self, game: GameState):
        if not self.can_death_kill(game):
            return {
                "role": self.role_name,
                "can_use_skill": False,
                "message": "狼王是最后一只狼，不能发动技能。",
            }

        return {
            "role": self.role_name,
            "can_use_skill": True,
            "action": "select_death_kill_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def death_kill(self, game: GameState, target_id: str):
        if not self.can_death_kill(game):
            return {"ok": False, "message": "狼王不能发动技能。"}

        return self.resolve_death(game, target_id, reason="狼王带人")
