# test_core.py
import datetime
import pytest
import core

# Helpers
def make_date(days_from_today):
    return core.get_today() + datetime.timedelta(days=days_from_today)

def sample_tasks():
    return [
        core.make_task("Task A", 10, 2, make_date(3)),
        core.make_task("Task B", 5, 0, make_date(5)),
    ]

def sample_availability():
    return [
        core.make_day(make_date(0), 4),
        core.make_day(make_date(1), 3),
        core.make_day(make_date(2), 5),
        core.make_day(make_date(3), 2),
        core.make_day(make_date(4), 4),
        core.make_day(make_date(5), 6),
    ]

# --- Core function tests ---

def test_make_task_and_day():
    t = core.make_task("X", 8, 2, make_date(1))
    d = core.make_day(make_date(1), 5)
    assert t["name"] == "X"
    assert t["total_hours"] == 8
    assert t["completed_hours"] == 2
    assert isinstance(t["due_date"], datetime.date)
    assert d["hours"] == 5

def test_display_today_formats():
    today = core.get_today()
    out = core.display_today(today)
    assert "Today is:" in out
    assert today.strftime("%Y") in out

def test_adjust_availability_reduces_hours():
    avail = sample_availability()
    today = core.get_today()
    adjusted, msg = core.adjust_availability(avail, today, hours_used_today=2)
    today_entry = next(d for d in adjusted if d["date"] == today)
    assert today_entry["hours"] == avail[0]["hours"] - 2
    assert "remaining today" in msg

def test_adjust_availability_handles_none():
    avail = sample_availability()
    today = core.get_today()
    adjusted, _ = core.adjust_availability(avail, today)
    assert adjusted[0]["hours"] == avail[0]["hours"]  # unchanged if no usage

def test_calculate_task_buffer_enough_time():
    task = core.make_task("Test", 4, 0, make_date(2))
    avail = [
        core.make_day(make_date(0), 2),
        core.make_day(make_date(1), 2),
        core.make_day(make_date(2), 2),
    ]
    total, required, buffer = core.calculate_task_buffer(task, avail, core.get_today())
    assert total == 6
    assert required == 4
    assert buffer == 2

def test_calculate_task_buffer_completed_task_returns_none():
    task = core.make_task("Done", 2, 2, make_date(1))
    result = core.calculate_task_buffer(task, sample_availability(), core.get_today())
    assert result is None

def test_report_task_buffers_includes_task_name():
    report = core.report_task_buffers(sample_tasks(), sample_availability(), core.get_today())
    assert "--- Buffer Time Report ---" in report
    assert "Task A" in report
    assert "Task B" in report

def test_report_overall_positive_buffer():
    tasks = [core.make_task("Easy", 2, 0, make_date(1))]
    avail = [core.make_day(make_date(0), 5)]
    report = core.report_overall(tasks, avail, core.get_today())
    assert "Total remaining work" in report
    assert "✅" in report

def test_report_overall_negative_buffer():
    tasks = [core.make_task("Hard", 10, 0, make_date(1))]
    avail = [core.make_day(make_date(0), 2)]
    report = core.report_overall(tasks, avail, core.get_today())
    assert "🚨" in report

def test_combine_same_due_date_merges():
    due = make_date(2)
    tasks = [
        core.make_task("One", 3, 1, due),
        core.make_task("Two", 2, 0, due),
    ]
    merged = core.combine_same_due_date(tasks)
    assert len(merged) == 1
    assert "One & Two" in merged[0]["name"]
    assert merged[0]["total_hours"] == 5
    assert merged[0]["completed_hours"] == 1

def test_report_procrastination_detects_shortage():
    tasks = [core.make_task("Late", 10, 0, make_date(1))]
    avail = [core.make_day(make_date(1), 2)]
    report = core.report_procrastination(tasks, avail, core.get_today())
    assert "🚨" in report

def test_basic_report_includes_sections():
    report = core.basic_report(sample_availability(), sample_tasks(), hours_used_today=1)
    assert "Today is:" in report
    assert "--- Buffer Time Report ---" in report
    assert "--- Overall Workload Report ---" in report

def test_procrastination_report_includes_sections():
    report = core.procrastination_report(sample_availability(), sample_tasks(), hours_used_today=1)
    assert "Today is:" in report
    assert "--- Procrastination Report ---" in report
