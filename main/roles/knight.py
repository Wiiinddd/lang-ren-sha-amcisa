from role_base import BaseRole, GameState


class Knight(BaseRole):
    role_name = "骑士"
    faction = "god"

    def day_options(self, game: GameState):
        """
        At day phase, can use skill.
        Frontend gives two buttons: fail / success.
        """
        if game.phase != "day":
            return {
                "role": self.role_name,
                "can_use_skill": False,
                "message": "骑士技能只能在白天使用。",
            }

        return {
            "role": self.role_name,
            "can_use_skill": True,
            "options": ["fail", "success"],
            "message": "选择骑士决斗结果。",
        }

    def resolve_skill(self, game: GameState, result: str):
        """
        fail: 骑士 dies and continue day phase.
        success: 骑士 remains and immediately go into night phase.
        """
        if game.phase != "day":
            return {"ok": False, "message": "现在不是白天，不能使用骑士技能。"}

        if result == "fail":
            death = self.resolve_death(game, self.player_id, reason="骑士技能失败")
            game.phase = "day"
            return {
                "ok": True,
                "skill_result": "fail",
                "phase": game.phase,
                "death": death,
                "message": "骑士失败，骑士死亡，继续白天。",
            }

        if result == "success":
            game.phase = "night"
            return {
                "ok": True,
                "skill_result": "success",
                "phase": game.phase,
                "message": "骑士成功，骑士不死，立即进入夜晚。",
            }

        return {"ok": False, "message": "result 只能是 fail 或 success。"}
