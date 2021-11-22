from flask import Flask
from flask_mysqldb import MySQL
from config import Config
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
db = MySQL(app)
app.config.from_object(Config)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
CORS(app)


if __name__ == '__main__':
    socketio.run(app, debug=True)

from app import routes