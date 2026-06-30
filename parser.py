import sys
import os
from datetime import datetime, timedelta
# pyrefly: ignore [missing-import]
import ply.lex as lex
import ply.yacc as yacc
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
def register_custom_persona(persona_val):
    """
    Parses a CUSTOM:hr1,hr2,... string, validates it, and registers it in the global PERSONAS dict.
    Returns the normalized key (e.g. 'CUSTOM:9,10,11').
    Raises ValueError if the format or values are invalid.
    """
    if not persona_val.startswith("CUSTOM:"):
        raise ValueError("Must start with CUSTOM:")
    hours_str = "".join(persona_val.split(":", 1)[1].split())
    custom_hours = [int(h) for h in hours_str.split(",") if h]
    for h in custom_hours:
        if not (0 <= h <= 23):
            raise ValueError("Hours must be between 0 and 23.")
    if not custom_hours:
        raise ValueError("Must specify at least one hour.")
    sorted_hours = sorted(list(set(custom_hours)))
    normalized_key = f"CUSTOM:{','.join(map(str, sorted_hours))}"
    PERSONAS[normalized_key] = sorted_hours
    return normalized_key

class DSLSyntaxError(Exception):
    """Exception raised for syntax errors in the Study Planner DSL."""
    def __init__(self, message, line_num=None):
        super().__init__(message)
        self.message = message
        self.line_num = line_num

    def __str__(self):
        if self.line_num is not None:
            return f"Line {self.line_num}: {self.message}"
        return self.message

