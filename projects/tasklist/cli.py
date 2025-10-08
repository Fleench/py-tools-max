import core
import data

def main():
    """
    Main function to run the CLI reports.
    """
    print("--- Running Basic Report ---")
    report = core.basic_report(data.availability, data.tasks)
    print(report)

    print("\n--- Running Procrastination Report ---")
    procrastination = core.procrastination_report(data.availability, data.tasks)
    print(procrastination)

if __name__ == "__main__":
    main()