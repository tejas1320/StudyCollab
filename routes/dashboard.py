from datetime import date, datetime, timedelta

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from models.database import mysql

from ai.planner import (
    generate_study_recommendation,
    generate_daily_plan
)


# ============================================================
# BLUEPRINT
# ============================================================

dashboard = Blueprint("dashboard", __name__)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_id():
    """
    Get the currently logged-in user's ID.
    """

    return session.get("user_id")


def login_required():
    """
    Check whether a user is logged in.
    """

    return get_user_id() is not None


def get_db_cursor():
    """
    Return a MySQL cursor.

    Your models/database.py already configures:
        MYSQL_CURSORCLASS = "DictCursor"

    Therefore rows are returned as dictionaries.
    """

    return mysql.connection.cursor()


# ============================================================
# DASHBOARD
# ============================================================

@dashboard.route("/dashboard")
def dashboard_home():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    conn = mysql.connection
    cursor = get_db_cursor()

    # --------------------------------------------------------
    # Subjects
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects = cursor.fetchall()

    # --------------------------------------------------------
    # Exams
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            e.*,
            s.subject_name
        FROM exams e
        LEFT JOIN subjects s
            ON e.subject_id = s.subject_id
        WHERE e.user_id = %s
        ORDER BY e.exam_date ASC
        """,
        (user_id,)
    )

    exams = cursor.fetchall()

    # --------------------------------------------------------
    # Study Sessions
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            ss.*,
            s.subject_name
        FROM study_sessions ss
        LEFT JOIN subjects s
            ON ss.subject_id = s.subject_id
        WHERE ss.user_id = %s
        ORDER BY ss.study_date DESC
        """,
        (user_id,)
    )

    study_sessions = cursor.fetchall()

    # --------------------------------------------------------
    # Goals
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id = %s
        ORDER BY target_date ASC
        """,
        (user_id,)
    )

    goals = cursor.fetchall()

    cursor.close()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_subjects = len(subjects)
    total_exams = len(exams)
    total_sessions = len(study_sessions)
    total_goals = len(goals)

    total_study_minutes = sum(
        int(s.get("duration", 0) or 0)
        for s in study_sessions
    )

    total_study_hours = round(
        total_study_minutes / 60,
        1
    )

    completed_goals = sum(
        1
        for g in goals
        if g.get("status") == "Completed"
    )

    # --------------------------------------------------------
    # Render dashboard
    # --------------------------------------------------------

    return render_template(
        "dashboard.html",
        subjects=subjects,
        exams=exams,
        study_sessions=study_sessions,
        goals=goals,
        total_subjects=total_subjects,
        total_exams=total_exams,
        total_sessions=total_sessions,
        total_goals=total_goals,
        total_study_minutes=total_study_minutes,
        total_study_hours=total_study_hours,
        completed_goals=completed_goals
    )


# ============================================================
# SUBJECTS
# ============================================================

@dashboard.route("/subjects")
def subjects():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "subjects.html",
        subjects=subjects_data
    )


# ============================================================
# ADD SUBJECT
# ============================================================

@dashboard.route("/subjects/add", methods=["GET", "POST"])
def add_subject():

    if not login_required():
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        user_id = get_user_id()

        subject_name = request.form.get(
            "subject_name",
            ""
        ).strip()

        difficulty = request.form.get(
            "difficulty",
            3
        )

        try:
            difficulty = float(difficulty)
        except ValueError:
            difficulty = 3

        if not subject_name:

            flash(
                "Subject name is required.",
                "error"
            )

            return redirect(
                url_for("dashboard.add_subject")
            )

        cursor = get_db_cursor()

        cursor.execute(
            """
            INSERT INTO subjects
                (user_id, subject_name, difficulty)
            VALUES
                (%s, %s, %s)
            """,
            (
                user_id,
                subject_name,
                difficulty
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Subject added successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.subjects")
        )

    return render_template(
        "add_subject.html"
    )


# ============================================================
# DELETE SUBJECT
# ============================================================

@dashboard.route("/subjects/delete/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

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

    return redirect(
        url_for("dashboard.subjects")
    )
# ============================================================
# TOPICS
# ============================================================

@dashboard.route("/subjects/<int:subject_id>/topics")
def subject_topics(subject_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    # Check that the subject belongs to the logged-in user
    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE subject_id = %s
        AND user_id = %s
        """,
        (subject_id, user_id)
    )

    subject = cursor.fetchone()

    if not subject:
        cursor.close()
        return "Subject not found", 404

    # Get topics for this subject
    cursor.execute(
        """
        SELECT *
        FROM topics
        WHERE subject_id = %s
        ORDER BY topic_name
        """,
        (subject_id,)
    )

    topics = cursor.fetchall()

    cursor.close()

    return render_template(
        "topics.html",
        subject=subject,
        topics=topics
    )

