from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from main.game_roles import get_role_definitions, get_role_image_filename
from main.game_state import (
    assign_roles as assign_room_roles,
    clean_role_counts,
    create_player,
    create_room as create_game_room,
    get_room,
    is_host,
    resolve_day_deaths,
    start_day,
    start_game,
    validate_role_counts,
)
from main.night_phase import get_current_night_info, init_night_phase, lock_night_action
from main.skills import get_skill_context, submit_day_skill, submit_night_skill

app = Flask(__name__)
app.secret_key = "my_werewolf_secret_key_123"


def current_room_and_player():
    room = get_room(session.get("room_id"))
    user_id = session.get("user_id")
    if room is None or user_id not in room["players"]:
        return None, None
    return room, room["players"][user_id]


@app.route("/")
def home():
    return render_template("enter_room.html", room_id="")


@app.route("/create_room", methods=["GET", "POST"])
def create_room_route():
    room = create_game_room()
    session.clear()
    return redirect(url_for("enter_room", room_id=room["room_id"]))


@app.route("/enter_room")
def enter_room():
    return render_template("enter_room.html", room_id=request.args.get("room_id", ""))


@app.route("/join_room", methods=["POST"])
def join_room():
    room_id = request.form.get("room_id")
    name = request.form.get("name", "").strip()
    room = get_room(room_id)
    if room is None:
        return render_template("enter_room.html", room_id=room_id or "", error="Room does not exist.")
    if not name:
        return render_template("enter_room.html", room_id=room_id or "", error="Please enter your name.")
    player = create_player(room, name)
    session.clear()
    session["room_id"] = room["room_id"]
    session["user_id"] = player["user_id"]
    return redirect(url_for("room_page"))


@app.route("/room")
def room_page():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    return render_template(
        "room.html",
        room=room,
        room_id=room["room_id"],
        player=player,
        players=room["players"],
        roles_assigned=room["status"] in ("roles_assigned", "started"),
        game_started=room["status"] == "started",
        is_host=is_host(room, player["user_id"]),
    )


@app.route("/role_options", methods=["GET", "POST"])
def role_options():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    if not is_host(room, player["user_id"]):
        return "Only the room host can choose role options.", 403
    if room["status"] == "started":
        return redirect(url_for("room_page"))
    if request.method == "POST":
        room["selected_role_counts"] = clean_role_counts(request.form)
        return redirect(url_for("role_options"))
    return render_template(
        "role_options.html",
        room_id=room["room_id"],
        player_count=len(room["players"]),
        roles=get_role_definitions(),
        role_counts=room.get("selected_role_counts", {}),
    )


@app.route("/validate_roles", methods=["POST"])
def validate_roles_route():
    room, _player = current_room_and_player()
    if room is None:
        return jsonify({"success": False, "message": "You are not in a room."}), 400
    role_counts = clean_role_counts(request.get_json(silent=True) or {})
    valid, message, selected_count, player_count = validate_role_counts(room, role_counts)
    return jsonify(
        {
            "success": valid,
            "message": message,
            "selected_count": selected_count,
            "player_count": player_count,
        }
    )


@app.route("/assign_roles", methods=["POST"])
def assign_roles():
    room, player = current_room_and_player()
    if room is None:
        return jsonify({"success": False, "message": "You are not in a room."}), 400
    if not is_host(room, player["user_id"]):
        return jsonify({"success": False, "message": "Only the host can assign roles."}), 403
    if room["status"] == "started":
        return jsonify({"success": False, "message": "The game has already started."}), 400
    success, message, selected_count, player_count = assign_room_roles(room, request.get_json(silent=True) or {})
    return jsonify(
        {
            "success": success,
            "message": message,
            "selected_count": selected_count,
            "player_count": player_count,
        }
    )


@app.route("/start_game", methods=["POST"])
def start_game_route():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    if not is_host(room, player["user_id"]):
        return "Only the host can start the game.", 403
    success, _message = start_game(room)
    if not success:
        return redirect(url_for("room_page"))
    init_night_phase(room)
    return redirect(url_for("skill_page"))


@app.route("/my_role")
@app.route("/role")
def my_role():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    if player["role"] is None:
        return "Roles have not been assigned yet."
    return render_template(
        "role.html",
        room=room,
        player=player,
        role_image_filename=get_role_image_filename(player["role"]),
        is_host=is_host(room, player["user_id"]),
    )


@app.route("/start_night", methods=["POST"])
def start_night():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    if not is_host(room, player["user_id"]):
        return "Only the host can start the night phase.", 403
    if room["status"] != "started":
        return redirect(url_for("room_page"))
    init_night_phase(room)
    return redirect(url_for("skill_page"))


@app.route("/skill")
def skill_page():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    return render_template("skill.html", room=room, context=get_skill_context(room, player["user_id"]), players=room["players"])


@app.route("/skill/<role_name>", methods=["POST"])
def submit_skill(role_name):
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    success, message = submit_night_skill(room, player["user_id"], role_name, request.form)
    return redirect(url_for("skill_page", message=message, success=int(success)))


@app.route("/day/skill/<role_name>", methods=["POST"])
def submit_day_skill_route(role_name):
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    success, message = submit_day_skill(room, player["user_id"], role_name, request.form)
    return redirect(url_for("skill_page", message=message, success=int(success)))


@app.route("/next_phase", methods=["POST"])
def next_phase():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    if not is_host(room, player["user_id"]):
        return "Only the host can move phases.", 403
    next_phase_name = request.form.get("phase")
    if next_phase_name == "night":
        init_night_phase(room)
    elif next_phase_name == "day":
        start_day(room)
    elif next_phase_name == "resolve_day":
        resolve_day_deaths(room)
    elif next_phase_name == "voting":
        room["phase"] = "voting"
    return redirect(url_for("room_page"))


@app.route("/night")
def night_page():
    return redirect(url_for("skill_page"))


@app.route("/night_state")
def night_state():
    room, player = current_room_and_player()
    if room is None:
        return jsonify({"error": "not in room"}), 400
    return jsonify(get_current_night_info(room, player["user_id"]))


@app.route("/lock_night_action", methods=["POST"])
def lock_night_action_route():
    room, player = current_room_and_player()
    if room is None:
        return jsonify({"success": False, "message": "Not in room."}), 400
    action_data = {"target_id": request.form.get("target_id"), "skill": request.form.get("skill")}
    success, message = lock_night_action(room, player["user_id"], action_data)
    return jsonify({"success": success, "message": message})


@app.route("/day")
def day_page():
    room, player = current_room_and_player()
    if room is None:
        return redirect(url_for("home"))
    return render_template("day.html", room=room, player=player)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
