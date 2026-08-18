from flask import Flask
from config import Config
from models.database import init_db

from routes.auth import auth
from routes.dashboard import dashboard


app = Flask(__name__)

app.config.from_object(Config)

init_db(app)

app.register_blueprint(auth)
app.register_blueprint(dashboard)


@app.route("/")
def home():

    from flask import redirect

    return redirect("/login")


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )