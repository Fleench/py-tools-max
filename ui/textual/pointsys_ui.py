import sys
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, RichLog, Label
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen, ModalScreen

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from projects.pointsys import core

class QuestionScreen(ModalScreen):
    """Screen with a question and two buttons."""

    def __init__(self, question: str, button1_label: str, button2_label: str) -> None:
        super().__init__()
        self.question = question
        self.button1_label = button1_label
        self.button2_label = button2_label

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.question, id="question"),
            Horizontal(
                Button(self.button1_label, variant="primary", id="button1"),
                Button(self.button2_label, id="button2"),
                classes="buttons",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "button1":
            self.dismiss(True)
        elif event.button.id == "button2":
            self.dismiss(False)

class LoginScreen(Screen):
    """Screen for user to login or create an account."""

    CSS = """
    #login-container {
        align: center middle;
        height: 100%;
    }
    Input {
        width: 40;
        margin-bottom: 1;
    }
    """
    def compose(self) -> ComposeResult:
        yield Header(name="PointSys - Login")
        with Container(id="login-container"):
            yield Static("Enter Account Name")
            yield Input(placeholder="e.g., 'personal' or 'work'", id="account_name")
            yield Button("Login / Create", variant="primary", id="login_button")
            yield Static(id="login_status")
        yield Footer()

    def on_mount(self) -> None:
        last_account = core.get_last_account()
        if last_account:
            self.query_one("#account_name").value = last_account

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login_button":
            account_name = self.query_one("#account_name").value.strip()
            if not account_name:
                self.query_one("#login_status").update("[red]Account name cannot be empty.[/red]")
                return

            if not core.account_exists(account_name):
                core.create_account(account_name)
                self.query_one("#login_status").update(f"Account '[bold]{account_name}[/bold]' created.")

            core.set_last_account(account_name)
            self.parent.account_name = account_name
            self.parent.files = core.get_account_files(account_name)

            def handle_crash_callback(should_commit: bool):
                if should_commit:
                    core.commit_session(self.parent.files)
                else:
                    core.rollback_session(self.parent.files)
                core.start_session(self.parent.files)
                self.app.push_screen("account")

            if core.has_crashed(account_name):
                self.app.push_screen(
                    QuestionScreen("A crashed session was found. Commit the changes?", "Commit", "Rollback"),
                    handle_crash_callback
                )
            else:
                core.start_session(self.parent.files)
                self.app.push_screen("account")

class AccountScreen(Screen):
    """Screen for managing an account."""
    CSS = """
    #main-container {
        layout: horizontal;
        height: 80%;
    }
    #left-pane, #right-pane {
        width: 50%;
        padding: 1;
    }
    #left-pane {
        border-right: solid $primary;
    }
    #log-container {
        height: 20%;
        border-top: wide $primary;
    }
    #status-bar {
        padding: 0 1;
        background: $surface;
        color: $text;
    }
    .action-group {
        border: round $accent;
        padding: 1;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(name=f"PointSys Account: {self.parent.account_name}")
        yield Static(id="status-bar")
        with Horizontal(id="main-container"):
            with Vertical(id="left-pane"):
                yield Static(f"[bold]Account:[/bold] {self.parent.account_name}", id="account_label")
                yield Static("Points: 0", id="points_display")
                yield Button("Logout (Rollback)", id="logout_button")
                yield Button("Commit & Exit", variant="primary", id="commit_button")
                yield Button("Rollback & Exit", id="rollback_button")

            with Vertical(id="right-pane"):
                with Vertical(classes="action-group"):
                    yield Static("[bold]Add Points[/bold]")
                    yield Input(placeholder="Reason (e.g., 'Worked out')", id="add_reason")
                    yield Input(placeholder="Number of points", id="add_value", type="number")
                    yield Button("Add Points", id="add_points_button")

                with Vertical(classes="action-group"):
                    yield Static("[bold]Redeem Reward[/bold]")
                    yield Input(placeholder="Reward (e.g., 'Coffee')", id="redeem_name")
                    yield Input(placeholder="Cost (e.g., '$5', '1h')", id="redeem_value")
                    yield Button("Redeem Reward", id="redeem_button")

        with Container(id="log-container"):
             yield RichLog(id="log_view", wrap=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.update_points()
        self.update_logs()
        self.set_status("Session started. Changes are temporary until committed.", "primary")

    def set_status(self, message, level="success"):
        status_bar = self.query_one("#status-bar")
        color_map = {"success": "green", "error": "red", "primary": "blue"}
        status_bar.update(f"[{color_map.get(level, 'white')}]{message}[/]")

    def update_points(self) -> None:
        points = core.read_points(self.parent.files["points_tmp"])
        self.query_one("#points_display").update(f"[bold]Points:[/bold] {points}")

    def update_logs(self) -> None:
        logs = core.view_logs(self.parent.files)
        log_widget = self.query_one("#log_view")
        log_widget.clear()
        log_widget.write(logs)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_points_button":
            reason = self.query_one("#add_reason").value
            value_str = self.query_one("#add_value").value

            if not reason:
                self.set_status("Error: Reason cannot be empty.", "error")
                return

            try:
                points = int(value_str)
                if points <= 0:
                    self.set_status("Error: Please enter a positive number for points.", "error")
                    return
            except (ValueError, TypeError):
                self.set_status("Error: Invalid input. Please enter a whole number for points.", "error")
                return

            core.add_points(self.parent.files, points, reason)
            self.update_points()
            self.update_logs()
            self.set_status(f"Added {points} points for '{reason}'.", "success")
            self.query_one("#add_reason").value = ""
            self.query_one("#add_value").value = ""

        elif event.button.id == "redeem_button":
            name = self.query_one("#redeem_name").value
            value_str = self.query_one("#redeem_value").value
            points, error = core.parse_value_string(value_str)
            if error:
                self.set_status(f"Error: {error}", "error")
                return

            message, error = core.redeem_reward(self.parent.files, name, points)
            if error:
                self.set_status(f"Error: {error}", "error")
            else:
                self.update_points()
                self.update_logs()
                self.set_status(f"Redeemed '{name}' for {points} points.", "success")
            self.query_one("#redeem_name").value = ""
            self.query_one("#redeem_value").value = ""

        elif event.button.id == "commit_button":
            core.commit_session(self.parent.files)
            self.app.pop_screen()

        elif event.button.id == "rollback_button" or event.button.id == "logout_button":
            core.rollback_session(self.parent.files)
            self.app.pop_screen()

class PointSysApp(App):
    """A Textual app to manage the points system."""

    CSS = """
    #dialog {
        padding: 0 1;
        background: $surface;
        border: thick $primary 80%;
        width: 60;
        height: 11;
        align: center middle;
    }
    #question {
        margin-bottom: 2;
    }
    .buttons {
        align: center middle;
        width: 100%;
    }
    """
    SCREENS = {"login": LoginScreen, "account": AccountScreen}

    account_name = None
    files = None

    def on_mount(self) -> None:
        core.setup_data_dir()
        self.push_screen("login")

if __name__ == "__main__":
    app = PointSysApp()
    app.run()