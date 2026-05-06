from role_base import Player, GameState, BaseRole
from seer import Seer
from witch import Witch
from hunter import Hunter
from idiot import Idiot
from guard import Guard
from knight import Knight
from bear import Bear
from werewolf import Werewolf
from wolf_king import WolfKing
from white_wolf_king import WhiteWolfKing
from wolf_beauty import WolfBeauty
from mechanical_wolf import MechanicalWolf


ROLE_CLASS = {
    "预言家": Seer,
    "女巫": Witch,
    "猎人": Hunter,
    "白痴": Idiot,
    "守卫": Guard,
    "骑士": Knight,
    "熊": Bear,
    "狼人": Werewolf,
    "狼王": WolfKing,
    "白狼王": WhiteWolfKing,
    "狼美人": WolfBeauty,
    "机械狼": MechanicalWolf,
}
