import random
import uuid

from main.game_roles import (
    ROLE_BEAR,
    ROLE_HUNTER,
    ROLE_IDIOT,
    ROLE_KNIGHT,
    ROLE_MECHANICAL_WOLF,
    ROLE_WHITE_WOLF_KING,
    ROLE_WITCH,
    ROLE_WOLF_BEAUTY,
    ROLE_WOLF_KING,
    get_default_role_counts,
    get_role_names,
    get_role_team,
    is_god_role,
    is_wolf_role,
)

rooms = {}
next_room_number = 1


def normalize_room_id(room_id):
    if room_id is None:
        return ""
    return room_id.strip().upper()


def default_night_state():
    return {
        "current_role": None,
        "wolf_votes": {},
        "wolf_locks": {},
        "wolf_kill_target": None,
        "last_guard_target": None,
        "dead_tonight": [],
        "mechanical_wolf_copied": {},
        "results": {},
    }


def default_day_state():
    return {"announcements": [], "voted_out": None, "pending_day_skills": []}


def create_room():
    global next_room_number

    room_id = f"{next_room_number:03d}"
    next_room_number += 1

    rooms[room_id] = {
        "room_id": room_id,
        "players": {},
        "player_order": [],
        "host": None,
        "host_id": None,
        "host_user_id": None,
        "selected_role_counts": get_default_role_counts(),
        "assigned_roles": {},
        "status": "waiting",
        "phase": "waiting",
        "day_count": 0,
        "night_count": 0,
        "night": None,
        "night_state": default_night_state(),
        "day_state": default_day_state(),
        "death_log": [],
        "winner": None,
    }
    return rooms[room_id]


def get_room(room_id):
    return rooms.get(normalize_room_id(room_id))


def create_player(room, name):
    user_id = uuid.uuid4().hex[:8]
    room["players"][user_id] = {
        "user_id": user_id,
        "name": name.strip(),
        "room_id": room["room_id"],
        "role": None,
        "assigned_role": None,
        "team": None,
        "alive": True,
        "revive_status": 0,
        "protected_once": False,
        "charmed_by_wolf_beauty": False,
        "charmed_by": None,
        "copied_role": None,
        "copied_skill": None,
        "selected_previously": None,
        "skill_used": {},
        "statuses": {},
        "death_causes": [],
    }
    room["player_order"].append(user_id)

    if room["host_user_id"] is None:
        room["host_user_id"] = user_id
        room["host_id"] = user_id
        room["host"] = user_id

    return room["players"][user_id]


def is_host(room, user_id):
    return room is not None and user_id == room.get("host_user_id")


def count_selected_roles(role_counts):
    return sum(int(count) for count in role_counts.values())


def validate_role_counts(room, role_counts):
    player_count = len(room["players"])
    selected_count = count_selected_roles(role_counts)
    if selected_count > player_count:
        return False, "Too many roles selected", selected_count, player_count
    if selected_count < player_count:
        return False, "Too few roles selected", selected_count, player_count
    return True, "Role count matches player count", selected_count, player_count


def clean_role_counts(raw_counts):
    role_counts = {}
    for role_name in get_role_names():
        try:
            count = int(raw_counts.get(role_name, 0))
        except (TypeError, ValueError):
            count = 0
        role_counts[role_name] = max(count, 0)
    return role_counts


def build_default_skill_state(role_name):
    if role_name == ROLE_WITCH:
        return {"poison_used": False, "antidote_used": False}
    if role_name == ROLE_IDIOT:
        return {"reveal_used": False}
    if role_name == ROLE_KNIGHT:
        return {"challenge_used": False}
    if role_name in (ROLE_HUNTER, ROLE_WOLF_KING, ROLE_WHITE_WOLF_KING):
        return {"death_skill_used": False}
    if role_name == ROLE_MECHANICAL_WOLF:
        return {
            "copy_used": False,
            "copied_guard_used": False,
            "copied_witch_poison_used": False,
            "copied_death_skill_used": False,
        }
    return {}


def assign_roles(room, raw_counts):
    role_counts = clean_role_counts(raw_counts)
    valid, message, selected_count, player_count = validate_role_counts(room, role_counts)
    if not valid:
        return False, message, selected_count, player_count

    roles = []
    for role_name, count in role_counts.items():
        roles.extend([role_name] * count)
    random.shuffle(roles)

    room["selected_role_counts"] = role_counts
    room["assigned_roles"] = {}
    for user_id, role_name in zip(room["player_order"], roles):
        player = room["players"][user_id]
        player["role"] = role_name
        player["assigned_role"] = role_name
        player["team"] = get_role_team(role_name)
        player["alive"] = True
        player["revive_status"] = 0
        player["protected_once"] = False
        player["charmed_by_wolf_beauty"] = False
        player["charmed_by"] = None
        player["copied_role"] = None
        player["copied_skill"] = None
        player["selected_previously"] = None
        player["skill_used"] = build_default_skill_state(role_name)
        player["statuses"] = {}
        player["death_causes"] = []
        room["assigned_roles"][user_id] = role_name

    room["status"] = "roles_assigned"
    room["phase"] = "waiting"
    room["night_state"] = default_night_state()
    room["day_state"] = default_day_state()
    room["winner"] = None
    return True, "Roles assigned successfully", selected_count, player_count


def get_alive_players(room):
    return [player for player in room["players"].values() if player.get("alive", True)]


