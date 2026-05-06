from role_base import BaseRole, GameState


class Witch(BaseRole):
    role_name = "女巫"
    faction = "god"

    def night_options(self, game: GameState):
        """
        First show who died at night: game.wolf_night_target.
        Then choose 毒药 or 解药.
        """
        dead_target = game.players.get(game.wolf_night_target) if game.wolf_night_target else None

        return {
            "role": self.role_name,
            "wolf_target": None if dead_target is None else {
                "id": dead_target.id,
                "name": dead_target.name,
            },
            "can_use_poison": game.witch_has_poison,
            "can_use_antidote": game.witch_has_antidote,
            "options": ["毒药", "解药"],
        }

    def poison_options(self, game: GameState):
        """
        If 毒药, show players exclude herself.
        """
        return {
            "role": self.role_name,
            "action": "select_poison_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def use_poison(self, game: GameState, target_id: str):
        if not game.witch_has_poison:
            return {"ok": False, "message": "女巫已经没有毒药。"}

        game.witch_has_poison = False
        return self.resolve_death(game, target_id, reason="女巫毒药")

    def use_antidote(self, game: GameState):
        """
        If 解药, the wolf target revive_status +1.
        During day phase death resolving:
        - revive_status == 1: revive
        - revive_status == 2: die
        """
        if not game.witch_has_antidote:
            return {"ok": False, "message": "女巫已经没有解药。"}

        if not game.wolf_night_target:
            return {"ok": False, "message": "今晚没有狼人击杀目标。"}

        game.witch_has_antidote = False
        return self.add_revive_status(game, game.wolf_night_target)
