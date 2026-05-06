ROLE_WEREWOLF = "\u72fc\u4eba"
ROLE_WOLF_KING = "\u72fc\u738b"
ROLE_WHITE_WOLF_KING = "\u767d\u72fc\u738b"
ROLE_WOLF_BEAUTY = "\u72fc\u7f8e\u4eba"
ROLE_MECHANICAL_WOLF = "\u673a\u68b0\u72fc"
ROLE_SEER = "\u9884\u8a00\u5bb6"
ROLE_WITCH = "\u5973\u5deb"
ROLE_HUNTER = "\u730e\u4eba"
ROLE_IDIOT = "\u767d\u75f4"
ROLE_GUARD = "\u5b88\u536b"
ROLE_KNIGHT = "\u9a91\u58eb"
ROLE_BEAR = "\u718a"
ROLE_VILLAGER = "\u5e73\u6c11"

GOD_ROLES = {
    ROLE_SEER,
    ROLE_WITCH,
    ROLE_HUNTER,
    ROLE_IDIOT,
    ROLE_GUARD,
    ROLE_KNIGHT,
    ROLE_BEAR,
}
WOLF_ROLES = {
    ROLE_WEREWOLF,
    ROLE_WOLF_KING,
    ROLE_WHITE_WOLF_KING,
    ROLE_WOLF_BEAUTY,
    ROLE_MECHANICAL_WOLF,
}
CIVILIAN_ROLES = {ROLE_VILLAGER}

ROLE_DEFINITIONS = [
    {"name": ROLE_WEREWOLF, "team": "wolf", "default_count": 0, "night": True, "image": "werewolf.png"},
    {"name": ROLE_WOLF_KING, "team": "wolf", "default_count": 0, "night": False, "image": "wolf_king.png"},
    {"name": ROLE_WHITE_WOLF_KING, "team": "wolf", "default_count": 0, "night": False, "image": "white_wolf_king.png"},
    {"name": ROLE_WOLF_BEAUTY, "team": "wolf", "default_count": 0, "night": True, "image": "wolf_beauty.png"},
    {"name": ROLE_MECHANICAL_WOLF, "team": "wolf", "default_count": 0, "night": True, "image": "mechanical_wolf.png"},
    {"name": ROLE_SEER, "team": "god", "default_count": 0, "night": True, "image": "seer.png"},
    {"name": ROLE_WITCH, "team": "god", "default_count": 0, "night": True, "image": "witch.png"},
    {"name": ROLE_HUNTER, "team": "god", "default_count": 0, "night": False, "image": "hunter.png"},
    {"name": ROLE_IDIOT, "team": "god", "default_count": 0, "night": False, "image": "idiot.png"},
    {"name": ROLE_GUARD, "team": "god", "default_count": 0, "night": True, "image": "guard.png"},
    {"name": ROLE_KNIGHT, "team": "god", "default_count": 0, "night": False, "image": "knight.png"},
    {"name": ROLE_BEAR, "team": "god", "default_count": 0, "night": False, "image": "bear.png"},
    {"name": ROLE_VILLAGER, "team": "civilian", "default_count": 0, "night": False, "image": "villager.png"},
]

ROLE_CONFIG = {role["name"]: role for role in ROLE_DEFINITIONS}
NIGHT_ORDER = [ROLE_GUARD, ROLE_SEER, ROLE_WEREWOLF, ROLE_WOLF_BEAUTY, ROLE_MECHANICAL_WOLF, ROLE_WITCH]


def get_role_definitions():
    return ROLE_DEFINITIONS


def get_role_names():
    return [role["name"] for role in ROLE_DEFINITIONS]


def get_default_role_counts():
    return {role["name"]: role["default_count"] for role in ROLE_DEFINITIONS}


def get_role_team(role):
    return ROLE_CONFIG.get(role, {}).get("team", "civilian")


def get_role_image_filename(role):
    return ROLE_CONFIG.get(role, {}).get("image", "sample_role.png")


def is_wolf_role(role):
    return role in WOLF_ROLES


def is_god_role(role):
    return role in GOD_ROLES


def is_civilian_role(role):
    return role in CIVILIAN_ROLES
