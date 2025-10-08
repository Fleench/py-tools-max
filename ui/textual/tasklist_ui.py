import sys
import os
import datetime
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, ListView, ListItem, Input, RichLog
from textual.containers import Container, VerticalScroll
from textual.screen import Screen

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from projects.tasklist.core import make_task, basic_report, procrastination_report, get_today
from projects.tasklist.data import tasks as initial_tasks, availability as initial_availability

class TasklistApp(App):
    """A Textual app to manage tasks."""

    CSS = """
    Screen {
        layout: horizontal;
        height: 100%;
    }
    #left-pane {
        width: 50%;
        height: 100%;
        border-right: solid $primary;
    }
    #right-pane {
        width: 50%;
        height: 100%;
    }
    #task-list {
        height: 50%;
        border: solid $accent;
        margin-bottom: 1;
    }
    #task-details {
        height: 20%;
        border: round $accent;
        padding: 1;
    }
    #add-task-container {
        height: auto;
    }
    #report-log {
        height: 100%;
    }
    """

    def __init__(self):
        super().__init__()
        # Use copies to avoid modifying the original data module on re-runs
        self.tasks = [task.copy() for task in initial_tasks]
        self.availability = [day.copy() for day in initial_availability]
        self.selected_task = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(name="Tasklist")
        with Container(id="left-pane"):
            yield Static("Tasks")
            yield ListView(id="task-list")
            yield Static("Task Details", id="task-details")
            with VerticalScroll(id="add-task-container"):
                yield Static("Add New Task")
                yield Input(placeholder="Task Name", id="task-name")
                yield Input(placeholder="Total Hours", id="total-hours", type="number")
                yield Input(placeholder="Completed Hours", id="completed-hours", type="number")
                yield Input(placeholder=f"Due Date (YYYY-MM-DD)", id="due-date")
                yield Button("Add Task", id="add-task-button")

        with Container(id="right-pane"):
            yield Static("Reports")
            yield Button("Generate Basic Report", id="basic-report-button")
            yield Button("Generate Procrastination Report", id="procrastination-report-button")
            yield RichLog(id="report-log", wrap=True)

        yield Footer()

    def on_mount(self) -> None:
        """Populate the task list on startup."""
        self.update_task_list()

    def update_task_list(self) -> None:
        """Clears and repopulates the task list view."""
        list_view = self.query_one("#task-list", ListView)
        list_view.clear()
        for task in self.tasks:
            # Using a custom ListItem to store the task object could be another way
            list_view.append(ListItem(Static(task['name'])))

    def on_list_view_selected(self, event: ListView.Selected):
        """Display task details when a task is selected."""
        selected_index = event.list_view.index
        if selected_index is not None and 0 <= selected_index < len(self.tasks):
            self.selected_task = self.tasks[selected_index]
            due_date_str = self.selected_task['due_date'].strftime('%Y-%m-%d')
            details = f"""
Name: {self.selected_task['name']}
Due: {due_date_str}
Hours: {self.selected_task['completed_hours']} / {self.selected_task['total_hours']}
"""
            self.query_one("#task-details").update(details)

    def on_button_pressed(self, event: Button.Pressed):
        """Handle button press events."""
        log = self.query_one("#report-log")
        if event.button.id == "add-task-button":
            try:
                name = self.query_one("#task-name").value
                total_hours = float(self.query_one("#total-hours").value or 0)
                completed_hours = float(self.query_one("#completed-hours").value or 0)
                due_date_str = self.query_one("#due-date").value

                if not name or not due_date_str:
                    log.write("[bold red]Error: Task Name and Due Date are required.[/bold red]")
                    return

                due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()

                new_task = make_task(name, total_hours, completed_hours, due_date)
                self.tasks.append(new_task)
                self.update_task_list()

                # Clear input fields
                self.query_one("#task-name").value = ""
                self.query_one("#total-hours").value = ""
                self.query_one("#completed-hours").value = ""
                self.query_one("#due-date").value = ""
                log.write(f"Added task: {name}")

            except ValueError:
                log.write("[bold red]Error: Invalid date or number format.[/bold red]")

        elif event.button.id == "basic-report-button":
            report = basic_report(self.availability, self.tasks)
            log.clear()
            log.write(report)

        elif event.button.id == "procrastination-report-button":
            report = procrastination_report(self.availability, self.tasks)
            log.clear()
            log.write(report)


if __name__ == "__main__":
    app = TasklistApp()
    app.run()