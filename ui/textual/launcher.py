import os
import json
import sys
import subprocess
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Button
from textual.containers import Container


class ProjectListItem(ListItem):
    """A ListItem that holds project data."""

    def __init__(self, project: dict) -> None:
        super().__init__(Static(project["data"]["name"]))
        self.project = project


class ProjectLauncher(App):
    """A Textual project launcher."""

    CSS_PATH = "launcher.css"

    def __init__(self):
        super().__init__()
        self.projects = self.find_projects()
        self.selected_project = None

    def find_projects(self):
        """Finds projects in the 'projects' directory."""
        projects = []
        # Construct a path to the 'projects' directory relative to this script's location
        script_dir = os.path.dirname(os.path.realpath(__file__))
        project_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "projects"))

        if not os.path.exists(project_dir):
            return []
        for project_name in os.listdir(project_dir):
            project_path = os.path.join(project_dir, project_name)
            if os.path.isdir(project_path):
                project_json_path = os.path.join(project_path, "project.json")
                if os.path.exists(project_json_path):
                    try:
                        with open(project_json_path, "r") as f:
                            project_data = json.load(f)
                            # Basic validation
                            if "name" in project_data and "version" in project_data and "description" in project_data:
                                projects.append({"data": project_data, "dir_name": project_name})
                            else:
                                # Handle cases where project.json is missing required fields
                                print(f"Warning: '{project_json_path}' is missing required fields.")
                    except json.JSONDecodeError:
                        # Handle cases where project.json is not valid JSON
                        print(f"Warning: Could not decode JSON from '{project_json_path}'.")
                    except Exception as e:
                        # Handle other file reading errors
                        print(f"Warning: Could not read '{project_json_path}': {e}")
        return projects

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(name="Project Launcher")
        with Container(id="main-container"):
            with Container(id="left-pane"):
                yield Static("Select a project to see details", id="project-details")
                yield Button("Launch Project", id="launch-button", disabled=True)
            with Container(id="right-pane"):
                # Display the name from the JSON data
                yield ListView(
                    *[ProjectListItem(project) for project in self.projects],
                    id="project-list"
                )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection."""
        # event.item is the ProjectListItem instance, which has the project data
        if not isinstance(event.item, ProjectListItem):
            # This case should ideally not be hit if selection is handled correctly
            self.query_one("#project-details").update("Select a project to see details")
            self.query_one("#launch-button").disabled = True
            self.selected_project = None
            return

        self.selected_project = event.item.project
        project_data = self.selected_project["data"]
        details = f"""
Name: {project_data["name"]}
Version: {project_data["version"]}

Description:
{project_data["description"]}
"""
        self.query_one("#project-details").update(details)
        self.query_one("#launch-button").disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "launch-button" and self.selected_project:
            project_dir_name = self.selected_project["dir_name"]

            # Construct absolute path to the UI file
            script_dir = os.path.dirname(os.path.realpath(__file__))
            ui_file = os.path.join(script_dir, f"{project_dir_name.lower()}_ui.py")

            if os.path.exists(ui_file):
                self.suspend_process()
                try:
                    # Use subprocess.run and capture output
                    result = subprocess.run(
                        [sys.executable, ui_file],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except subprocess.CalledProcessError as e:
                    # Display the captured stderr for better debugging
                    error_message = f"Error running '{project_dir_name}':\n{e.stderr}"
                    self.query_one("#project-details").update(error_message)
                    self.query_one("#launch-button").disabled = True
                finally:
                    self.resume_process()
            else:
                self.query_one("#project-details").update(f"Error: UI file not found for '{project_dir_name}'")
                self.query_one("#launch-button").disabled = True

if __name__ == "__main__":
    app = ProjectLauncher()
    app.run()