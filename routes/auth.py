from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models.database import mysql


auth = Blueprint(
    "auth",
    __name__
)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:

            flash(
                "All fields are required.",
                "danger"
            )

            return redirect("/register")

        cursor = mysql.connection.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()

            flash(
                "Email already registered.",
                "danger"
            )

            return redirect("/register")

        hashed_password = generate_password_hash(
            password
        )

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (
                name,
                email,
                hashed_password
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect("/login")

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


@auth.route("/logout")
def logout():

    session.clear()

    return redirect("/login")