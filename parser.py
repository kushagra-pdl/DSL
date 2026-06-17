import sys
import os
from datetime import datetime, timedelta
# Default start date for scheduling (tomorrow relative to current conversation local time 2026-06-17)
DEFAULT_START_DATE = "2026-06-18"
# Persona hour definitions (24-hour format slots)
PERSONAS = {
    "NIGHT_OWL": [18, 19, 20, 21, 22, 23],
    "EARLY_BIRD": [6, 7, 8, 9, 10, 11],
    "BALANCED": [9, 10, 11, 14, 15, 16]
}
PRIORITY_ORDER = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1
}
def parse_dsl(filepath):
    """
    Parses the study planner DSL file.
    Returns:
        persona (str): The persona name or "BALANCED" if not specified.
        tasks (list): A list of parsed task dictionaries.
    """
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' does not exist.")
        sys.exit(1)
    persona = "BALANCED"
    tasks = []
    current_task = {}
    in_task = False
    with open(filepath, "r") as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            # Skip empty lines or comments starting with #
            if not line or line.startswith("#"):
                continue
            # Check for persona definition (must be outside task blocks)
            if line.startswith("PERSONA"):
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"Error on line {line_num}: PERSONA keyword requires a value.")
                    sys.exit(1)
                persona = parts[1].upper()
                if persona not in PERSONAS:
                    print(f"Warning on line {line_num}: Unknown persona '{persona}'. Defaulting to BALANCED.")
                    persona = "BALANCED"
                continue
            # Start of a task block
            if line.startswith("TASK"):
                if in_task:
                    print(f"Error on line {line_num}: Nested TASK block is not allowed.")
                    sys.exit(1)
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"Error on line {line_num}: TASK keyword requires a task name.")
                    sys.exit(1)
                current_task = {"name": parts[1]}
                in_task = True
                continue
            # End of a task block
            if line == "END":
                if not in_task:
                    print(f"Error on line {line_num}: END without starting a TASK.")
                    sys.exit(1)
                
                # Validate task completeness
                required_keys = ["SUBJECT", "DUE", "PRIORITY", "DURATION", "STATUS"]
                missing = [key for key in required_keys if key not in current_task]
                if missing:
                    print(f"Error on line {line_num}: Task '{current_task.get('name', 'UNKNOWN')}' is missing fields: {', '.join(missing)}")
                    sys.exit(1)
                
                # Parse DURATION (e.g. '3h' -> 3)
                duration_str = current_task["DURATION"]
                if duration_str.endswith("h"):
                    try:
                        current_task["duration_hours"] = int(duration_str[:-1])
                    except ValueError:
                        print(f"Error on line {line_num}: Invalid DURATION format '{duration_str}'. Must be an integer followed by 'h' (e.g., 3h).")
                        sys.exit(1)
                else:
                    print(f"Error on line {line_num}: DURATION must end with 'h' (e.g., 3h).")
                    sys.exit(1)
                # Validate PRIORITY
                priority = current_task["PRIORITY"].upper()
                if priority not in PRIORITY_ORDER:
                    print(f"Error on line {line_num}: Invalid PRIORITY '{priority}'. Must be HIGH, MEDIUM, or LOW.")
                    sys.exit(1)
                current_task["priority_val"] = PRIORITY_ORDER[priority]
                # Validate STATUS
                status = current_task["STATUS"].upper()
                if status not in ["PENDING", "COMPLETED"]:
                    print(f"Error on line {line_num}: Invalid STATUS '{status}'. Must be PENDING or COMPLETED.")
                    sys.exit(1)
                current_task["STATUS"] = status
                # Validate DUE date format
                due_date_str = current_task["DUE"]
                try:
                    current_task["due_date"] = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                except ValueError:
                    print(f"Error on line {line_num}: Invalid DUE date format '{due_date_str}'. Must be YYYY-MM-DD.")
                    sys.exit(1)
                tasks.append(current_task)
                current_task = {}
                in_task = False
                continue
            # Parse key-value pairs inside task block
            if in_task:
                parts = line.split(maxsplit=1)
                if len(parts) < 2:
                    print(f"Error on line {line_num}: Field '{parts[0]}' requires a value.")
                    sys.exit(1)
                key, value = parts[0].upper(), parts[1]
                current_task[key] = value
            else:
                print(f"Error on line {line_num}: Keyword '{line}' must be inside a TASK block.")
                sys.exit(1)
    if in_task:
        print("Error: Reached end of file without closing the last TASK block with END.")
        sys.exit(1)
    return persona, tasks
