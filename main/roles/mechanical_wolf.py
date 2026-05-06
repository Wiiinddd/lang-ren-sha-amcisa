from role_base import BaseRole, GameState, WOLF_ROLES
from seer import Seer


class MechanicalWolf(BaseRole):
    role_name = "机械狼"
    faction = "wolve"

    def night_options(self, game: GameState):
        """
        Mechanical wolf will not awake with wolves.
        First night: show all remaining players exclude himself to copy.
        After copied, use copied skill if available.
        """
        if game.mechanical_copied_role is None:
            return {
                "role": self.role_name,
                "action": "select_copy_target",
                "players": self.player_list_payload(self.alive_players_except_self(game)),
            }

        return {
            "role": self.role_name,
            "copied_role": game.mechanical_copied_role,
            "message": "机械狼已经获得技能，请调用对应 copied_* 方法。",
        }

    def copy_target(self, game: GameState, target_id: str):
        target = game.players[target_id]
        game.mechanical_copied_role = target.role

        # How Seer sees Mechanical Wolf depends on copied role.
        if target.role in WOLF_ROLES:
            game.mechanical_copied_alignment_seen_by_seer = "wolve"
        else:
            game.mechanical_copied_alignment_seen_by_seer = "god"

        return {
            "ok": True,
            "copied_player_id": target_id,
            "copied_player_name": target.name,
            "copied_role": target.role,
            "seer_will_see_as": game.mechanical_copied_alignment_seen_by_seer,
            "message": f"机械狼复制了 {target.name} 的身份：{target.role}",
        }

    def copied_guard_options(self, game: GameState):
        """
        If copied 守卫:
        can choose to protect someone only one time.
        Protected target can avoid from any death.
        """
        if game.mechanical_copied_role != "守卫":
            return {"ok": False, "message": "机械狼没有复制守卫。"}

        if game.mechanical_guard_skill_used:
            return {"ok": False, "message": "机械狼守卫技能已经使用过。"}

        return {
            "ok": True,
            "action": "select_mechanical_guard_target",
            "players": self.player_list_payload(self.alive_players(game)),
        }

    def copied_guard_protect(self, game: GameState, target_id: str):
        if game.mechanical_copied_role != "守卫":
            return {"ok": False, "message": "机械狼没有复制守卫。"}

        if game.mechanical_guard_skill_used:
            return {"ok": False, "message": "机械狼守卫技能已经使用过。"}

        game.mechanical_guard_skill_used = True
        target = game.players[target_id]
        target.statuses["mechanical_guard_protected"] = True

        return {
            "ok": True,
            "target_id": target_id,
            "target_name": target.name,
            "message": f"{target.name} 获得机械狼守卫保护，可避免任何死亡一次。",
        }

    def resolve_mechanical_guard_protection(self, game: GameState, target_id: str):
        """
        Call this before any death.
        If target has mechanical_guard_protected, remove the status and avoid death.
        """
        target = game.players[target_id]

        if target.statuses.get("mechanical_guard_protected"):
            target.statuses["mechanical_guard_protected"] = False
            return {
                "protected": True,
                "target_id": target_id,
                "message": f"{target.name} 被机械狼守卫技能保护，避免死亡。",
            }

        return {"protected": False}

    def copied_seer_options(self, game: GameState):
        """
        If copied 预言家:
        every night can check player.
        """
        if game.mechanical_copied_role != "预言家":
            return {"ok": False, "message": "机械狼没有复制预言家。"}

        return {
            "ok": True,
            "action": "select_mechanical_seer_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def copied_seer_check(self, game: GameState, target_id: str):
        if game.mechanical_copied_role != "预言家":
            return {"ok": False, "message": "机械狼没有复制预言家。"}

        # Reuse Seer logic, but acting player is mechanical wolf.
        return Seer(self.player_id).check_player(game, target_id)

    def copied_witch_poison_options(self, game: GameState):
        """
        If copied 女巫:
        gets one poison, same as witch poison.
        """
        if game.mechanical_copied_role != "女巫":
            return {"ok": False, "message": "机械狼没有复制女巫。"}

        if game.mechanical_witch_poison_used:
            return {"ok": False, "message": "机械狼毒药已经使用过。"}

        return {
            "ok": True,
            "action": "select_mechanical_poison_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def copied_witch_poison(self, game: GameState, target_id: str):
        if game.mechanical_copied_role != "女巫":
            return {"ok": False, "message": "机械狼没有复制女巫。"}

        if game.mechanical_witch_poison_used:
            return {"ok": False, "message": "机械狼毒药已经使用过。"}

        game.mechanical_witch_poison_used = True
        return self.resolve_death(game, target_id, reason="机械狼复制女巫毒药")

    def copied_hunter_options(self, game: GameState):
        """
        If copied 猎人:
        when leaving at day phase, can shoot.
        """
        if game.mechanical_copied_role != "猎人":
            return {"ok": False, "message": "机械狼没有复制猎人。"}

        if game.phase != "day":
            return {"ok": False, "message": "机械狼猎人技能只能在白天离场时使用。"}

        return {
            "ok": True,
            "action": "select_mechanical_hunter_shoot_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def copied_hunter_shoot(self, game: GameState, target_id: str):
        if game.mechanical_copied_role != "猎人":
            return {"ok": False, "message": "机械狼没有复制猎人。"}

        if game.phase != "day":
            return {"ok": False, "message": "现在不是白天，不能开枪。"}

        return self.resolve_death(game, target_id, reason="机械狼复制猎人开枪")

    def copied_werewolf_options(self, game: GameState):
        """
        If copied 狼人:
        can kill one player at mechanical wolf's turn.
        """
        if game.mechanical_copied_role != "狼人":
            return {"ok": False, "message": "机械狼没有复制狼人。"}

        return {
            "ok": True,
            "action": "select_mechanical_wolf_kill_target",
            "players": self.player_list_payload(self.alive_players(game)),
        }

    def copied_werewolf_kill(self, game: GameState, target_id: str):
        if game.mechanical_copied_role != "狼人":
            return {"ok": False, "message": "机械狼没有复制狼人。"}

        return self.resolve_death(game, target_id, reason="机械狼复制狼人击杀")

    def can_normal_mechanical_kill(self, game: GameState):
        """
        Rule:
        - if all wolves are remaining, mechanical wolf cannot kill others
          except copied 狼人 skill.
        - if no wolves remaining, mechanical wolf can kill others.
        - if copied 狼人, then he can kill two:
          one normal kill + one copied werewolf kill.
        """
        alive_wolves = self.remaining_wolves(game)
        alive_wolves_except_mech = [w for w in alive_wolves if w.id != self.player_id]

        return len(alive_wolves_except_mech) == 0

    def normal_kill_options(self, game: GameState):
        if not self.can_normal_mechanical_kill(game):
            return {
                "ok": False,
                "message": "还有其他狼人存活，机械狼不能进行普通击杀。",
            }

        return {
            "ok": True,
            "action": "select_mechanical_normal_kill_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
            "extra_copied_wolf_kill_available": game.mechanical_copied_role == "狼人",
        }

    def normal_kill(self, game: GameState, target_id: str):
        if not self.can_normal_mechanical_kill(game):
            return {
                "ok": False,
                "message": "还有其他狼人存活，机械狼不能进行普通击杀。",
            }

        return self.resolve_death(game, target_id, reason="机械狼普通击杀")
