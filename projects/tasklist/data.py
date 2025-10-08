import datetime
from projects.tasklist.core import make_task as task, make_day as day


tasks = [
    task("Math Week 5", 4, 3, datetime.date(2025, 9, 19)),
    task("English Paragraph", 1, 1, datetime.date(2025, 9, 17)),
    task("Music DNA 2", 2, 1, datetime.date(2025, 9, 19)),
    task("Triangle CS", 1, 0.75, datetime.date(2025, 9, 22)),
    task("Quiz 2 Math", 1, 1, datetime.date(2025, 9, 19)),
]

availability = [
    day(datetime.date(2025, 9, 15), 2),
    day(datetime.date(2025, 9, 16), 5),
    day(datetime.date(2025, 9, 17), 4.5),
    day(datetime.date(2025, 9, 18), 4),
    day(datetime.date(2025, 9, 19), 2),
    day(datetime.date(2025, 9, 20), 10),
    day(datetime.date(2025, 9, 21), 0),
    day(datetime.date(2025, 9, 22), 2),
    day(datetime.date(2025, 9, 23), 4),
]