import pytest
from textual.pilot import Pilot
from ui.textual.tasklist_ui import TasklistApp, TaskListItem
from projects.tasklist.data import tasks as initial_tasks

@pytest.mark.asyncio
async def test_task_selection_is_robust():
    """
    Test that selecting a task from the list view works correctly
    and uses the robust, data-driven approach.
    """
    app = TasklistApp()
    async with app.run_test() as pilot:
        # Wait for the app to settle initially
        await pilot.pause()

        # 1. Verify that the list is populated with the correct custom widget
        list_view = app.query_one("#task-list")
        assert len(list_view.children) == len(initial_tasks)
        assert all(isinstance(child, TaskListItem) for child in list_view.children)

        # 2. Simulate selecting the first item by clicking it
        await pilot.click(TaskListItem, control=list_view)
        await pilot.pause()

        # 3. Verify the details view is updated with the correct task data
        details_widget = app.query_one("#task-details")
        selected_task = initial_tasks[0]
        expected_details = f"""
Name: {selected_task['name']}
Due: {selected_task['due_date'].strftime('%Y-%m-%d')}
Hours: {selected_task['completed_hours']} / {selected_task['total_hours']}
"""
        assert str(details_widget.render()).strip() == expected_details.strip()

        # 4. Select another item and verify again
        # To click the second item, we can use an offset
        await pilot.click(TaskListItem, control=list_view, offset=(0, 1))
        await pilot.pause()

        selected_task = initial_tasks[1]
        expected_details_2 = f"""
Name: {selected_task['name']}
Due: {selected_task['due_date'].strftime('%Y-%m-%d')}
Hours: {selected_task['completed_hours']} / {selected_task['total_hours']}
"""
        assert str(details_widget.render()).strip() == expected_details_2.strip()