# ============================================================
# EXAMS
# ============================================================

@dashboard.route("/exams")
def exams():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT
            e.*,
            s.subject_name
        FROM exams e
        LEFT JOIN subjects s
            ON e.subject_id = s.subject_id
        WHERE e.user_id = %s
        ORDER BY e.exam_date ASC
        """,
        (user_id,)
    )

    exams_data = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "exams.html",
        exams=exams_data,
        subjects=subjects_data
    )


# ============================================================
# ADD EXAM
# ============================================================

@dashboard.route("/exams/add", methods=["GET", "POST"])
def add_exam():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    if request.method == "POST":

        subject_id = request.form.get(
            "subject_id"
        )

        exam_name = request.form.get(
            "exam_name",
            ""
        ).strip()

        exam_date = request.form.get(
            "exam_date"
        )

        if not subject_id or not exam_name or not exam_date:

            flash(
                "Please fill all exam details.",
                "error"
            )

            return redirect(
                url_for("dashboard.add_exam")
            )

        cursor = get_db_cursor()

        cursor.execute(
            """
            INSERT INTO exams
                (
                    user_id,
                    subject_id,
                    exam_name,
                    exam_date
                )
            VALUES
                (%s, %s, %s, %s)
            """,
            (
                user_id,
                subject_id,
                exam_name,
                exam_date
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Exam added successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.exams")
        )

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "add_exam.html",
        subjects=subjects_data
    )


# ============================================================
# DELETE EXAM
# ============================================================

@dashboard.route("/exams/delete/<int:exam_id>", methods=["POST"])
def delete_exam(exam_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        DELETE FROM exams
        WHERE exam_id = %s
        AND user_id = %s
        """,
        (
            exam_id,
            user_id
        )
    )

    mysql.connection.commit()

    cursor.close()

    flash(
        "Exam deleted successfully.",
        "success"
    )

    return redirect(
        url_for("dashboard.exams")
    )


# ============================================================
# STUDY SESSION FORM
# ============================================================

@dashboard.route("/study-session", methods=["GET", "POST"])
def study_session():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    if request.method == "POST":

        subject_id = request.form.get(
            "subject_id"
        )

        study_date = request.form.get(
            "study_date"
        )

        duration = request.form.get(
            "duration"
        )

        topics_completed = request.form.get(
            "topics_completed",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if not subject_id:
            flash(
                "Please select a subject.",
                "error"
            )

            return redirect(
                url_for("dashboard.study_session")
            )

        if not duration:

            flash(
                "Please enter study duration.",
                "error"
            )

            return redirect(
                url_for("dashboard.study_session")
            )

        try:
            duration = int(duration)
        except ValueError:

            flash(
                "Duration must be a number.",
                "error"
            )

            return redirect(
                url_for("dashboard.study_session")
            )

        if not study_date:
            study_date = date.today()

        cursor = get_db_cursor()

        cursor.execute(
            """
            INSERT INTO study_sessions
                (
                    user_id,
                    subject_id,
                    study_date,
                    duration,
                    topics_completed,
                    notes
                )
            VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                subject_id,
                study_date,
                duration,
                topics_completed,
                notes
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Study session recorded successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.study_sessions")
        )

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "study_session.html",
        subjects=subjects_data,
        today=date.today().isoformat()
    )


# ============================================================
# STUDY SESSIONS LIST
# ============================================================

@dashboard.route("/study-sessions")
def study_sessions():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT
            ss.*,
            s.subject_name
        FROM study_sessions ss
        LEFT JOIN subjects s
            ON ss.subject_id = s.subject_id
        WHERE ss.user_id = %s
        ORDER BY ss.study_date DESC, ss.session_id DESC
        """,
        (user_id,)
    )

    sessions_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "study_sessions.html",
        study_sessions=sessions_data,
        sessions=sessions_data
    )


