from main.game_roles import get_role_names
from main.game_state import assign_roles


def get_available_roles():
    return get_role_names()


def assign_roles_to_players(players, role_counts):
    room = {
        "players": players,
        "selected_role_counts": {},
        "assigned_roles": {},
        "status": "waiting",
        "phase": "lobby",
    }
    success, message, _selected_count, _player_count = assign_roles(room, role_counts)
    return success, message
