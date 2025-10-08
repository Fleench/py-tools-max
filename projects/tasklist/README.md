# Task Management and Procrastination Reporter

This is a simple command-line tool to help you manage your tasks and get a report on your workload. The key feature is the "procrastination report," which tells you if you can afford to delay your tasks.

## How to Use

The main entry point is `main.py`. It reads task and availability data from `data.py` and generates a procrastination report.

To run the application, simply execute `main.py`:

```bash
python main.py
```

## How to Configure

You can configure your tasks and availability by editing the `data.py` file. The file contains two lists: `tasks` and `availability`.

- The `tasks` list contains your tasks, with each task having a name, total hours, completed hours, and a due date.
- The `availability` list contains your available work hours for each day.

## How to Run Tests

The project uses `pytest` for testing. To run the tests, you first need to install `pytest`:

```bash
pip install pytest
```

Then, you can run the tests by executing the following command:

```bash
pytest test-main.py
```