# ============================================================
# DELETE STUDY SESSION
# ============================================================

@dashboard.route(
    "/study-sessions/delete/<int:session_id>",
    methods=["POST"]
)
def delete_study_session(session_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        DELETE FROM study_sessions
        WHERE session_id = %s
        AND user_id = %s
        """,
        (
            session_id,
            user_id
        )
    )

    mysql.connection.commit()

    cursor.close()

    flash(
        "Study session deleted successfully.",
        "success"
    )

    return redirect(
        url_for("dashboard.study_sessions")
    )


# ============================================================
# GOALS
# ============================================================

@dashboard.route("/goals")
def goals():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id = %s
        ORDER BY target_date ASC
        """,
        (user_id,)
    )

    goals_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "goals.html",
        goals=goals_data
    )


# ============================================================
# ADD GOAL
# ============================================================

@dashboard.route("/goals/add", methods=["GET", "POST"])
def add_goal():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    if request.method == "POST":

        goal_name = request.form.get(
            "goal_name",
            ""
        ).strip()

        target_date = request.form.get(
            "target_date"
        )

        progress = request.form.get(
            "progress",
            0
        )

        if not goal_name:

            flash(
                "Goal name is required.",
                "error"
            )

            return redirect(
                url_for("dashboard.add_goal")
            )

        if not target_date:

            flash(
                "Target date is required.",
                "error"
            )

            return redirect(
                url_for("dashboard.add_goal")
            )

        try:
            progress = float(progress)
        except ValueError:
            progress = 0

        progress = max(
            0,
            min(100, progress)
        )

        status = (
            "Completed"
            if progress >= 100
            else "Pending"
        )

        cursor = get_db_cursor()

        cursor.execute(
            """
            INSERT INTO goals
                (
                    user_id,
                    goal_name,
                    target_date,
                    progress,
                    status
                )
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                goal_name,
                target_date,
                progress,
                status
            )
        )

        mysql.connection.commit()

        cursor.close()

        flash(
            "Goal created successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.goals")
        )

    return render_template(
        "add_goal.html"
    )


# ============================================================
# UPDATE GOAL PROGRESS
# ============================================================

@dashboard.route(
    "/goals/update/<int:goal_id>",
    methods=["POST"]
)
def update_goal(goal_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    progress = request.form.get(
        "progress",
        0
    )

    try:
        progress = float(progress)
    except ValueError:
        progress = 0

    progress = max(
        0,
        min(100, progress)
    )

    status = (
        "Completed"
        if progress >= 100
        else "Pending"
    )

    cursor = get_db_cursor()

    cursor.execute(
        """
        UPDATE goals
        SET
            progress = %s,
            status = %s
        WHERE goal_id = %s
        AND user_id = %s
        """,
        (
            progress,
            status,
            goal_id,
            user_id
        )
    )

    mysql.connection.commit()

    cursor.close()

    flash(
        "Goal progress updated successfully.",
        "success"
    )

    return redirect(
        url_for("dashboard.goals")
    )


# ============================================================
# DELETE GOAL
# ============================================================

@dashboard.route(
    "/goals/delete/<int:goal_id>",
    methods=["POST"]
)
def delete_goal(goal_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        DELETE FROM goals
        WHERE goal_id = %s
        AND user_id = %s
        """,
        (
            goal_id,
            user_id
        )
    )

    mysql.connection.commit()

    cursor.close()

    flash(
        "Goal deleted successfully.",
        "success"
    )

    return redirect(
        url_for("dashboard.goals")
    )