def parse_dsl(filepath):
    """
    Parses the study planner DSL file.
    Returns:
        persona (str): The persona name or "BALANCED" if not specified.
        tasks (list): A list of parsed task dictionaries.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Error: File '{filepath}' does not exist.")
    with open(filepath, "r", encoding="utf-8") as file:
        data = file.read()
    
    lexer = lex.lex()
    parser = yacc.yacc()
    
    return parser.parse(data, lexer=lexer)

# Lexer definitions
tokens = (
    'PERSONA',
    'TASK',
    'END',
    'SUBJECT',
    'DUE',
    'PRIORITY',
    'DURATION',
    'STATUS',
    'VALUE',
)

states = (
    ('value', 'exclusive'),
)

def t_ANY_COMMENT(t):
    r'\#.*'
    pass

def t_PERSONA(t):
    r'PERSONA'
    t.lexer.begin('value')
    return t

def t_TASK(t):
    r'TASK'
    t.lexer.begin('value')
    return t

def t_SUBJECT(t):
    r'SUBJECT'
    t.lexer.begin('value')
    return t

def t_DUE(t):
    r'DUE'
    t.lexer.begin('value')
    return t

def t_PRIORITY(t):
    r'PRIORITY'
    t.lexer.begin('value')
    return t

def t_DURATION(t):
    r'DURATION'
    t.lexer.begin('value')
    return t

def t_STATUS(t):
    r'STATUS'
    t.lexer.begin('value')
    return t

def t_END(t):
    r'END'
    return t

def t_ANY_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.begin('INITIAL')

t_ANY_ignore = ' \t\r'

def t_value_VALUE(t):
    r'[^\n]+'
    t.value = t.value.strip()
    t.lexer.begin('INITIAL')
    if t.value:
        return t

def t_ANY_error(t):
    raise DSLSyntaxError(f"Illegal character '{t.value[0]}'", t.lineno)

# Parser definitions
def p_planner(p):
    '''planner : statements'''
    persona = "BALANCED"
    tasks = []
    for stmt in p[1]:
        if stmt[0] == 'persona':
            persona = stmt[1]
        elif stmt[0] == 'task':
            tasks.append(stmt[1])
    p[0] = (persona, tasks)

def p_statements(p):
    '''statements : statements statement
                  | empty'''
    if len(p) == 3:
        if p[2]:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = p[1]
    else:
        p[0] = []

def p_statement(p):
    '''statement : persona_stmt
                 | task_block'''
    p[0] = p[1]

def p_persona_stmt(p):
    '''persona_stmt : PERSONA VALUE'''
    persona_val = p[2].upper()
    if persona_val.startswith("CUSTOM:"):
        try:
            persona = register_custom_persona(persona_val)
        except ValueError as e:
            raise DSLSyntaxError(f"Invalid CUSTOM persona format: {str(e)}", p.lineno(1))
    elif persona_val in PERSONAS:
        persona = persona_val
    else:
        print(f"Warning on line {p.lineno(1)}: Unknown persona '{persona_val}'. Defaulting to BALANCED.")
        persona = "BALANCED"
    p[0] = ('persona', persona)

def p_task_block(p):
    '''task_block : TASK VALUE task_attributes END'''
    task_dict = {'name': p[2]}
    for attr in p[3]:
        task_dict.update(attr)
    
    # Validate required fields
    required_keys = ["SUBJECT", "DUE", "PRIORITY", "DURATION", "STATUS"]
    missing = [key for key in required_keys if key not in task_dict]
    if missing:
        raise DSLSyntaxError(f"Task '{task_dict.get('name', 'UNKNOWN')}' is missing fields: {', '.join(missing)}", p.lineno(1))
        
    p[0] = ('task', task_dict)

def p_task_attributes(p):
    '''task_attributes : task_attributes task_attribute
                       | empty'''
    if len(p) == 3:
        if p[2]:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = p[1]
    else:
        p[0] = []

def p_task_attribute(p):
    '''task_attribute : SUBJECT VALUE
                      | DUE VALUE
                      | PRIORITY VALUE
                      | DURATION VALUE
                      | STATUS VALUE'''
    key = p[1]
    val = p[2]
    lineno = p.lineno(1)
    
    if key == 'DURATION':
        if val.endswith("h"):
            try:
                duration_hours = int(val[:-1])
                p[0] = {'DURATION': val, 'duration_hours': duration_hours}
            except ValueError:
                raise DSLSyntaxError(f"Invalid DURATION format '{val}'. Must be an integer followed by 'h' (e.g., 3h).", lineno)
        else:
            raise DSLSyntaxError("DURATION must end with 'h' (e.g., 3h).", lineno)
    elif key == 'PRIORITY':
        priority = val.upper()
        if priority not in PRIORITY_ORDER:
            raise DSLSyntaxError(f"Invalid PRIORITY '{priority}'. Must be HIGH, MEDIUM, or LOW.", lineno)
        p[0] = {'PRIORITY': priority, 'priority_val': PRIORITY_ORDER[priority]}
    elif key == 'STATUS':
        status = val.upper()
        if status not in ["PENDING", "COMPLETED"]:
            raise DSLSyntaxError(f"Invalid STATUS '{status}'. Must be PENDING or COMPLETED.", lineno)
        p[0] = {'STATUS': status}
    elif key == 'DUE':
        try:
            due_date = datetime.strptime(val, "%Y-%m-%d").date()
            p[0] = {'DUE': val, 'due_date': due_date}
        except ValueError:
            raise DSLSyntaxError(f"Invalid DUE date format '{val}'. Must be YYYY-MM-DD.", lineno)
    else:
        p[0] = {key: val}

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p:
        raise DSLSyntaxError(f"Syntax error at '{p.value}'", p.lineno)
    else:
        raise DSLSyntaxError("Reached end of file without closing the last TASK block with END.")
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
        
    try:
        persona, tasks = parse_dsl(dsl_file)
    except (FileNotFoundError, DSLSyntaxError) as e:
        print(e)
        sys.exit(1)
    
    if override_persona:
        if override_persona.startswith("CUSTOM:"):
            try:
                override_persona = register_custom_persona(override_persona)
                print(f"Overriding persona '{persona}' with: {override_persona}")
                persona = override_persona
            except ValueError as e:
                print(f"Warning: Override persona '{override_persona}' is invalid ({str(e)}). Using '{persona}'.")
        elif override_persona in PERSONAS:
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