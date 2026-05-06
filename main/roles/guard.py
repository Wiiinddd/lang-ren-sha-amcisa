from role_base import BaseRole, GameState


class Guard(BaseRole):
    role_name = "守卫"
    faction = "god"

    def night_options(self, game: GameState):
        """
        Show all remaining players.
        Cannot choose player with selected previously status.
        """
        players = []
        for p in self.alive_players(game):
            players.append({
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "faction": p.faction,
                "alive": p.alive,
                "cannot_select": p.id == game.guard_previous_target,
                "selected_previously": p.id == game.guard_previous_target,
            })

        return {
            "role": self.role_name,
            "action": "select_guard_target",
            "players": players,
        }

    def protect(self, game: GameState, target_id: str):
        if target_id == game.guard_previous_target:
            return {
                "ok": False,
                "message": "守卫不能连续守护同一个玩家。",
            }

        # remove old selected status
        if game.guard_previous_target and game.guard_previous_target in game.players:
            game.players[game.guard_previous_target].statuses["guard_selected_previous"] = False

        # add protection
        result = self.add_revive_status(game, target_id)

        # update selected previous status
        game.guard_previous_target = target_id
        game.players[target_id].statuses["guard_selected_previous"] = True

        result["message"] = f"守卫选择守护 {game.players[target_id].name}。"
        return result
