'''
The core of the software. Manages generating all reports and task/availability lists.
'''
import datetime

def make_task(name, total_hours, completed_hours, due_date):
    return {
        "name": name,
        "total_hours": total_hours,
        "completed_hours": completed_hours,
        "due_date": due_date,
    }

def make_day(date, hours):
    return {"date": date, "hours": hours}

# (rest of core stays the same, no global tasks/availability lists)



def get_today():
    """Return today's date."""
    return datetime.date.today()


def display_today(today):
    """Return today's formatted date string."""
    return f"Today is: {today.strftime('%A, %B %d, %Y')}\n"


def adjust_availability(availability, today, hours_used_today=None):
    """
    Return availability adjusted for hours already used today.
    If hours_used_today is None, assume 0 (non-interactive).
    """
    adjusted = [day.copy() for day in availability]
    messages = []

    for day in adjusted:
        if day["date"] == today:
            try:
                if hours_used_today is None:
                    hours_used_today = 0
                day["hours"] = max(0, day["hours"] - float(hours_used_today))
                messages.append(
                    f"👍 Got it. You have {day['hours']} hours remaining today.\n"
                )
            except ValueError:
                messages.append("Invalid input. Assuming 0 hours used today.\n")
            break

    return adjusted, "\n".join(messages)


def calculate_task_buffer(task, adjusted_availability, today):
    """Calculate available time, required time, and buffer for a single task."""
    hours_remaining = task["total_hours"] - task["completed_hours"]
    if hours_remaining <= 0:
        return None

    total_available_hours = sum(
        day["hours"]
        for day in adjusted_availability
        if today <= day["date"] <= task["due_date"]
    )

    buffer_time = total_available_hours - hours_remaining
    return total_available_hours, hours_remaining, buffer_time


def report_task_buffers(tasks, adjusted_availability, today):
    """Return buffer report for all tasks as a string."""
    lines = ["--- Buffer Time Report ---"]

    for task in sorted(tasks, key=lambda t: t["due_date"]):
        result = calculate_task_buffer(task, adjusted_availability, today)
        if not result:
            continue

        total_available, required, buffer_time = result
        lines.append(f"📚 Task: {task['name']} (Due: {task['due_date'].strftime('%m/%d')})")
        lines.append(f"   - You have {total_available:.1f} hours available until the due date.")
        lines.append(f"   - You need to complete {required:.1f} hours of this work by then.")

        if buffer_time >= 0:
            lines.append(f"   - ✅ Result: You have a buffer of {buffer_time:.1f} hours.\n")
        else:
            lines.append(
                f"   - 🚨 Warning: You are short by {abs(buffer_time):.1f} hours! "
                "You need to find more time.\n"
            )

    return "\n".join(lines)


def report_overall(tasks, adjusted_availability, today):
    """Return overall workload and availability summary as a string."""
    lines = ["--- Overall Workload Report ---"]

    grand_total_required = sum(
        max(0, task["total_hours"] - task["completed_hours"]) for task in tasks
    )
    grand_total_available = sum(
        day["hours"] for day in adjusted_availability if day["date"] >= today
    )

    lines.append(f"📝 Total remaining work: {grand_total_required:.1f} hours")
    lines.append(f"🕒 Total available time: {grand_total_available:.1f} hours")

    if grand_total_available >= grand_total_required:
        lines.append(
            f"   - ✅ Overall: You can finish everything with "
            f"{grand_total_available - grand_total_required:.1f} hours to spare.\n"
        )
    else:
        lines.append(
            f"   - 🚨 Overall: You are short by "
            f"{grand_total_required - grand_total_available:.1f} hours. "
            "Too busy! Find extra time.\n"
        )

    return "\n".join(lines)


def combine_same_due_date(tasks):
    """Merge tasks with the same due date into combined tasks."""
    merged = {}
    for task in tasks:
        key = task["due_date"]
        if key not in merged:
            merged[key] = task.copy()
        else:
            merged[key]["name"] = merged[key]["name"] + " & " + task["name"]
            merged[key]["total_hours"] += task["total_hours"]
            merged[key]["completed_hours"] += task["completed_hours"]
    return list(merged.values())


def report_procrastination(tasks, adjusted_availability, today, hours_used_today=None):
    """
    Procrastination report:
    Assume tasks are not started until the due date of the next closest task has passed.
    Merge tasks with the same due date.
    """
    lines = ["--- Procrastination Report ---"]
    merged_tasks = combine_same_due_date(tasks)
    merged_tasks = sorted(merged_tasks, key=lambda t: t["due_date"])

    for idx, task in enumerate(merged_tasks):
        required = max(0, task["total_hours"] - task["completed_hours"])
        window_start = merged_tasks[idx - 1]["due_date"] if idx > 0 else today
        window_start = max(window_start, today)  # clamp to today

        total_available = sum(
            day["hours"]
            for day in adjusted_availability
            if window_start < day["date"] <= task["due_date"]
        )

        buffer_time = total_available - required

        lines.append(f"📚 Task: {task['name']} (Due: {task['due_date'].strftime('%m/%d')})")
        lines.append(f"   - Available hours in window: {total_available:.1f}")
        lines.append(f"   - Required hours: {required:.1f}")

        if buffer_time >= 0:
            lines.append(f"   - ✅ You can procrastinate until then with {buffer_time:.1f} hours spare.\n")
        else:
            lines.append(
                f"   - 🚨 Danger: Procrastination fails, short by {abs(buffer_time):.1f} hours!\n"
            )

    return "\n".join(lines)


def basic_report(availability, tasks, hours_used_today=None):
    """Return full report as a single string (non-interactive)."""
    today = get_today()
    outputs = [display_today(today)]

    adjusted_availability, adjust_msg = adjust_availability(
        availability, today, hours_used_today
    )
    outputs.append(adjust_msg)

    outputs.append(report_task_buffers(tasks, adjusted_availability, today))
    outputs.append(report_overall(tasks, adjusted_availability, today))

    return "\n".join(outputs)


def procrastination_report(availability, tasks, hours_used_today=None):
    """Return procrastination report as a string (non-interactive)."""
    today = get_today()
    outputs = [display_today(today)]

    adjusted_availability, adjust_msg = adjust_availability(
        availability, today, hours_used_today
    )
    outputs.append(adjust_msg)

    outputs.append(report_procrastination(tasks, adjusted_availability, today))

    return "\n".join(outputs)


# Example:
# report = basic_report(availability, tasks, hours_used_today=2)
# print(report)
# procrastination = procrastination_report(availability, tasks, hours_used_today=2)
# print(procrastination)
