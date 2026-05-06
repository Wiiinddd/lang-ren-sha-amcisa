from game_roles import (
    ROLE_GUARD,
    ROLE_HUNTER,
    ROLE_IDIOT,
    ROLE_KNIGHT,
    ROLE_MECHANICAL_WOLF,
    ROLE_SEER,
    ROLE_WEREWOLF,
    ROLE_WHITE_WOLF_KING,
    ROLE_WITCH,
    ROLE_WOLF_BEAUTY,
    ROLE_WOLF_KING,
    is_wolf_role,
)
from game_state import (
    add_revive_status,
    check_win_condition,
    get_alive_players,
    get_alive_players_except_self,
    is_last_god,
    is_last_wolf,
    kill_player,
)
from night_phase import (
    advance_night_role,
    can_mechanical_wolf_kill,
    choose_final_wolf_target,
    get_wolf_lock_summary,
    lock_current_role,
    player_can_act,
)


def get_seer_result(room, target_user_id):
    target = room["players"].get(target_user_id)
    if target is None:
        return {"result": "unknown", "image": "?", "message": "Target not found."}
    if target.get("role") == ROLE_MECHANICAL_WOLF:
        if target.get("copied_skill") in (ROLE_GUARD, ROLE_SEER, ROLE_WITCH, ROLE_HUNTER):
            return {"result": "good", "image": "golden_potion", "message": "\u91d1\u6c34"}
        return {"result": "wolf", "image": "cross", "message": "\u67e5\u6740"}
    if is_wolf_role(target.get("role")):
        return {"result": "wolf", "image": "cross", "message": "\u67e5\u6740"}
    return {"result": "good", "image": "golden_potion", "message": "\u91d1\u6c34"}


def get_skill_context(room, user_id):
    player = room["players"][user_id]
    phase = room.get("phase")
    current_role = room.get("night", {}).get("current_role") if room.get("night") else None
    can_act = player_can_act(room, user_id) if phase == "night" else True
    context = {
        "phase": phase,
        "player": player,
        "current_role": current_role,
        "can_act": can_act,
        "title": "Skill",
        "action_url": None,
        "targets": [],
        "options": [],
        "message": "",
        "wolf_summary": None,
        "night_result": room["night_state"].get("results", {}).get(user_id),
    }
    if phase == "night":
        build_night_context(room, user_id, context)
    elif phase == "day":
        build_day_context(room, user_id, context)
    else:
        context["message"] = "No skill is active in this phase."
    return context


def build_night_context(room, user_id, context):
    player = context["player"]
    role = context["current_role"]
    context["action_url"] = f"/skill/{role}"
    if not context["can_act"]:
        context["message"] = f"Waiting for {role}."
        return
    if role == ROLE_GUARD:
        last_target = room["night_state"].get("last_guard_target")
        context["title"] = ROLE_GUARD
        context["targets"] = [p for p in get_alive_players(room) if p["user_id"] != last_target]
        context["message"] = "Choose one alive player to protect. You cannot repeat last night's target."
    elif role == ROLE_SEER:
        context["title"] = ROLE_SEER
        context["targets"] = get_alive_players_except_self(room, user_id)
        context["message"] = "Choose one alive player to check."
    elif role == ROLE_WEREWOLF:
        context["title"] = ROLE_WEREWOLF
        context["targets"] = get_alive_players(room)
        context["wolf_summary"] = get_wolf_lock_summary(room)
        context["message"] = "All alive wolves lock a kill target."
    elif role == ROLE_WOLF_BEAUTY:
        context["title"] = ROLE_WOLF_BEAUTY
        context["targets"] = get_alive_players(room)
        context["message"] = "Choose one alive player to charm."
    elif role == ROLE_MECHANICAL_WOLF:
        context["title"] = ROLE_MECHANICAL_WOLF
        build_mechanical_wolf_context(room, user_id, context)
    elif role == ROLE_WITCH:
        context["title"] = ROLE_WITCH
        wolf_target = room["night_state"].get("wolf_kill_target")
        dead_tonight = room["night_state"].get("dead_tonight", [])
        context["message"] = "Wolf target: " + get_player_name(room, wolf_target or (dead_tonight[0] if dead_tonight else None))
        if not player["skill_used"].get("poison_used"):
            context["options"].append({"value": "poison", "label": "\u6bd2\u836f"})
        if wolf_target and not player["skill_used"].get("antidote_used"):
            context["options"].append({"value": "antidote", "label": "\u89e3\u836f"})
        context["targets"] = get_alive_players_except_self(room, user_id)


def build_mechanical_wolf_context(room, user_id, context):
    player = context["player"]
    copied_skill = player.get("copied_skill")
    if not player["skill_used"].get("copy_used"):
        context["targets"] = get_alive_players_except_self(room, user_id)
        context["message"] = "First night: choose one alive player to copy."
    elif copied_skill == ROLE_GUARD and not player["skill_used"].get("copied_guard_used"):
        context["targets"] = get_alive_players(room)
        context["message"] = "Copied guard: protect one player one time."
    elif copied_skill == ROLE_SEER:
        context["targets"] = get_alive_players_except_self(room, user_id)
        context["message"] = "Copied seer: check one player."
    elif copied_skill == ROLE_WITCH and not player["skill_used"].get("copied_witch_poison_used"):
        context["targets"] = get_alive_players_except_self(room, user_id)
        context["message"] = "Copied witch: poison one player one time."
    elif copied_skill == ROLE_WEREWOLF or can_mechanical_wolf_kill(room, user_id):
        context["targets"] = get_alive_players(room)
        context["message"] = "Mechanical wolf kill action."
    else:
        context["message"] = "No mechanical wolf skill is available now."


