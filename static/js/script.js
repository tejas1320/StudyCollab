console.log("AI Study Planner loaded successfully.");


// ==========================================
// AUTO HIDE FLASH MESSAGES
// ==========================================

setTimeout(() => {

    const alerts = document.querySelectorAll(
        ".alert"
    );

    alerts.forEach((alert) => {

        if (
            !alert.classList.contains("alert-info")
        ) {

            alert.style.transition =
                "opacity 0.5s";

            alert.style.opacity = "0";

            setTimeout(() => {

                alert.remove();

            }, 500);

        }

    });

}, 4000);


// ==========================================
// EXAM COUNTDOWN
// ==========================================

function updateExamCountdowns() {

    const examCards = document.querySelectorAll(
        "[data-exam-date]"
    );

    const today = new Date();

    today.setHours(
        0,
        0,
        0,
        0
    );


    examCards.forEach((card) => {

        const examDateString =
            card.getAttribute(
                "data-exam-date"
            );

        const examDate =
            new Date(
                examDateString + "T00:00:00"
            );

        const difference =
            examDate.getTime()
            - today.getTime();

        const daysRemaining =
            Math.ceil(
                difference /
                (1000 * 60 * 60 * 24)
            );


        const display =
            card.querySelector(
                ".days-remaining"
            );


        if (!display) {
            return;
        }


        if (daysRemaining < 0) {

            display.textContent =
                "Exam completed";

            card.classList.remove(
                "alert-info"
            );

            card.classList.add(
                "alert-secondary"
            );

        }
        else if (daysRemaining === 0) {

            display.textContent =
                "🔴 Exam is today!";

            card.classList.remove(
                "alert-info"
            );

            card.classList.add(
                "alert-danger"
            );

        }
        else if (daysRemaining <= 3) {

            display.textContent =
                "🔴 " +
                daysRemaining +
                " day(s) remaining";

            card.classList.remove(
                "alert-info"
            );

            card.classList.add(
                "alert-danger"
            );

        }
        else if (daysRemaining <= 7) {

            display.textContent =
                "🟠 " +
                daysRemaining +
                " day(s) remaining";

            card.classList.remove(
                "alert-info"
            );

            card.classList.add(
                "alert-warning"
            );

        }
        else {

            display.textContent =
                "🟢 " +
                daysRemaining +
                " day(s) remaining";

        }

    });

}


updateExamCountdowns();