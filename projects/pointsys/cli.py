import os
import core

def handle_crash_recovery(account_name):
    """Handles the three-option crash recovery on startup."""
    if not core.has_crashed(account_name):
        return # No crash detected

    files = core.get_account_files(account_name)
    while True:
        print("\n--- Unsaved Session Found ---")
        print("An unsaved session was found from a previous run.")
        print("What would you like to do?")
        print("1. Save found data (Commit and start fresh)")
        print("2. Load found data (Continue the session)")
        print("3. Discard found data (Delete and start fresh)")
        choice = input("> ")

        if choice == '1':
            print(core.commit_session(files))
            return
        elif choice == '2':
            print("Loading previous session...")
            return
        elif choice == '3':
            print(core.rollback_session(files))
            return
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

def add_points_cli(files):
    """Handles the CLI logic for adding points."""
    reason = input("Enter a name/reason for these points: ")
    value_str = input("Enter the number of points to add: ")

    try:
        points_to_add = int(value_str)
        if points_to_add <= 0:
            print("Please enter a positive number.")
            return

        print(f"\nYou are about to add {points_to_add} points for '{reason}'.")
        consent = input("Is this correct? (y/n): ").lower()

        if consent == 'y':
            message = core.add_points(files, points_to_add, reason)
            print(message)
        else:
            print("Action cancelled.")

    except ValueError:
        print("Invalid input. Please enter a whole number for points.")

def redeem_reward_cli(files):
    """Handles the CLI logic for redeeming a reward."""
    name = input("Enter the name of the reward: ")
    value_str = input("Enter the value of the reward (e.g., $20, 1h 30m): ")

    points_cost, error = core.parse_value_string(value_str)
    if error:
        print(f"Error: {error}")
        return

    current_points = core.read_points(files["points_tmp"])

    print(f"\nThe reward '{name}' costs {points_cost} points.")
    print(f"You currently have {current_points} points in this session.")

    if current_points >= points_cost:
        consent = input("Do you want to redeem this reward? (y/n): ").lower()
        if consent == 'y':
            message, error_msg = core.redeem_reward(files, name, points_cost)
            if error_msg:
                print(error_msg)
            else:
                print(message)
        else:
            print("Action cancelled.")
    else:
        print(f"Sorry, you don't have enough points. You need {points_cost - current_points} more.")


def view_logs_cli(files):
    """Displays the logs from the current session's .tmp file."""
    print(f"\n--- Transaction Log for this Session ---")
    logs = core.view_logs(files)
    print(logs)
    print("----------------------------------------")


def switch_account_cli():
    """Handles switching, creating, and loading user accounts."""
    new_account = input("Enter account name to switch to or create: ").strip()
    if not new_account:
        print("Account name cannot be empty.")
        return None

    if not core.account_exists(new_account):
        consent = input(f"Account '{new_account}' not found. Create it? (y/n): ").lower()
        if consent == 'y':
            print(core.create_account(new_account))
        else:
            print("Account switch cancelled.")
            return None

    core.set_last_account(new_account)
    print(f"Switched to account: {new_account}")
    return new_account

def main():
    """The main function to run the terminal application."""
    core.setup_data_dir()

    current_account = core.get_last_account()
    if not current_account:
        print("No accounts found. Let's create one.")
        current_account = switch_account_cli()
        if not current_account:
            print("Cannot proceed without an account. Exiting.")
            return

    print(f"--- Welcome to Your Rewards Manager ---")
    print(f"Loading last used account: {current_account}")

    handle_crash_recovery(current_account)

    files = core.get_account_files(current_account)
    core.start_session(files)

    while True:
        points = core.read_points(files["points_tmp"])
        print("\n==================================")
        print(f"Account: {current_account} | Session Points: {points}")
        print("==================================")
        print("Choose an option:")
        print("  1. Add Points")
        print("  2. Redeem a Reward")
        print("  3. Switch/Create Account")
        print("  4. View Session Log")
        print("  5. Exit")

        choice = input("> ")

        if choice == "1":
            add_points_cli(files)
        elif choice == "2":
            redeem_reward_cli(files)
        elif choice == "3":
            # End current session before switching
            print(core.rollback_session(files)) # Discard any uncommitted changes
            new_account_name = switch_account_cli()
            if new_account_name:
                current_account = new_account_name
                files = core.get_account_files(current_account)
                handle_crash_recovery(current_account)
                core.start_session(files)
        elif choice == "4":
            view_logs_cli(files)
        elif choice == "5":
            # End of session logic
            print("\n--- End of Session ---")
            original_log_size = os.path.getsize(files["log"]) if os.path.exists(files["log"]) else 0

            if os.path.exists(files["log_tmp"]):
                with open(files["log_tmp"], 'r') as f:
                    # this logic is UI specific, so it stays here
                    f.seek(original_log_size)
                    new_actions = f.read().strip()
                    if new_actions:
                        print("Logged actions this session:")
                        print(new_actions)
                    else:
                        print("No new actions were logged this session.")

            consent = input("Record actions? (y/n): ").lower()
            if consent == 'y':
                print(core.commit_session(files))
            else:
                print(core.rollback_session(files))

            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please enter a number from 1 to 5.")

if __name__ == "__main__":
    main()