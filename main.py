# Start by creating basic flask web server
# We are gonna use socket which is a live way of communicating rather than refreshing the page and saving in databases
# So we are storing the messages in RAM, so once exited the data is gone

from flask import Flask, request, render_template, session, redirect, url_for
from flask_socketio import SocketIO, send, leave_room, join_room
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = 'fjoierjfoiejio'
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code

# We'll make two routes: Homepage and room page
# using decorator syntax @ we create different route
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(6)
            rooms[room] = {"members" : 0, "messages" : []}
        elif code not in rooms:
            return render_template("home.html", error="Code does not exist.", code=code, name=name)
        # A session a semi-permanent way to store the information of a user
        # A session is a temporary data stored on a server
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    # Make it so that you can't enter a room unless you have done your registration
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    # This room.html contains the chat room code
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
# todo:  If you want to know the date of the message when it was actually sent you have to do here on the server
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return 
    
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} left the room {room}")

if __name__ == "__main__":
    # debug= True means that any change we make to our server that does not break any of the code will automatically refresh
    socketio.run(app, debug=True)