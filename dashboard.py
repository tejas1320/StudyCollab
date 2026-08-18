from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash
)

from models.database import mysql


dashboard = Blueprint(
    "dashboard",
    __name__
)


# =========================
# DASHBOARD
# =========================

@dashboard.route("/dashboard")
def index():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cursor = mysql.connection.cursor()

    # Count subjects
    cursor.execute(
        """
        SELECT COUNT(*) AS subject_count
        FROM subjects
        WHERE user_id = %s
        """,
        (user_id,)
    )

    subject_data = cursor.fetchone()

    # Calculate total study hours
    cursor.execute(
        """
        SELECT COALESCE(
            SUM(duration_minutes),
            0
        ) AS total_minutes
        FROM study_sessions
        WHERE user_id = %s
        """,
        (user_id,)
    )

    study_data = cursor.fetchone()

    cursor.close()

    total_hours = round(
        study_data["total_minutes"] / 60,
        2
    )

    return render_template(
        "dashboard.html",
        subject_count=subject_data["subject_count"],
        total_hours=total_hours
    )


# =========================
# SUBJECT LIST
# =========================

@dashboard.route("/subjects")
def subjects():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        SELECT
            subject_id,
            subject_name,
            difficulty,
            preparation_percentage
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_list = cursor.fetchall()

    cursor.close()

    return render_template(
        "subjects.html",
        subjects=subjects_list
    )


# =========================
# ADD SUBJECT
# =========================

@dashboard.route(
    "/subjects/add",
    methods=["GET", "POST"]
)
def add_subject():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        subject_name = request.form.get(
            "subject_name"
        )

        difficulty = request.form.get(
            "difficulty"
        )

        preparation = request.form.get(
            "preparation"
        )

        # Basic validation

        if not subject_name:
            flash(
                "Subject name is required.",
                "danger"
            )

            return redirect("/subjects/add")

        try:

            difficulty = int(difficulty)
            preparation = float(preparation)

        except (TypeError, ValueError):

            flash(
                "Please enter valid numbers.",
                "danger"
            )

            return redirect("/subjects/add")

        if difficulty < 1 or difficulty > 5:

            flash(
                "Difficulty must be between 1 and 5.",
                "danger"
            )

            return redirect("/subjects/add")

        if preparation < 0 or preparation > 100:

            flash(
                "Preparation must be between 0 and 100.",
                "danger"
            )

            return redirect("/subjects/add")

        user_id = session["user_id"]

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            INSERT INTO subjects
            (
                user_id,
                subject_name,
                difficulty,
                preparation_percentage
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                subject_name,
                difficulty,
                preparation
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Subject added successfully!",
            "success"
        )

        return redirect("/subjects")

    return render_template(
        "add_subject.html"
    )


# =========================
# DELETE SUBJECT
# =========================

@dashboard.route(
    "/subjects/delete/<int:subject_id>",
    methods=["POST"]
)
def delete_subject(subject_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cursor = mysql.connection.cursor()

    # Delete only if subject belongs
    # to the logged-in user

    cursor.execute(
        """
        DELETE FROM subjects
        WHERE subject_id = %s
        AND user_id = %s
        """,
        (
            subject_id,
            user_id
        )
    )

    mysql.connection.commit()

    cursor.close()

    flash(
        "Subject deleted successfully.",
        "success"
    )

    return redirect("/subjects")