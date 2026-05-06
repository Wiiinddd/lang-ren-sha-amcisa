from role_base import BaseRole, GameState


class Werewolf(BaseRole):
    role_name = "狼人"
    faction = "wolve"

    def night_options(self, game: GameState):
        """
        Show all remaining players list.
        Wolves can choose anyone, including themselves.

        All remaining wolves need to select and lock.
        Need indicator: how many wolves locked at each player.
        """
        alive_wolves = self.remaining_wolves(game)

        lock_count_by_target = {}
        for target_id in game.wolf_locks.values():
            lock_count_by_target[target_id] = lock_count_by_target.get(target_id, 0) + 1

        players = []
        for p in self.alive_players(game):
            players.append({
                "id": p.id,
                "name": p.name,
                "role": p.role,
                "faction": p.faction,
                "lock_count": lock_count_by_target.get(p.id, 0),
            })

        return {
            "role": self.role_name,
            "action": "select_wolf_kill_target",
            "players": players,
            "wolves_alive_count": len(alive_wolves),
            "wolves_locked_count": len(game.wolf_locks),
            "all_wolves_locked": len(game.wolf_locks) >= len(alive_wolves),
        }

    def lock_kill_target(self, game: GameState, target_id: str):
        wolf = self.me(game)

        if not wolf.alive:
            return {"ok": False, "message": "死亡狼人不能锁定目标。"}

        game.wolf_locks[self.player_id] = target_id

        alive_wolves = self.remaining_wolves(game)
        all_locked = len(game.wolf_locks) >= len(alive_wolves)

        # Simple rule: final target is the target with most locks.
        # If tie, first one in lock order wins.
        final_target = None
        if all_locked:
            counts = {}
            for tid in game.wolf_locks.values():
                counts[tid] = counts.get(tid, 0) + 1

            final_target = max(counts, key=counts.get)
            game.wolf_night_target = final_target

        return {
            "ok": True,
            "wolf_id": self.player_id,
            "target_id": target_id,
            "wolves_alive_count": len(alive_wolves),
            "wolves_locked_count": len(game.wolf_locks),
            "all_wolves_locked": all_locked,
            "final_target": final_target,
            "message": "狼人已锁定目标。" if not all_locked else "所有狼人已锁定，已确定夜晚击杀目标。",
        }
