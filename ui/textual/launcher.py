import os
import json
import sys
import subprocess
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, ListView, ListItem, Button
from textual.containers import Container

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
                    with open(project_json_path, "r") as f:
                        project_data = json.load(f)
                        # Store both the JSON data and the directory name
                        projects.append({"data": project_data, "dir_name": project_name})
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
                    *[ListItem(Static(project["data"]["name"])) for project in self.projects],
                    id="project-list"
                )
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        """Handle project selection."""
        selected_index = event.list_view.index
        self.selected_project = self.projects[selected_index]
        project_data = self.selected_project["data"]
        details = f"""
Name: {project_data['name']}
Version: {project_data['version']}

Description:
{project_data['description']}
"""
        self.query_one("#project-details").update(details)
        self.query_one("#launch-button").disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "launch-button" and self.selected_project:
            # Use the directory name for the UI file path to avoid case issues
            project_dir_name = self.selected_project["dir_name"]
            ui_file = f"ui/textual/{project_dir_name}_ui.py"

            if os.path.exists(ui_file):
                self.app.suspend_process()
                try:
                    # Use subprocess.run for better process management
                    subprocess.run([sys.executable, ui_file], check=True)
                except subprocess.CalledProcessError as e:
                    # This will be seen after resuming
                    self.query_one("#project-details").update(f"Error running {project_dir_name}:\n{e}")
                    self.query_one("#launch-button").disabled = True
                finally:
                    self.app.resume_process()
            else:
                self.query_one("#project-details").update(f"Error: UI file not found for '{project_dir_name}'")
                self.query_one("#launch-button").disabled = True

if __name__ == "__main__":
    app = ProjectLauncher()
    app.run()