import random
import time

from main.game_roles import (
    NIGHT_ORDER,
    ROLE_GUARD,
    ROLE_MECHANICAL_WOLF,
    ROLE_SEER,
    ROLE_WEREWOLF,
    ROLE_WHITE_WOLF_KING,
    ROLE_WITCH,
    ROLE_WOLF_BEAUTY,
    ROLE_WOLF_KING,
    is_wolf_role,
)
from main.game_state import get_players_by_role, start_day

MAX_TURN_TIME = 180


def init_night_phase(room):
    room["phase"] = "night"
    room["night_count"] += 1
    room["night"] = {
        "order": NIGHT_ORDER,
        "index": 0,
        "current_role": None,
        "deadline": None,
        "dead_wait_until": None,
        "locked": {},
        "actions": [],
    }
    room["night_state"].update(
        {
            "current_role": None,
            "wolf_votes": {},
            "wolf_locks": {},
            "wolf_kill_target": None,
            "dead_tonight": [],
            "results": {},
        }
    )
    move_to_next_valid_role(room)


def get_wolf_group_players(room):
    wolves = []
    for player in room["players"].values():
        role = player.get("role")
        copied_skill = player.get("copied_skill")
        if role in (ROLE_WEREWOLF, ROLE_WOLF_KING, ROLE_WHITE_WOLF_KING, ROLE_WOLF_BEAUTY):
            wolves.append(player)
        elif role == ROLE_MECHANICAL_WOLF and copied_skill == ROLE_WEREWOLF:
            wolves.append(player)
    return wolves


def get_alive_wolf_group_players(room):
    return [player for player in get_wolf_group_players(room) if player.get("alive", True)]


def get_night_actor_players(room, role):
    if role == ROLE_WEREWOLF:
        return get_wolf_group_players(room)
    if role == ROLE_MECHANICAL_WOLF:
        return [
            player for player in get_players_by_role(room, ROLE_MECHANICAL_WOLF)
            if mechanical_wolf_has_night_action(room, player["user_id"])
        ]
    return get_players_by_role(room, role)


def get_alive_night_actor_players(room, role):
    return [player for player in get_night_actor_players(room, role) if player.get("alive", True)]


def mechanical_wolf_has_night_action(room, user_id):
    player = room["players"].get(user_id)
    if not player or player.get("role") != ROLE_MECHANICAL_WOLF:
        return False
    if not player["skill_used"].get("copy_used"):
        return True
    return player.get("copied_skill") in (ROLE_GUARD, ROLE_SEER, ROLE_WITCH, ROLE_WEREWOLF)


def can_mechanical_wolf_kill(room, mechanical_wolf_user_id):
    player = room["players"].get(mechanical_wolf_user_id)
    if not player or player.get("role") != ROLE_MECHANICAL_WOLF or not player.get("alive", True):
        return False
    other_alive_wolves = [
        p for p in room["players"].values()
        if p["user_id"] != mechanical_wolf_user_id and p.get("alive", True) and is_wolf_role(p.get("role"))
    ]
    if player.get("copied_skill") == ROLE_WEREWOLF:
        return True
    return not other_alive_wolves


def move_to_next_valid_role(room):
    night = room["night"]
    night["locked"] = {}
    night["current_role"] = None
    night["deadline"] = None
    night["dead_wait_until"] = None

    while night["index"] < len(night["order"]):
        role = night["order"][night["index"]]
        if not get_night_actor_players(room, role):
            night["index"] += 1
            continue
        night["current_role"] = role
        room["night_state"]["current_role"] = role
        if not get_alive_night_actor_players(room, role):
            night["dead_wait_until"] = time.time() + random.randint(2, 6)
            return
        night["deadline"] = time.time() + MAX_TURN_TIME
        return
    finish_night_phase(room)


def finish_night_phase(room):
    if room.get("night"):
        room["night"]["current_role"] = None
        room["night"]["deadline"] = None
        room["night"]["dead_wait_until"] = None
    room["night_state"]["current_role"] = None
    start_day(room)


def check_night_timer(room):
    if room.get("phase") != "night" or not room.get("night"):
        return
    night = room["night"]
    now = time.time()
    if night.get("dead_wait_until") is not None and now >= night["dead_wait_until"]:
        night["index"] += 1
        move_to_next_valid_role(room)
        return
    if night.get("deadline") is not None and now >= night["deadline"]:
        night["index"] += 1
        move_to_next_valid_role(room)


def player_can_act(room, user_id):
    if room.get("phase") != "night":
        return False
    check_night_timer(room)
    night = room["night"]
    current_role = night.get("current_role")
    player = room["players"].get(user_id)
    if not player or not player.get("alive", True) or night.get("dead_wait_until") is not None:
        return False
    if current_role == ROLE_WEREWOLF:
        return player in get_alive_wolf_group_players(room)
    if current_role == ROLE_MECHANICAL_WOLF:
        return player.get("role") == ROLE_MECHANICAL_WOLF and mechanical_wolf_has_night_action(room, user_id)
    return player.get("role") == current_role


def get_current_night_info(room, user_id):
    check_night_timer(room)
    if room.get("phase") != "night" or not room.get("night"):
        return {"phase": room.get("phase"), "current_role": None, "can_act": False, "message": "Night phase is not active."}
    night = room["night"]
    current_role = night.get("current_role")
    if current_role is None:
        return {"phase": room.get("phase"), "current_role": None, "can_act": False, "message": "Night phase ended."}
    if night.get("dead_wait_until") is not None:
        return {"phase": "night", "current_role": current_role, "can_act": False, "message": f"{current_role} is dead. Waiting briefly..."}
    if player_can_act(room, user_id):
        return {"phase": "night", "current_role": current_role, "can_act": True, "message": f"It is your turn: {current_role}"}
    return {"phase": "night", "current_role": current_role, "can_act": False, "message": f"Waiting for {current_role}..."}


def lock_current_role(room, user_id, action_data):
    night = room["night"]
    night["locked"][user_id] = {"role": night.get("current_role"), "user_id": user_id, **action_data}
    night["actions"].append(night["locked"][user_id])


def advance_night_role(room):
    room["night"]["index"] += 1
    move_to_next_valid_role(room)


def get_wolf_lock_summary(room):
    return {
        "locked_count": len(room["night_state"].get("wolf_locks", {})),
        "total_count": len(get_alive_wolf_group_players(room)),
        "votes": room["night_state"].get("wolf_votes", {}),
    }


def choose_final_wolf_target(room):
    votes = room["night_state"].get("wolf_votes", {})
    if not votes:
        return None
    highest_vote_count = max(votes.values())
    tied_targets = [target_id for target_id, count in votes.items() if count == highest_vote_count]
    return random.choice(tied_targets)


def lock_night_action(room, user_id, action_data):
    if room.get("phase") != "night":
        return False, "Not night phase."
    check_night_timer(room)
    if not player_can_act(room, user_id):
        return False, "You cannot act now."
    lock_current_role(room, user_id, action_data)
    advance_night_role(room)
    return True, "Action locked."
