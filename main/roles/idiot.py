from role_base import BaseRole, GameState


class Idiot(BaseRole):
    role_name = "白痴"
    faction = "god"

    def on_voted_day(self, game: GameState):
        """
        If voted during day phase:
        reveal role and avoid death once.
        Only day phase.
        Still can be killed by wolves.
        """
        if game.phase != "day":
            return {
                "ok": False,
                "message": "白痴技能只能在白天被投票出局时触发。",
            }

        if game.idiot_revealed:
            return {
                "ok": False,
                "message": "白痴已经翻牌过，不能再次免死。",
            }

        game.idiot_revealed = True
        me = self.me(game)

        return {
            "ok": True,
            "reveal_role": self.role_name,
            "avoid_death": True,
            "player_id": me.id,
            "player_name": me.name,
            "message": f"{me.name} 翻牌为白痴，本次投票不死亡。",
        }

    def killed_by_wolves(self, game: GameState):
        """
        Wolves kill still works.
        """
        return self.resolve_death(game, self.player_id, reason="狼人击杀白痴")