def schedule_tasks(persona, tasks, start_date_str):
    """
    Schedules pending tasks based on the persona's study windows, task priority, and deadlines.
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    preferred_hours = PERSONAS[persona]
    
    # Separate completed and pending tasks
    completed_tasks = [t for t in tasks if t["STATUS"] == "COMPLETED"]
    pending_tasks = [t for t in tasks if t["STATUS"] == "PENDING"]
    
    # Sort pending tasks:
    # 1. Higher priority first (HIGH > MEDIUM > LOW)
    # 2. Earlier due date first
    pending_tasks.sort(key=lambda t: (-t["priority_val"], t["due_date"]))
    
    # Calendar allocation: date -> list of (hour, task_name, subject)
    schedule = {}
    warnings = []
    
    # Track daily allocated hours to avoid double booking
    allocated_slots = {}  # (date, hour) -> task_ref
    
    for task in pending_tasks:
        hours_needed = task["duration_hours"]
        hours_scheduled = 0
        current_day = start_date
        
        # We search for available slots up to the task's due date
        # If we reach the due date and still have hours left, we schedule them but issue a deadline warning.
        # To avoid infinite loops, we set a hard limit of 30 days from start date.
        max_search_date = max(task["due_date"], start_date + timedelta(days=30))
        
        while hours_scheduled < hours_needed and current_day <= max_search_date:
            # Check if this day is past the due date (meaning we are scheduling late)
            is_late = current_day > task["due_date"]
            
            # Find available slots on this day
            for hr in preferred_hours:
                if hours_scheduled >= hours_needed:
                    break
                
                slot_key = (current_day, hr)
                if slot_key not in allocated_slots:
                    allocated_slots[slot_key] = {
                        "name": task["name"],
                        "subject": task["SUBJECT"],
                        "is_late": is_late
                    }
                    hours_scheduled += 1
                    
                    if current_day not in schedule:
                        schedule[current_day] = []
                    schedule[current_day].append((hr, task["name"], task["SUBJECT"], is_late))
            
            current_day += timedelta(days=1)
            
        if hours_scheduled < hours_needed:
            warnings.append(f"WARNING: Task '{task['name']}' could not be fully scheduled. Allocated {hours_scheduled}/{hours_needed} hours.")
        elif any(item[3] for day in schedule for item in schedule[day] if item[1] == task["name"]):
            warnings.append(f"WARNING: Task '{task['name']}' (due {task['due_date']}) was scheduled late (after due date).")
            
    return schedule, completed_tasks, warnings
def format_schedule(persona, schedule, completed_tasks, warnings, start_date_str):
    """
    Formats the schedule into a neat, human-readable text presentation.
    """
    output = []
    output.append("=" * 60)
    output.append(f"PERSONAL STUDY PLANNER SCHEDULE")
    output.append(f"Persona: {persona}")
    output.append(f"Schedule Start Date: {start_date_str}")
    output.append("=" * 60)
    output.append("")
    
    if warnings:
        output.append("SYSTEM WARNINGS:")
        for w in warnings:
            output.append(f"  * {w}")
        output.append("")
        output.append("-" * 60)
        output.append("")
    output.append("WEEKLY STUDY SESSIONS:")
    if not schedule:
        output.append("  No tasks scheduled.")
    else:
        # Sort days chronologically
        for day in sorted(schedule.keys()):
            output.append(f"\n{day.strftime('%A, %Y-%m-%d')}:")
            day_slots = sorted(schedule[day], key=lambda x: x[0])
            
            # Group consecutive slots of the same task for a cleaner presentation
            current_task_name = None
            current_subject = None
            start_hour = None
            prev_hour = None
            is_late = False
            
            def append_grouped_slot(start, end, name, subject, late):
                late_suffix = " [LATE / PAST DUE]" if late else ""
                output.append(f"  {start:02d}:00 - {end:02d}:00 | {name} ({subject}){late_suffix}")
            
            for hr, name, subject, late in day_slots:
                if current_task_name is None:
                    current_task_name = name
                    current_subject = subject
                    start_hour = hr
                    prev_hour = hr
                    is_late = late
                elif name == current_task_name and hr == prev_hour + 1:
                    prev_hour = hr
                else:
                    append_grouped_slot(start_hour, prev_hour + 1, current_task_name, current_subject, is_late)
                    current_task_name = name
                    current_subject = subject
                    start_hour = hr
                    prev_hour = hr
                    is_late = late
            
            if current_task_name is not None:
                append_grouped_slot(start_hour, prev_hour + 1, current_task_name, current_subject, is_late)
                
    output.append("")
    output.append("-" * 60)
    output.append("")
    output.append("COMPLETED TASKS SUMMARY:")
    if not completed_tasks:
        output.append("  No tasks marked as completed.")
    else:
        for task in completed_tasks:
            output.append(f"  [✓] {task['name']} ({task['SUBJECT']}) - Completed")
            
    output.append("")
    output.append("=" * 60)
    
    return "\n".join(output)
def main():
    if len(sys.argv) < 2:
        dsl_file = "study.dsl"
        override_persona = None
    else:
        dsl_file = sys.argv[1]
        override_persona = sys.argv[2].upper() if len(sys.argv) > 2 else None
        
    if not os.path.exists(dsl_file):
        print(f"Error: DSL file '{dsl_file}' not found.")
        print("Usage: python3 parser.py [path_to_dsl_file] [optional_persona_override]")
        sys.exit(1)
        
    print(f"Parsing DSL file: {dsl_file}...")
    persona, tasks = parse_dsl(dsl_file)
    
    if override_persona:
        if override_persona in PERSONAS:
            print(f"Overriding persona '{persona}' with: {override_persona}")
            persona = override_persona
        else:
            print(f"Warning: Override persona '{override_persona}' is invalid. Using '{persona}'.")
            
    print(f"Persona: {persona}")
    print(f"Total tasks parsed: {len(tasks)}")
    
    print(f"Scheduling tasks starting from {DEFAULT_START_DATE}...")
    schedule, completed_tasks, warnings = schedule_tasks(persona, tasks, DEFAULT_START_DATE)
    
    formatted_output = format_schedule(persona, schedule, completed_tasks, warnings, DEFAULT_START_DATE)
    
    print("\nGenerated Schedule Summary:")
    print(formatted_output)
    
    output_file = "output.txt"
    with open(output_file, "w") as f:
        f.write(formatted_output)
    print(f"\nFull schedule saved to: {os.path.abspath(output_file)}")
if __name__ == "__main__":
    main()