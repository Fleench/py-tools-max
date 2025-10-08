'''
A Textual UI for the project management tool.
'''
import data
import core

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input
from textual.containers import Container

class ProjectApp(App):
    """A Textual app to manage projects."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            Input(placeholder="Hours worked today", id="hours_worked"),
            Button("Basic Report", id="basic_report", variant="success"),
            Button("Procrastination Report", id="procrastination_report", variant="warning"),
        )
        yield Static(id="report_display")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "Project Management Tool"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        report_display = self.query_one("#report_display", Static)
        if event.button.id == "basic_report":
            hours_worked_input = self.query_one("#hours_worked", Input)
            hours_worked_str = hours_worked_input.value
            try:
                hours_worked = float(hours_worked_str) if hours_worked_str else 0.0
                report = core.basic_report(data.availability, data.tasks, hours_worked)
                report_display.update(report)
            except ValueError:
                report_display.update("[bold red]Invalid input for hours worked. Please enter a number.[/bold red]")
        elif event.button.id == "procrastination_report":
            report = core.procrastination_report(data.availability, data.tasks)
            report_display.update(report)

if __name__ == "__main__":
    app = ProjectApp()
    app.run()