def get_alive_players_except_self(room, user_id):
    return [player for player in get_alive_players(room) if player["user_id"] != user_id]


def get_players_by_role(room, role):
    return [player for player in room["players"].values() if player.get("role") == role]


def get_alive_players_by_role(room, role):
    return [player for player in get_players_by_role(room, role) if player.get("alive", True)]


def is_last_god(room, user_id):
    player = room["players"].get(user_id)
    if not player or not is_god_role(player.get("role")):
        return False
    alive_gods = [p for p in get_alive_players(room) if is_god_role(p.get("role")) and p["user_id"] != user_id]
    return len(alive_gods) == 0


def is_last_wolf(room, user_id):
    player = room["players"].get(user_id)
    if not player or not is_wolf_role(player.get("role")):
        return False
    alive_wolves = [p for p in get_alive_players(room) if is_wolf_role(p.get("role")) and p["user_id"] != user_id]
    return len(alive_wolves) == 0


def kill_player(room, target_user_id, cause):
    player = room["players"].get(target_user_id)
    if player is None:
        return False, "Target player does not exist."

    if player.get("role") == ROLE_IDIOT and cause == "vote" and not player["skill_used"].get("reveal_used"):
        player["skill_used"]["reveal_used"] = True
        room["day_state"]["announcements"].append(f"{player['name']} is {ROLE_IDIOT} and avoided vote death once.")
        return True, f"{ROLE_IDIOT} revealed and avoided vote death."

    player["alive"] = False
    player["death_causes"].append(cause)
    room["death_log"].append({"user_id": target_user_id, "cause": cause})

    if room.get("phase") == "night":
        room["night_state"]["dead_tonight"].append(target_user_id)

    if player.get("role") == ROLE_WOLF_BEAUTY and cause != "guard" and room.get("phase") == "day":
        charm_id = find_wolf_beauty_charm_target(room, target_user_id)
        if charm_id:
            kill_player(room, charm_id, "wolf_beauty_charm")

    return True, f"{player['name']} died because of {cause}."


def add_revive_status(room, target_user_id, source):
    player = room["players"].get(target_user_id)
    if player is None:
        return False, "Target player does not exist."
    player["revive_status"] = player.get("revive_status", 0) + 1
    player["statuses"][f"revive_from_{source}"] = True
    return True, f"{player['name']} gained revive status from {source}."


def resolve_day_deaths(room):
    results = []
    for player in room["players"].values():
        revive_status = player.get("revive_status", 0)
        if revive_status == 1:
            player["alive"] = True
            results.append(f"{player['name']} survived/revived.")
        elif revive_status >= 2:
            player["alive"] = False
            player["death_causes"].append("revive_overflow")
            results.append(f"{player['name']} died from overlapping protection/revive.")
        player["revive_status"] = 0
    room["day_state"]["announcements"].extend(results)
    check_win_condition(room)
    return results


def get_previous_alive_player(room, user_id):
    alive_ids = [pid for pid in room["player_order"] if room["players"][pid].get("alive", True)]
    if user_id not in alive_ids or len(alive_ids) <= 1:
        return None
    index = alive_ids.index(user_id)
    return room["players"][alive_ids[index - 1]]


def get_next_alive_player(room, user_id):
    alive_ids = [pid for pid in room["player_order"] if room["players"][pid].get("alive", True)]
    if user_id not in alive_ids or len(alive_ids) <= 1:
        return None
    index = alive_ids.index(user_id)
    return room["players"][alive_ids[(index + 1) % len(alive_ids)]]


def find_wolf_beauty_charm_target(room, wolf_beauty_user_id):
    for player in room["players"].values():
        if player.get("charmed_by") == wolf_beauty_user_id:
            return player["user_id"]
    return None


def start_game(room):
    if room["status"] != "roles_assigned":
        return False, "Roles must be assigned before starting the game."
    room["status"] = "started"
    return True, "Game started."


def start_day(room):
    room["phase"] = "day"
    room["day_count"] += 1
    room["day_state"] = default_day_state()
    resolve_day_deaths(room)
    add_bear_announcement(room)
    check_win_condition(room)


def add_bear_announcement(room):
    bears = get_players_by_role(room, ROLE_BEAR)
    if not bears:
        return
    bear = bears[0]
    if not bear.get("alive", True):
        room["day_state"]["announcements"].append("\u718a\u6ca1\u6709\u53eb")
        return
    previous_player = get_previous_alive_player(room, bear["user_id"])
    next_player = get_next_alive_player(room, bear["user_id"])
    neighbor_roles = [p.get("role") for p in (previous_player, next_player) if p is not None]
    if any(is_wolf_role(role) for role in neighbor_roles):
        room["day_state"]["announcements"].append("\u718a\u53eb\u4e86")
    else:
        room["day_state"]["announcements"].append("\u718a\u6ca1\u6709\u53eb")


def check_win_condition(room):
    alive_players = get_alive_players(room)
    alive_wolves = [p for p in alive_players if is_wolf_role(p.get("role"))]
    alive_gods = [p for p in alive_players if is_god_role(p.get("role"))]
    alive_civilians = [p for p in alive_players if p.get("team") == "civilian"]
    if not alive_wolves:
        room["winner"] = "good"
        return "good"
    if not alive_gods or not alive_civilians:
        room["winner"] = "wolves"
        return "wolves"
    room["winner"] = None
    return None
