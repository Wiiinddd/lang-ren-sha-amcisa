from role_base import BaseRole, GameState
from werewolf import Werewolf


class WolfBeauty(Werewolf):
    role_name = "狼美人"
    faction = "wolve"

    def charm_options_after_wolves_lock(self, game: GameState):
        """
        Awake with wolves.
        After all wolves choose target, 狼美人 chooses one player to charm.
        """
        alive_wolves = self.remaining_wolves(game)
        all_locked = len(game.wolf_locks) >= len(alive_wolves)

        if not all_locked:
            return {
                "role": self.role_name,
                "can_charm": False,
                "message": "需要所有狼人先锁定击杀目标。",
            }

        return {
            "role": self.role_name,
            "can_charm": True,
            "action": "select_charm_target",
            "players": self.player_list_payload(self.alive_players_except_self(game)),
        }

    def charm(self, game: GameState, target_id: str):
        old_target = game.wolf_beauty_charmed_target
        if old_target and old_target in game.players:
            game.players[old_target].statuses.pop("charmed_by", None)

        game.wolf_beauty_charmed_target = target_id
        game.players[target_id].statuses["charmed_by"] = self.player_id

        return {
            "ok": True,
            "target_id": target_id,
            "target_name": game.players[target_id].name,
            "message": f"狼美人魅惑了 {game.players[target_id].name}。",
        }

    def on_leave_day(self, game: GameState, killed_by_guard_skill: bool = False):
        """
        If 狼美人 leaves during day phase, charmed player also leaves.
        If 狼美人 leaves during day phase by 守卫 skill, charmed player will not leave.

        `killed_by_guard_skill` should be passed by your death-resolving system.
        """
        if game.phase != "day":
            return {
                "ok": False,
                "message": "狼美人带人只在白天离场时触发。",
            }

        if killed_by_guard_skill:
            return {
                "ok": True,
                "charmed_target_dies": False,
                "message": "狼美人因守卫技能离场，被魅惑玩家不离场。",
            }

        target_id = game.wolf_beauty_charmed_target
        if not target_id:
            return {
                "ok": True,
                "charmed_target_dies": False,
                "message": "没有被魅惑玩家。",
            }

        result = self.resolve_death(game, target_id, reason="狼美人魅惑带走")
        return {
            "ok": True,
            "charmed_target_dies": True,
            "death": result,
            "message": "狼美人离场，被魅惑玩家也离场。",
        }
