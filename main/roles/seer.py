from role_base import BaseRole, GameState


class Seer(BaseRole):
    role_name = "预言家"
    faction = "god"

    def night_options(self, game: GameState):
        """
        Show all remaining players except himself.
        Frontend should render this list for selection.
        """
        return {
            "role": self.role_name,
            "action": "select_check_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def check_player(self, game: GameState, target_id: str):
        """
        If target is wolf team -> show cross logo.
        If target is not wolf team -> show golden potion picture.

        Special rule:
        If target is 机械狼, result depends on copied skill alignment.
        Example: if 机械狼 copied 守卫, Seer sees golden potion.
        """
        target = game.players[target_id]

        if target.role == "机械狼":
            seen_alignment = game.mechanical_copied_alignment_seen_by_seer

            if seen_alignment == "wolve":
                is_wolf_result = True
            elif seen_alignment == "god":
                is_wolf_result = False
            else:
                # no copied role yet, default treat as wolf team
                is_wolf_result = True
        else:
            is_wolf_result = self.is_wolf_player(target)

        return {
            "role": self.role_name,
            "target_id": target.id,
            "target_name": target.name,
            "is_wolf": is_wolf_result,
            "logo": "cross" if is_wolf_result else "golden_potion",
            "message": "查验结果：狼人阵营" if is_wolf_result else "查验结果：好人阵营",
        }
