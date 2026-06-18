import os
from datetime import date
from flask import Flask, request, jsonify, render_template
from parser import parse_dsl_lines, schedule_tasks, DSLSyntaxError, PERSONAS, register_custom_persona

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/schedule", methods=["POST"])
def get_schedule():
    data = request.get_json() or {}
    dsl_content = data.get("dsl_content", "")
    start_date = data.get("start_date", "")
    persona_override = data.get("persona_override", "")

    if not dsl_content.strip():
        return jsonify({"success": False, "error_type": "ValidationError", "message": "DSL content cannot be empty."}), 400

    if not start_date:
        start_date = "2026-06-18"

    try:
        lines = dsl_content.splitlines()
        persona, tasks = parse_dsl_lines(lines)

        if persona_override:
            persona_override = persona_override.upper()
            if persona_override.startswith("CUSTOM:"):
                try:
                    persona_override = register_custom_persona(persona_override)
                    persona = persona_override
                except ValueError:
                    pass
            elif persona_override in PERSONAS:
                persona = persona_override

        schedule, completed_tasks, warnings = schedule_tasks(persona, tasks, start_date)

        # Serialize schedule
        serialized_schedule = {}
        for day, sessions in schedule.items():
            day_str = day.strftime("%Y-%m-%d")
            # Grouping sessions by task names if consecutive to simplify rendering in frontend
            # sessions is sorted by hour in parser, but let's double check or group them in front-end JS.
            # We'll just pass raw sessions list to JS, and let JS render it.
            serialized_schedule[day_str] = [
                {
                    "hour_start": hr,
                    "hour_end": hr + 1,
                    "task_name": task_name,
                    "subject": subject,
                    "is_late": is_late
                }
                for hr, task_name, subject, is_late in sessions
            ]

        # Serialize completed tasks
        serialized_completed = []
        for task in completed_tasks:
            task_copy = task.copy()
            if "due_date" in task_copy and isinstance(task_copy["due_date"], date):
                task_copy["due_date"] = task_copy["due_date"].strftime("%Y-%m-%d")
            # Strip standard python date objects so they are JSON serializable
            serialized_completed.append(task_copy)

        return jsonify({
            "success": True,
            "persona": persona,
            "start_date": start_date,
            "schedule": serialized_schedule,
            "completed_tasks": serialized_completed,
            "warnings": warnings
        })

    except DSLSyntaxError as e:
        return jsonify({
            "success": False,
            "error_type": "SyntaxError",
            "message": str(e),
            "line_num": e.line_num
        }), 400
    except ValueError as e:
        return jsonify({
            "success": False,
            "error_type": "ValueError",
            "message": f"Validation/Value Error: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error_type": "Exception",
            "message": f"Server Error: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
