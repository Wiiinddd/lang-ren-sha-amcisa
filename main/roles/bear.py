from role_base import BaseRole, GameState


class Bear(BaseRole):
    role_name = "熊"
    faction = "god"

    def day_announcement(self, game: GameState):
        """
        If either previous or next remaining player is wolf:
        announce 熊叫了.

        Remaining player order follows current order of game.players values.
        """
        bear = self.me(game)

        if not bear.alive:
            return {
                "role": self.role_name,
                "bear_roared": False,
                "announcement": "熊没有叫",
                "message": "熊已经死亡。",
            }

        alive_players = [p for p in game.players.values() if p.alive]
        ids = [p.id for p in alive_players]

        if bear.id not in ids:
            return {
                "role": self.role_name,
                "bear_roared": False,
                "announcement": "熊没有叫",
            }

        idx = ids.index(bear.id)

        prev_player = alive_players[idx - 1] if idx > 0 else None
        next_player = alive_players[idx + 1] if idx < len(alive_players) - 1 else None

        prev_is_wolf = prev_player is not None and self.is_wolf_player(prev_player)
        next_is_wolf = next_player is not None and self.is_wolf_player(next_player)

        roar = prev_is_wolf or next_is_wolf

        return {
            "role": self.role_name,
            "bear_roared": roar,
            "announcement": "熊叫了" if roar else "熊没有叫",
            "prev_player": None if prev_player is None else prev_player.name,
            "next_player": None if next_player is None else next_player.name,
        }
