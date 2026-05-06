# Werewolf Role Modules

This folder contains one `.py` file per role.

## Main idea

Each role class receives:

```python
role = Seer(player_id="p1")
result = role.night_options(game)
```

Most methods return dictionaries, for example:

```python
{
    "role": "预言家",
    "action": "select_check_target",
    "players": [...]
}
```

Your Flask route can use these dictionaries to render HTML buttons, player lists, result logos, and messages.

## Important shared fields

`GameState` is inside `role_base.py`.

Important fields:

- `players`
- `phase`
- `wolf_night_target`
- `wolf_locks`
- `guard_previous_target`
- `witch_has_poison`
- `witch_has_antidote`
- `mechanical_copied_role`
- `wolf_beauty_charmed_target`

## Death / protection logic

Use:

```python
role.resolve_death(game, target_id)
```

Rule:

- `revive_status == 1`: avoid death, then reset to 0
- `revive_status >= 2`: die, then reset to 0
- `revive_status == 0`: die

Guard and Witch antidote both use `revive_status += 1`.

## Frontend image logic

For Seer:

```python
result = seer.check_player(game, target_id)
```

Then frontend checks:

```python
if result["logo"] == "cross":
    # show cross image
elif result["logo"] == "golden_potion":
    # show golden potion image
```

## Example

```python
from role_base import Player, GameState
from seer import Seer

players = {
    "p1": Player(id="p1", name="A", role="预言家", faction="god"),
    "p2": Player(id="p2", name="B", role="狼人", faction="wolve"),
    "p3": Player(id="p3", name="C", role="村民", faction="villager"),
}

game = GameState(players=players)
seer = Seer("p1")

print(seer.night_options(game))
print(seer.check_player(game, "p2"))
```