def build_day_context(room, user_id, context):
    player = context["player"]
    role = player.get("role")
    context["action_url"] = f"/day/skill/{role}"
    if role == ROLE_HUNTER:
        context["title"] = ROLE_HUNTER
        if is_last_god(room, user_id) or player["skill_used"].get("death_skill_used"):
            context["message"] = "Hunter skill is not available."
        else:
            context["targets"] = get_alive_players_except_self(room, user_id)
            context["message"] = "If hunter leaves during day, choose one player to shoot."
    elif role in (ROLE_WOLF_KING, ROLE_WHITE_WOLF_KING):
        context["title"] = role
        if is_last_wolf(room, user_id) or player["skill_used"].get("death_skill_used"):
            context["message"] = "Death skill is not available."
        else:
            context["targets"] = get_alive_players_except_self(room, user_id)
            context["message"] = "Choose one alive player to kill when leaving during day."
    elif role == ROLE_KNIGHT:
        context["title"] = ROLE_KNIGHT
        if player["skill_used"].get("challenge_used"):
            context["message"] = "Knight skill has already been used."
        else:
            context["options"] = [{"value": "fail", "label": "fail"}, {"value": "success", "label": "success"}]
            context["message"] = "Use the knight skill once during day."
    elif role == ROLE_MECHANICAL_WOLF and player.get("copied_skill") == ROLE_HUNTER:
        context["title"] = "Mechanical wolf copied hunter"
        if player["skill_used"].get("copied_death_skill_used"):
            context["message"] = "Copied hunter skill already used."
        else:
            context["targets"] = get_alive_players_except_self(room, user_id)
            context["message"] = "Copied hunter death skill placeholder."
    else:
        context["message"] = "No day skill is available for your role."


def submit_night_skill(room, user_id, role_name, form):
    if room.get("phase") != "night":
        return False, "Not night phase."
    if not player_can_act(room, user_id):
        return False, "You cannot act now."
    if room["night"]["current_role"] != role_name:
        return False, "It is not this role's turn."
    target_id = form.get("target_id")
    option = form.get("option")
    if role_name == ROLE_GUARD:
        return guard_skill(room, user_id, target_id)
    if role_name == ROLE_SEER:
        return seer_skill(room, user_id, target_id)
    if role_name == ROLE_WEREWOLF:
        return wolf_skill(room, user_id, target_id)
    if role_name == ROLE_WOLF_BEAUTY:
        return wolf_beauty_skill(room, user_id, target_id)
    if role_name == ROLE_MECHANICAL_WOLF:
        return mechanical_wolf_skill(room, user_id, target_id)
    if role_name == ROLE_WITCH:
        return witch_skill(room, user_id, option, target_id)
    return False, "Unknown night skill."


def guard_skill(room, user_id, target_id):
    if target_id == room["night_state"].get("last_guard_target"):
        return False, "Guard cannot protect the same player as last night."
    ok, message = add_revive_status(room, target_id, "guard")
    if ok:
        room["night_state"]["last_guard_target"] = target_id
        lock_current_role(room, user_id, {"target_id": target_id})
        advance_night_role(room)
    return ok, message


def seer_skill(room, user_id, target_id):
    result = get_seer_result(room, target_id)
    room["night_state"]["results"][user_id] = result
    lock_current_role(room, user_id, {"target_id": target_id, "result": result})
    advance_night_role(room)
    return True, result["message"]


def wolf_skill(room, user_id, target_id):
    room["night_state"]["wolf_locks"][user_id] = target_id
    votes = {}
    for locked_target in room["night_state"]["wolf_locks"].values():
        votes[locked_target] = votes.get(locked_target, 0) + 1
    room["night_state"]["wolf_votes"] = votes
    alive_wolves = [
        p for p in room["players"].values()
        if p.get("alive", True)
        and (p.get("role") in (ROLE_WEREWOLF, ROLE_WOLF_KING, ROLE_WHITE_WOLF_KING, ROLE_WOLF_BEAUTY)
             or (p.get("role") == ROLE_MECHANICAL_WOLF and p.get("copied_skill") == ROLE_WEREWOLF))
    ]
    if len(room["night_state"]["wolf_locks"]) >= len(alive_wolves):
        final_target = choose_final_wolf_target(room)
        room["night_state"]["wolf_kill_target"] = final_target
        kill_player(room, final_target, "wolf")
        lock_current_role(room, user_id, {"target_id": final_target, "group": True})
        advance_night_role(room)
        return True, "All wolves locked. Wolf kill target selected."
    return True, "Wolf target locked. Waiting for other wolves."


