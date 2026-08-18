def calculate_priority(difficulty, preparation, days_until_exam):
    """
    Calculate study priority for a subject.
    Higher score means the subject needs more attention.
    """

    difficulty = float(difficulty)
    preparation = float(preparation)
    days_until_exam = int(days_until_exam)

    difficulty_score = (difficulty / 5.0) * 30.0

    weakness_score = ((100.0 - preparation) / 100.0) * 40.0

    if days_until_exam <= 3:
        urgency_score = 30.0
    elif days_until_exam <= 7:
        urgency_score = 25.0
    elif days_until_exam <= 14:
        urgency_score = 20.0
    elif days_until_exam <= 30:
        urgency_score = 15.0
    else:
        urgency_score = 10.0

    priority = (
        difficulty_score
        + weakness_score
        + urgency_score
    )

    return round(min(priority, 100.0), 2)


def generate_study_recommendation(
    subject_name,
    difficulty,
    preparation,
    days_until_exam
):

    priority = calculate_priority(
        difficulty,
        preparation,
        days_until_exam
    )

    if priority >= 75:
        recommendation = "High Priority"
    elif priority >= 50:
        recommendation = "Medium Priority"
    else:
        recommendation = "Low Priority"

    return {
        "subject": subject_name,
        "priority": priority,
        "recommendation": recommendation
    }


def calculate_recommended_minutes(priority):
    """
    Decide study duration based on priority.
    """

    priority = float(priority)

    if priority >= 85:
        return 90
    elif priority >= 75:
        return 75
    elif priority >= 60:
        return 60
    elif priority >= 45:
        return 45
    else:
        return 30


def generate_daily_plan(recommendations):
    """
    Generate today's AI study timetable.
    """

    sorted_subjects = sorted(
        recommendations,
        key=lambda x: float(x["priority"]),
        reverse=True
    )

    daily_plan = []

    time_slots = [
        "08:00 AM",
        "10:00 AM",
        "02:00 PM",
        "04:00 PM",
        "07:00 PM"
    ]

    for index, subject in enumerate(sorted_subjects):

        if index >= len(time_slots):
            break

        minutes = calculate_recommended_minutes(
            subject["priority"]
        )

        preparation = float(
            subject["preparation"]
        )

        difficulty = float(
            subject["difficulty"]
        )

        days_until_exam = int(
            subject["days_until_exam"]
        )

        if preparation < 50:
            focus = (
                "Revise weak areas and important concepts."
            )

        elif difficulty >= 4:
            focus = (
                "Practice difficult concepts and solve questions."
            )

        elif days_until_exam <= 7:
            focus = (
                "Practice previous questions and revise."
            )

        else:
            focus = (
                "Study new topics and revise previous topics."
            )

        daily_plan.append({
            "time": time_slots[index],
            "subject": subject["subject"],
            "minutes": minutes,
            "focus": focus,
            "priority": subject["priority"]
        })

    return daily_plan