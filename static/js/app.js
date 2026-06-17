/* ==========================================================================
   PERSONA STUDY PLANNER DSL - INTERACTIVE LOGIC (app.js)
   ========================================================================== */

// Predefined DSL Templates
const PRESETS = {
    night_owl: `PERSONA NIGHT_OWL

TASK AI_Assignment
    SUBJECT   Artificial_Intelligence
    DUE       2026-06-20
    PRIORITY  HIGH
    DURATION  3h
    STATUS    PENDING
END

TASK DBMS_Project
    SUBJECT   Database
    DUE       2026-06-23
    PRIORITY  MEDIUM
    DURATION  2h
    STATUS    PENDING
END

TASK Mathematics_Revision
    SUBJECT   Mathematics
    DUE       2026-06-25
    PRIORITY  HIGH
    DURATION  4h
    STATUS    COMPLETED
END

TASK OS_Lab_Report
    SUBJECT   Operating_Systems
    DUE       2026-06-19
    PRIORITY  HIGH
    DURATION  2h
    STATUS    PENDING
END

TASK Computer_Networks_Quiz
    SUBJECT   Computer_Networks
    DUE       2026-06-21
    PRIORITY  LOW
    DURATION  2h
    STATUS    PENDING
END

TASK Ethics_Essay
    SUBJECT   Humanities
    DUE       2026-06-18
    PRIORITY  LOW
    DURATION  1h
    STATUS    PENDING
END`,

    early_bird: `PERSONA EARLY_BIRD

TASK Math_Analysis
    SUBJECT   Calculus
    DUE       2026-06-19
    PRIORITY  HIGH
    DURATION  4h
    STATUS    PENDING
END

TASK Chemistry_Lab
    SUBJECT   Organic_Chemistry
    DUE       2026-06-21
    PRIORITY  MEDIUM
    DURATION  3h
    STATUS    PENDING
END

TASK Physics_Review
    SUBJECT   Thermodynamics
    DUE       2026-06-18
    PRIORITY  HIGH
    DURATION  2h
    STATUS    COMPLETED
END`,

    balanced: `PERSONA BALANCED

TASK Project_Presentation
    SUBJECT   Software_Engineering
    DUE       2026-06-22
    PRIORITY  HIGH
    DURATION  3h
    STATUS    PENDING
END

TASK Technical_Writing
    SUBJECT   Communications
    DUE       2026-06-25
    PRIORITY  LOW
    DURATION  2h
    STATUS    PENDING
END

TASK Lab_Experiment
    SUBJECT   Microprocessors
    DUE       2026-06-20
    PRIORITY  MEDIUM
    DURATION  4h
    STATUS    PENDING
END`,

    empty: `# Custom DSL Study Plan
PERSONA BALANCED

TASK New_Task
    SUBJECT   General
    DUE       2026-06-20
    PRIORITY  MEDIUM
    DURATION  2h
    STATUS    PENDING
END
`
};

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dslTextarea = document.getElementById('dsl-textarea');
    const startDateInput = document.getElementById('start-date-input');
    const personaSelect = document.getElementById('persona-override-select');
    const btnGenerate = document.getElementById('btn-generate');
    const statusBadge = document.getElementById('status-badge');
    
    // Presets Dropdown
    const btnPresets = document.getElementById('btn-presets');
    const presetsMenu = document.getElementById('presets-menu');
    
    // View States
    const viewIdle = document.getElementById('view-idle');
    const viewLoading = document.getElementById('view-loading');
    const viewError = document.getElementById('view-error');
    const viewSuccess = document.getElementById('view-success');
    
    // Error View elements
    const errorMessage = document.getElementById('error-message');
    const errorLine = document.getElementById('error-line');
    
    // Success View elements
    const warningsSection = document.getElementById('warnings-section');
    const warningsList = document.getElementById('warnings-list');
    const metaPersona = document.getElementById('meta-persona');
    const metaStartDate = document.getElementById('meta-start-date');
    const timelineContainer = document.getElementById('timeline-container');
    const completedTasksList = document.getElementById('completed-tasks-list');

    // ==========================================================================
    // INITIALIZATION & SETUP
    // ==========================================================================
    
    // Set default start date to tomorrow dynamically
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const yyyy = tomorrow.getFullYear();
    const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const dd = String(tomorrow.getDate()).padStart(2, '0');
    startDateInput.value = `${yyyy}-${mm}-${dd}`;
    
    // Load Night Owl preset by default
    dslTextarea.value = PRESETS.night_owl;

    // Presets Dropdown Toggle
    btnPresets.addEventListener('click', (e) => {
        e.stopPropagation();
        presetsMenu.classList.toggle('active');
    });

    // Close presets dropdown on outside click
    document.addEventListener('click', () => {
        presetsMenu.classList.remove('active');
    });

    // Load preset selection
    presetsMenu.querySelectorAll('li').forEach(item => {
        item.addEventListener('click', (e) => {
            const presetKey = e.currentTarget.getAttribute('data-preset');
            if (PRESETS[presetKey] !== undefined) {
                dslTextarea.value = PRESETS[presetKey];
            }
            presetsMenu.classList.remove('active');
        });
    });

    // ==========================================================================
    // STATE MANAGEMENT UTILS
    // ==========================================================================
    function switchState(state) {
        // Remove active class from all states
        viewIdle.classList.remove('active');
        viewLoading.classList.remove('active');
        viewError.classList.remove('active');
        viewSuccess.classList.remove('active');
        
        statusBadge.className = 'badge';

        if (state === 'idle') {
            viewIdle.classList.add('active');
            statusBadge.innerText = 'Idle';
        } else if (state === 'loading') {
            viewLoading.classList.add('active');
            statusBadge.innerText = 'Compiling...';
            statusBadge.classList.add('active');
        } else if (state === 'error') {
            viewError.classList.add('active');
            statusBadge.innerText = 'Error';
            statusBadge.classList.add('error');
        } else if (state === 'success') {
            viewSuccess.classList.add('active');
            statusBadge.innerText = 'Success';
            statusBadge.classList.add('active');
        }
    }

    // ==========================================================================
    // SCHEDULE COMPILATION CALL
    // ==========================================================================
    btnGenerate.addEventListener('click', async () => {
        const dslContent = dslTextarea.value;
        const startDate = startDateInput.value;
        const personaOverride = personaSelect.value;

        switchState('loading');

        try {
            const response = await fetch('/api/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dsl_content: dslContent,
                    start_date: startDate,
                    persona_override: personaOverride
                })
            });

            const result = await response.json();

            if (result.success) {
                renderSchedule(result);
                switchState('success');
            } else {
                renderError(result);
                switchState('error');
            }
        } catch (err) {
            renderError({
                message: 'Failed to communicate with Flask backend server. Ensure the app is running.',
                error_type: 'NetworkError'
            });
            switchState('error');
        }
    });

    // ==========================================================================
    // RENDERING LOGIC
    // ==========================================================================
    
    function renderError(data) {
        errorMessage.innerText = data.message || 'An unexpected compilation error occurred.';
        if (data.line_num) {
            errorLine.parentElement.style.display = 'inline-block';
            errorLine.innerText = data.line_num;
        } else {
            errorLine.parentElement.style.display = 'none';
        }
    }

    function renderSchedule(data) {
        // Clear elements
        timelineContainer.innerHTML = '';
        completedTasksList.innerHTML = '';
        warningsList.innerHTML = '';
        
        // Update Metadata
        metaPersona.innerText = data.persona;
        metaStartDate.innerText = data.start_date;

        // Warnings List
        if (data.warnings && data.warnings.length > 0) {
            warningsSection.classList.remove('hidden');
            data.warnings.forEach(warning => {
                const li = document.createElement('li');
                li.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color: var(--warning); margin-right: 0.5rem;"></i>${warning}`;
                warningsList.appendChild(li);
            });
        } else {
            warningsSection.classList.add('hidden');
        }

        // Timeline Schedule Sorting & Render
        const sortedDays = Object.keys(data.schedule).sort();

        if (sortedDays.length === 0) {
            timelineContainer.innerHTML = `
                <div class="empty-state" style="padding: 2rem 0;">
                    <i class="fa-solid fa-calendar-xmark" style="font-size: 1.5rem; margin-bottom: 0.5rem; color: var(--text-muted);"></i>
                    <h3>No Scheduled Days</h3>
                    <p>All parsed tasks are either completed or could not be mapped within scheduling ranges.</p>
                </div>`;
        } else {
            sortedDays.forEach(dayStr => {
                const dateObj = new Date(dayStr + 'T00:00:00');
                const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
                const dayTitleText = dateObj.toLocaleDateString('en-US', options);

                const dayCard = document.createElement('div');
                dayCard.className = 'day-card';

                const title = document.createElement('h3');
                title.className = 'day-title';
                title.innerText = dayTitleText;
                dayCard.appendChild(title);

                const sessionsDiv = document.createElement('div');
                sessionsDiv.className = 'day-sessions';

                // Sort slots chronologically within day
                const slots = data.schedule[dayStr].sort((a, b) => a.hour_start - b.hour_start);

                // Group consecutive hours of the same task for a cleaner presentation
                const groupedSlots = [];
                let currentSlot = null;

                slots.forEach(slot => {
                    if (currentSlot === null) {
                        currentSlot = { ...slot };
                    } else if (slot.task_name === currentSlot.task_name && slot.hour_start === currentSlot.hour_end) {
                        currentSlot.hour_end = slot.hour_end;
                    } else {
                        groupedSlots.push(currentSlot);
                        currentSlot = { ...slot };
                    }
                });
                if (currentSlot !== null) {
                    groupedSlots.push(currentSlot);
                }

                groupedSlots.forEach(slot => {
                    const sessionSlot = document.createElement('div');
                    sessionSlot.className = 'session-slot';

                    // Format Time range
                    const startFmt = String(slot.hour_start).padStart(2, '0') + ':00';
                    const endFmt = String(slot.hour_end).padStart(2, '0') + ':00';

                    sessionSlot.innerHTML = `
                        <div class="session-time">
                            <i class="fa-regular fa-clock"></i>
                            <span>${startFmt} - ${endFmt}</span>
                        </div>
                        <div class="session-details">
                            <div class="session-info">
                                <span class="session-task">${slot.task_name}</span>
                                <span class="session-subject">${slot.subject.replace(/_/g, ' ')}</span>
                            </div>
                            <div class="session-badges">
                                ${slot.is_late ? '<span class="badge-late">Late / Past Due</span>' : ''}
                            </div>
                        </div>`;
                    
                    sessionsDiv.appendChild(sessionSlot);
                });

                dayCard.appendChild(sessionsDiv);
                timelineContainer.appendChild(dayCard);
            });
        }

        // Completed Tasks Summary
        if (data.completed_tasks && data.completed_tasks.length > 0) {
            data.completed_tasks.forEach(task => {
                const li = document.createElement('li');
                li.innerHTML = `<i class="fa-solid fa-square-check"></i> <span><strong>${task.name}</strong> (${task.SUBJECT.replace(/_/g, ' ')}) - Completed</span>`;
                completedTasksList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.style.color = 'var(--text-muted)';
            li.innerText = 'No completed tasks in the input DSL.';
            completedTasksList.appendChild(li);
        }
    }
});