# ============================================================
# AI STUDY PLANNER
# ============================================================



@dashboard.route("/ai-planner")
def ai_planner():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    # --------------------------------------------------------
    # Get subjects
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_data = cursor.fetchall()

    # --------------------------------------------------------
    # Get exams
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            e.*,
            s.subject_name
        FROM exams e
        LEFT JOIN subjects s
            ON e.subject_id = s.subject_id
        WHERE e.user_id = %s
        ORDER BY e.exam_date ASC
        """,
        (user_id,)
    )

    exams_data = cursor.fetchall()

    cursor.close()

    # --------------------------------------------------------
    # Generate recommendations
    # --------------------------------------------------------

    recommendations = []

    today = date.today()

    for subject in subjects_data:

        subject_id = subject.get("subject_id")
        subject_name = subject.get("subject_name", "Unknown Subject")

        # Get difficulty
        difficulty = float(
            subject.get("difficulty", 3)
            or 3
        )

        # Get preparation
        preparation = float(
            subject.get("preparation", 0)
            or 0
        )

        # ----------------------------------------------------
        # Find nearest upcoming exam for this subject
        # ----------------------------------------------------

        days_until_exam = 999

        for exam in exams_data:

            if exam.get("subject_id") == subject_id:

                exam_date = exam.get("exam_date")

                if exam_date:

                    try:

                        if isinstance(exam_date, str):
                            exam_date = datetime.strptime(
                                exam_date,
                                "%Y-%m-%d"
                            ).date()

                        exam_days = (
                            exam_date - today
                        ).days

                        if exam_days >= 0:
                            days_until_exam = min(
                                days_until_exam,
                                exam_days
                            )

                    except Exception:
                        pass

        # ----------------------------------------------------
        # Generate AI recommendation
        # ----------------------------------------------------

        recommendation = generate_study_recommendation(
            subject_name,
            difficulty,
            preparation,
            days_until_exam
        )

        # Add information required by the template
        recommendation["difficulty"] = difficulty
        recommendation["preparation"] = preparation
        recommendation["days_until_exam"] = days_until_exam

        recommendations.append(
            recommendation
        )

    # --------------------------------------------------------
    # Generate today's study plan
    # --------------------------------------------------------

    daily_plan = generate_daily_plan(
        recommendations
    )

    # --------------------------------------------------------
    # Calculate total recommended minutes
    # --------------------------------------------------------

    total_minutes = sum(
        int(item.get("minutes", 0) or 0)
        for item in daily_plan
    )

    # --------------------------------------------------------
    # Render AI planner
    # --------------------------------------------------------

    return render_template(
        "ai_planner.html",

        subjects=subjects_data,

        exams=exams_data,

        recommendations=recommendations,

        daily_plan=daily_plan,

        total_minutes=total_minutes
    )

# ============================================================
# AI RECOMMENDATION FOR SUBJECT
# ============================================================

@dashboard.route(
    "/ai-planner/recommend/<int:subject_id>"
)
def ai_recommend(subject_id):

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    # --------------------------------------------------------
    # Subject
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE subject_id = %s
        AND user_id = %s
        """,
        (
            subject_id,
            user_id
        )
    )

    subject = cursor.fetchone()

    if not subject:

        cursor.close()

        flash(
            "Subject not found.",
            "error"
        )

        return redirect(
            url_for("dashboard.ai_planner")
        )

    # --------------------------------------------------------
    # Topics
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM topics
        WHERE subject_id = %s
        ORDER BY topic_name
        """,
        (subject_id,)
    )

    topics_data = cursor.fetchall()

    # --------------------------------------------------------
    # Exams
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM exams
        WHERE subject_id = %s
        AND user_id = %s
        ORDER BY exam_date ASC
        """,
        (
            subject_id,
            user_id
        )
    )

    exams_data = cursor.fetchall()

    # --------------------------------------------------------
    # Study sessions
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM study_sessions
        WHERE subject_id = %s
        AND user_id = %s
        ORDER BY study_date DESC
        """,
        (
            subject_id,
            user_id
        )
    )

    sessions_data = cursor.fetchall()

    cursor.close()

    # --------------------------------------------------------
    # Generate recommendation
    # --------------------------------------------------------

    recommendation = None

    try:

        recommendation = generate_study_recommendation(
            subject=subject,
            topics=topics_data,
            exams=exams_data,
            study_sessions=sessions_data
        )

    except TypeError:

        try:

            recommendation = generate_study_recommendation(
                subject,
                topics_data,
                exams_data,
                sessions_data
            )

        except Exception:

            recommendation = None

    except Exception:

        recommendation = None

    return render_template(
        "ai_recommendation.html",
        subject=subject,
        topics=topics_data,
        exams=exams_data,
        study_sessions=sessions_data,
        recommendation=recommendation
    )


# ============================================================
# AI DAILY PLAN
# ============================================================

@dashboard.route(
    "/ai-planner/generate",
    methods=["POST"]
)
def generate_ai_plan():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    # --------------------------------------------------------
    # Subjects
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT *
        FROM subjects
        WHERE user_id = %s
        ORDER BY subject_name
        """,
        (user_id,)
    )

    subjects_data = cursor.fetchall()

    # --------------------------------------------------------
    # Exams
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            e.*,
            s.subject_name
        FROM exams e
        LEFT JOIN subjects s
            ON e.subject_id = s.subject_id
        WHERE e.user_id = %s
        ORDER BY e.exam_date ASC
        """,
        (user_id,)
    )

    exams_data = cursor.fetchall()

    # --------------------------------------------------------
    # Topics
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            t.*,
            s.subject_name
        FROM topics t
        LEFT JOIN subjects s
            ON t.subject_id = s.subject_id
        WHERE s.user_id = %s
        ORDER BY s.subject_name
        """,
        (user_id,)
    )

    topics_data = cursor.fetchall()

    # --------------------------------------------------------
    # Sessions
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            ss.*,
            s.subject_name
        FROM study_sessions ss
        LEFT JOIN subjects s
            ON ss.subject_id = s.subject_id
        WHERE ss.user_id = %s
        ORDER BY ss.study_date DESC
        """,
        (user_id,)
    )

    sessions_data = cursor.fetchall()

    cursor.close()

    # --------------------------------------------------------
    # Generate plan
    # --------------------------------------------------------

    try:

        daily_plan = generate_daily_plan(
            subjects=subjects_data,
            exams=exams_data,
            topics=topics_data,
            study_sessions=sessions_data
        )

    except TypeError:

        try:

            daily_plan = generate_daily_plan(
                subjects_data,
                exams_data,
                topics_data,
                sessions_data
            )

        except Exception:

            daily_plan = []

    except Exception:

        daily_plan = []

    return render_template(
        "ai_planner.html",
        subjects=subjects_data,
        exams=exams_data,
        topics=topics_data,
        study_sessions=sessions_data,
        daily_plan=daily_plan
    )


# ============================================================
# TOPICS
# ============================================================

@dashboard.route("/topics")
def all_topics():

    if not login_required():
        return redirect(url_for("auth.login"))

    user_id = get_user_id()

    cursor = get_db_cursor()

    cursor.execute(
        """
        SELECT
            t.*,
            s.subject_name
        FROM topics t
        LEFT JOIN subjects s
            ON t.subject_id = s.subject_id
        WHERE s.user_id = %s
        ORDER BY s.subject_name, t.topic_name
        """,
        (user_id,)
    )

    topics_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "topics.html",
        topics=topics_data
    )


# ============================================================
# 404 / SAFE ROUTE
# ============================================================

@dashboard.route("/")
def home():

    if login_required():
        return redirect(
            url_for("dashboard.dashboard_home")
        )

    return redirect(
        url_for("auth.login")
    )