def wolf_beauty_skill(room, user_id, target_id):
    target = room["players"].get(target_id)
    if target is None:
        return False, "Target player does not exist."
    for player in room["players"].values():
        if player.get("charmed_by") == user_id:
            player["charmed_by"] = None
            player["charmed_by_wolf_beauty"] = False
    target["charmed_by_wolf_beauty"] = True
    target["charmed_by"] = user_id
    lock_current_role(room, user_id, {"target_id": target_id})
    advance_night_role(room)
    return True, f"{target['name']} was charmed."


def witch_skill(room, user_id, option, target_id):
    witch = room["players"][user_id]
    wolf_target = room["night_state"].get("wolf_kill_target")
    if option == "antidote":
        if witch["skill_used"].get("antidote_used"):
            return False, "Antidote has already been used."
        if not wolf_target:
            return False, "No wolf target to save."
        witch["skill_used"]["antidote_used"] = True
        ok, message = add_revive_status(room, wolf_target, "witch_antidote")
    elif option == "poison":
        if witch["skill_used"].get("poison_used"):
            return False, "Poison has already been used."
        witch["skill_used"]["poison_used"] = True
        ok, message = kill_player(room, target_id, "witch_poison")
    else:
        return False, "Choose poison or antidote."
    if ok:
        lock_current_role(room, user_id, {"target_id": target_id, "option": option})
        advance_night_role(room)
    return ok, message


def mechanical_wolf_skill(room, user_id, target_id):
    mechanical = room["players"][user_id]
    if not mechanical["skill_used"].get("copy_used"):
        target = room["players"].get(target_id)
        if target is None:
            return False, "Target player does not exist."
        copied_role = target.get("role")
        mechanical["copied_role"] = copied_role
        mechanical["copied_skill"] = copied_role if copied_role in (ROLE_GUARD, ROLE_SEER, ROLE_WITCH, ROLE_HUNTER, ROLE_WEREWOLF) else None
        mechanical["skill_used"]["copy_used"] = True
        room["night_state"]["mechanical_wolf_copied"][user_id] = mechanical["copied_skill"]
        lock_current_role(room, user_id, {"target_id": target_id, "copied_skill": mechanical["copied_skill"]})
        advance_night_role(room)
        return True, f"Copied {copied_role}."
    copied_skill = mechanical.get("copied_skill")
    if copied_skill == ROLE_GUARD and not mechanical["skill_used"].get("copied_guard_used"):
        mechanical["skill_used"]["copied_guard_used"] = True
        ok, message = add_revive_status(room, target_id, "mechanical_guard")
    elif copied_skill == ROLE_SEER:
        result = get_seer_result(room, target_id)
        room["night_state"]["results"][user_id] = result
        ok, message = True, result["message"]
    elif copied_skill == ROLE_WITCH and not mechanical["skill_used"].get("copied_witch_poison_used"):
        mechanical["skill_used"]["copied_witch_poison_used"] = True
        ok, message = kill_player(room, target_id, "mechanical_witch_poison")
    elif copied_skill == ROLE_WEREWOLF or can_mechanical_wolf_kill(room, user_id):
        ok, message = kill_player(room, target_id, "mechanical_wolf")
    else:
        return False, "No copied mechanical wolf skill is available."
    if ok:
        lock_current_role(room, user_id, {"target_id": target_id, "copied_skill": copied_skill})
        advance_night_role(room)
    return ok, message


def submit_day_skill(room, user_id, role_name, form):
    if room.get("phase") != "day":
        return False, "Not day phase."
    player = room["players"].get(user_id)
    target_id = form.get("target_id")
    option = form.get("option")
    if player is None or player.get("role") != role_name:
        return False, "Wrong player for this skill."
    if role_name == ROLE_HUNTER:
        if is_last_god(room, user_id):
            return False, "Last god cannot use hunter skill."
        player["skill_used"]["death_skill_used"] = True
        ok, message = kill_player(room, target_id, "hunter")
    elif role_name in (ROLE_WOLF_KING, ROLE_WHITE_WOLF_KING):
        if is_last_wolf(room, user_id):
            return False, "Last wolf cannot use death skill."
        player["skill_used"]["death_skill_used"] = True
        ok, message = kill_player(room, target_id, role_name)
    elif role_name == ROLE_KNIGHT:
        if player["skill_used"].get("challenge_used"):
            return False, "Knight skill has already been used."
        player["skill_used"]["challenge_used"] = True
        if option == "success":
            from night_phase import init_night_phase
            init_night_phase(room)
            return True, "Knight succeeded. Going to night phase."
        ok, message = kill_player(room, user_id, "knight_fail")
    elif role_name == ROLE_MECHANICAL_WOLF and player.get("copied_skill") == ROLE_HUNTER:
        player["skill_used"]["copied_death_skill_used"] = True
        ok, message = kill_player(room, target_id, "mechanical_hunter")
    else:
        return False, "No day skill is available."
    check_win_condition(room)
    return ok, message


def get_player_name(room, user_id):
    if user_id is None:
        return "None"
    player = room["players"].get(user_id)
    if player is None:
        return "Unknown"
    return player["name"]
