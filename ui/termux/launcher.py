import os
import json
import sys
import importlib

# Add the root of the repository to the Python path
# This allows us to import modules from the 'projects' directory
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.append(root_dir)

def find_projects():
    """Scans the 'projects' directory and returns a list of valid projects."""
    projects_dir = os.path.join(root_dir, 'projects')
    projects = []
    if not os.path.isdir(projects_dir):
        return projects

    for project_name in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, project_name)
        if os.path.isdir(project_path):
            project_json_path = os.path.join(project_path, 'project.json')
            if os.path.isfile(project_json_path):
                with open(project_json_path, 'r') as f:
                    try:
                        project_data = json.load(f)
                        project_data['path'] = project_path
                        project_data['id'] = project_name
                        projects.append(project_data)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode JSON from {project_json_path}")
    return projects

def launch_project_ui(project_id):
    """Dynamically imports and runs the UI for the selected project."""
    ui_module_name = f"ui.termux.{project_id}_ui"
    try:
        ui_module = importlib.import_module(ui_module_name)
        if hasattr(ui_module, 'run') and callable(ui_module.run):
            ui_module.run()
        else:
            print(f"Error: UI module for '{project_id}' does not have a 'run' function.")
    except ImportError:
        print(f"Error: UI for project '{project_id}' not found.")
    except Exception as e:
        print(f"An error occurred while launching the project: {e}")


def main():
    """Main function for the launcher."""
    projects = find_projects()

    if not projects:
        print("No projects found.")
        return

    print("Available Projects:")
    for i, project in enumerate(projects):
        print(f"  {i + 1}. {project.get('name', 'N/A')} - {project.get('description', 'No description')}")

    while True:
        try:
            choice = input("Enter the number of the project to launch (or 'q' to quit): ")
            if choice.lower() == 'q':
                break

            choice_index = int(choice) - 1
            if 0 <= choice_index < len(projects):
                selected_project = projects[choice_index]
                print(f"Launching {selected_project['name']}...")
                launch_project_ui(selected_project['id'])
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()