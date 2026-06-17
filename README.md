# Persona-Based Study Planner DSL 📅

A declarative, human-readable Domain Specific Language (DSL) that automatically generates personalized study schedules based on student learning personas. Instead of booking calendar slots manually, students define their workload, priorities, deadlines, and study persona, letting the scheduler handle the rest.

---

## 🚀 Quick Start

### 🖥️ CLI Parser
The core parser does not require any external packages. By default, it reads `study.dsl` and schedules tasks starting from tomorrow under the `BALANCED` persona:
```bash
python3 parser.py
```

To override the persona via CLI, pass the file path and the target persona:
```bash
python3 parser.py study.dsl NIGHT_OWL
python3 parser.py study.dsl EARLY_BIRD
```

### 🌐 Web Interface (Flask)
A premium glassmorphic web interface is available to interactively edit study plans, load templates, and view schedules visually:
1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python3 app.py
   ```
3. Open your web browser to: **`http://127.0.0.1:5000`**

---

## ⚡ DSL Syntax Example

Save your study plan as `.dsl` (e.g., `study.dsl`). Here is how it looks:

```text
PERSONA NIGHT_OWL

TASK AI_Assignment
    SUBJECT   Artificial_Intelligence
    DUE       2026-06-20
    PRIORITY  HIGH
    DURATION  3h
    STATUS    PENDING
END

TASK Mathematics_Revision
    SUBJECT   Mathematics
    DUE       2026-06-25
    PRIORITY  HIGH
    DURATION  4h
    STATUS    COMPLETED
END
```

---

## 🧠 Core Features & Concepts

### 👤 Study Personas
Tasks are automatically slotted into time blocks according to the selected persona:
*   **`NIGHT_OWL`**: Peak productivity from **18:00 to 00:00** (Evening sessions)
*   **`EARLY_BIRD`**: Peak productivity from **06:00 to 12:00** (Morning sessions)
*   **`BALANCED`**: Standard split-day hours: **09:00 to 12:00** & **14:00 to 17:00**

### ⚖️ Greedy Scheduling Heuristic
1.  **Filtering**: Only slots `PENDING` tasks. `COMPLETED` tasks are logged in a summary list.
2.  **Priority Sorting**: Sorts tasks by priority value (`HIGH` > `MEDIUM` > `LOW`) then by due date (earliest first).
3.  **Conflict Prevention**: Allocates tasks sequentially into the persona's available slots without overlapping.
4.  **Past-Due Warnings**: If a task's duration extends beyond its `DUE` date, it is labeled as `[LATE / PAST DUE]` and a system warning is generated.
