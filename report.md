# Project Report: Persona-Based Study Planner DSL

## 1. Objective and Introduction

The **Persona Study Planner DSL** is a domain-specific language designed to help students declare study tasks, priorities, deadlines, and completion statuses. Additionally, it integrates a **Persona Scheduler** that automatically generates personalized day-by-day study calendars matching a student's biological productivity patterns (e.g., Night Owl, Early Bird, or Balanced).

Traditional calendar tools require tedious manual slot booking. In contrast, this DSL allows students to simply specify *what* needs to be done, *when* it is due, and *who* they are, shifting the cognitive load of scheduling onto a declarative execution engine.

---

## 2. DSL Grammar and Language Specification

### EBNF Grammar Definition
The language is defined by the following Extended Backus-Naur Form (EBNF) grammar:

```
Program       ::= Persona task_block*
Persona       ::= 'PERSONA' ('NIGHT_OWL' | 'EARLY_BIRD' | 'BALANCED')
task_block    ::= 'TASK' task_name
                  'SUBJECT' subject_name
                  'DUE' date
                  'PRIORITY' priority_level
                  'DURATION' duration_value
                  'STATUS' status_value
                  'END'

task_name     ::= identifier
subject_name  ::= identifier
date          ::= yyyy-mm-dd
priority_level::= 'HIGH' | 'MEDIUM' | 'LOW'
duration_value::= integer 'h'
status_value  ::= 'PENDING' | 'COMPLETED'
identifier    ::= [a-zA-Z_][a-zA-Z0-9_]*
```

### Keywords and Token Reference

| Keyword | Description | Valid Values |
| :--- | :--- | :--- |
| **PERSONA** | Defines the global scheduling persona of the student. | `NIGHT_OWL`, `EARLY_BIRD`, `BALANCED` |
| **TASK** | Initiates a task definition block. | Any alphanumeric string |
| **SUBJECT** | The academic course or subject category. | Any alphanumeric string |
| **DUE** | Deadline of the task in YYYY-MM-DD format. | E.g., `2026-06-20` |
| **PRIORITY** | The urgency weight used by the scheduling heuristic. | `HIGH`, `MEDIUM`, `LOW` |
| **DURATION** | Estimated execution hours needed. | Integer followed by `h` (e.g., `3h`) |
| **STATUS** | Current state of completion. | `PENDING`, `COMPLETED` |
| **END** | Terminating boundary of the task block. | N/A |

---

## 3. Architecture and Scheduling Heuristic

The system employs a two-tier architecture:
1. **Parser Layer**: Scans the `.dsl` file, validates syntax, processes keywords, and builds list-of-dict representations of tasks.
2. **Scheduling Heuristic Layer**: Resolves task ordering and slots hours into calendar cells.

```
       +-------------+
       |  study.dsl  |
       +------+------+
              |
              v
       +------+------+
       |  parser.py  |  --- (Syntax validation & token extraction)
       +------+------+
              |
              v
       +------+------+
       |  Scheduler  |  <--- (Persona definitions: NIGHT_OWL, etc.)
       +------+------+
              |
              v
     +--------+--------+
     |                 |
     v                 v
+----+----+       +----+----+
| Console |       |output.txt|  (Formatted day-by-day calendar)
+---------+       +---------+
```

### Scheduling Strategy (Greedy Priority Heuristic)
1. **Filtering**: Only `PENDING` tasks enter the scheduler. `COMPLETED` tasks are omitted from slotting and appended as completed summaries.
2. **Sorting (Task Urgency Score)**: Pending tasks are sorted using a multi-key comparison:
   - Primary: **Priority Value** ($HIGH = 3 > MEDIUM = 2 > LOW = 1$).
   - Secondary: **Due Date** (earliest deadline first).
3. **Allocation (Slotting)**: 
   - A calendar starts from tomorrow's date ($D$).
   - For each task in the sorted list, the scheduler scans forward day-by-day.
   - On each day, it looks at the student's persona hours:
     - **NIGHT_OWL**: 18:00 to 00:00 (Evening)
     - **EARLY_BIRD**: 06:00 to 12:00 (Morning)
     - **BALANCED**: 09:00 to 12:00 & 14:00 to 17:00 (Split workday)
   - The task is allotted to the earliest unoccupied slots on that day.
   - If a task's duration extends past its due date, the scheduler continues slotting but triggers a **Late / Past Due Warning** in the output report.

---

## 4. How to Run and Interact

### Execution Requirements
- Python 3.x (Zero external dependencies).

### Run the Default Schedule
To run the parser against the default `study.dsl`:
```bash
python3 parser.py
```

### Override Persona via Command Line
You can test how different personas affect the scheduling output by passing the persona override as the third argument:
```bash
python3 parser.py study.dsl NIGHT_OWL
python3 parser.py study.dsl EARLY_BIRD
python3 parser.py study.dsl BALANCED
```

### Outputs
- **Console Out**: Standard output prints a clean summary and validation results.
- **output.txt**: Contains the full formatted schedule with warnings and a completed task summary.
