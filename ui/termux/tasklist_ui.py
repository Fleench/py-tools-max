import os
import datetime
import sys
import copy

# Add project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.append(root_dir)

from projects.tasklist import core
from projects.tasklist import data as tasklist_data

def view_tasks(data):
    """Displays the list of tasks."""
    print("\n--- Your Tasks ---")
    tasks = data.get('tasks', [])
    if not tasks:
        print("No tasks found.")
        return

    for i, task in enumerate(tasks):
        due_date = task['due_date'].strftime('%Y-%m-%d') if isinstance(task['due_date'], datetime.date) else 'N/A'
        print(f"{i + 1}. {task['name']} (Due: {due_date}) - {task['completed_hours']}/{task['total_hours']} hours completed")

def add_task(data):
    """Adds a new task to the in-memory data object."""
    print("\n--- Add a New Task ---")
    try:
        name = input("Task name: ")
        total_hours = float(input("Total hours required: "))
        completed_hours = float(input("Hours already completed: "))
        due_date_str = input("Due date (YYYY-MM-DD): ")
        due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()

        new_task = core.make_task(name, total_hours, completed_hours, due_date)
        data['tasks'].append(new_task)
        print("Task added successfully for this session!")
    except ValueError:
        print("Invalid input. Please check the format of your entries.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_reports(data):
    """Shows the reports menu and generates the selected report."""
    while True:
        print("\n--- Reports Menu ---")
        print("1. Basic Report")
        print("2. Procrastination Report")
        print("q. Back to Main Menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            report = core.basic_report(data['availability'], data['tasks'])
            print(f"\n{report}")
        elif choice == '2':
            report = core.procrastination_report(data['availability'], data['tasks'])
            print(f"\n{report}")
        elif choice.lower() == 'q':
            break
        else:
            print("Invalid choice. Please try again.")

def run():
    """Main function to run the tasklist UI."""
    # Deepcopy the data from the module to avoid modifying the original data in the module
    data = {
        "tasks": copy.deepcopy(tasklist_data.tasks),
        "availability": copy.deepcopy(tasklist_data.availability)
    }

    print("Welcome to the Tasklist!")

    while True:
        print("\n--- Main Menu ---")
        print("1. View Tasks")
        print("2. Add Task")
        print("3. Generate Reports")
        print("q. Quit")

        choice = input("Enter your choice: ")

        if choice == '1':
            view_tasks(data)
        elif choice == '2':
            add_task(data)
        elif choice == '3':
            generate_reports(data)
        elif choice.lower() == 'q':
            print("Exiting Tasklist.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    run()