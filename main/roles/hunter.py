from role_base import BaseRole, GameState


class Hunter(BaseRole):
    role_name = "猎人"
    faction = "god"

    def night_options(self, game: GameState):
        """
        Hunter will not awake at night.
        """
        return {
            "role": self.role_name,
            "awake": False,
            "message": "猎人夜晚不行动。",
        }

    def can_shoot(self, game: GameState):
        """
        If Hunter leaves during day phase, he can shoot.
        If Hunter is the last god, he cannot use skill.
        """
        if game.phase != "day":
            return False

        alive_gods = self.remaining_gods(game)
        return len(alive_gods) > 1

    def day_leave_options(self, game: GameState):
        if not self.can_shoot(game):
            return {
                "role": self.role_name,
                "can_use_skill": False,
                "message": "猎人是最后一个神，不能开枪。",
            }

        return {
            "role": self.role_name,
            "can_use_skill": True,
            "action": "select_shoot_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def shoot(self, game: GameState, target_id: str):
        if not self.can_shoot(game):
            return {"ok": False, "message": "猎人不能使用技能。"}

        return self.resolve_death(game, target_id, reason="猎人开枪")
