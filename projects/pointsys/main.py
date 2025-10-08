import os
import datetime
import struct
import re
import shutil

# --- Configuration ---
DATA_DIR = "data"
LAST_ACCOUNT_FILE = os.path.join(DATA_DIR, "last_account.txt")

# Conversion rates for reward calculation
DOLLAR_TO_POINTS = 100
MINUTE_TO_POINTS = 10

# --- Helper Functions ---

def setup_data_dir():
    """Ensures the data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_account_files(account_name):
    """Generates a dictionary of file paths for a given account name."""
    base = os.path.join(DATA_DIR, account_name)
    return {
        "points": f"{base}-points.dat",
        "log": f"{base}-central_log.txt",
        "points_tmp": f"{base}-points.dat.tmp",
        "log_tmp": f"{base}-central_log.txt.tmp",
    }

def read_points(filepath):
    """Reads an integer from a binary file. Returns 0 if file doesn't exist."""
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'rb') as f:
            # Reads 4 bytes and unpacks them into an integer
            return struct.unpack('i', f.read(4))[0]
    except (IOError, struct.error):
        return 0

def write_points(filepath, points):
    """Writes an integer to a binary file."""
    try:
        with open(filepath, 'wb') as f:
            # Packs an integer into 4 bytes
            f.write(struct.pack('i', points))
    except IOError as e:
        print(f"Error writing points file: {e}")

def append_log(filepath, entry):
    """Appends a timestamped entry to the log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_entry = f"[{timestamp}] {entry}"
    try:
        with open(filepath, 'a') as f:
            f.write(full_entry + "\n")
    except IOError as e:
        print(f"Error writing to log file: {e}")

def parse_value_string(value_str):
    """
    Parses a string like '$20', '1h30m', '1d' and returns the point cost.
    Returns (points, error_message).
    """
    value_str = value_str.strip().lower()

    # Check for monetary value
    if value_str.startswith('$'):
        try:
            amount = abs(float(value_str[1:]))
            return int(amount * DOLLAR_TO_POINTS), None
        except ValueError:
            return None, "Invalid dollar amount."

    # Check for time value
    total_minutes = 0
    time_parts = re.findall(r'(\d+)\s*(d|h|m)', value_str)

    if not time_parts and re.match(r'^\d+$', value_str): # Handle plain minutes
         time_parts = [(value_str, 'm')]

    if not time_parts:
        return None, "Invalid format. Use '$', 'd', 'h', 'm' (e.g., '$25', '1h 30m')."

    for value, unit in time_parts:
        value = int(value)
        if unit == 'd':
            total_minutes += value * 24 * 60
        elif unit == 'h':
            total_minutes += value * 60
        elif unit == 'm':
            total_minutes += value

    return total_minutes * MINUTE_TO_POINTS, None


# --- Session and Account Management ---

def get_last_account():
    """Gets the last used account name."""
    if os.path.exists(LAST_ACCOUNT_FILE):
        with open(LAST_ACCOUNT_FILE, 'r') as f:
            return f.read().strip()
    return None

def set_last_account(account_name):
    """Sets the last used account name."""
    with open(LAST_ACCOUNT_FILE, 'w') as f:
        f.write(account_name)

def start_session(files):
    """Copies main files to .tmp files to begin a session."""
    shutil.copyfile(files["points"], files["points_tmp"]) if os.path.exists(files["points"]) else write_points(files["points_tmp"], 0)
    shutil.copyfile(files["log"], files["log_tmp"]) if os.path.exists(files["log"]) else open(files["log_tmp"], 'w').close()

def commit_session(files):
    """Commits changes by replacing main files with .tmp files."""
    print("Saving changes...")
    shutil.move(files["points_tmp"], files["points"])
    shutil.move(files["log_tmp"], files["log"])
    print("Changes saved successfully.")

def rollback_session(files):
    """Discards changes by deleting .tmp files."""
    print("Discarding changes...")
    if os.path.exists(files["points_tmp"]): os.remove(files["points_tmp"])
    if os.path.exists(files["log_tmp"]): os.remove(files["log_tmp"])
    print("Session changes have been discarded.")

def handle_crash_recovery(account_name):
    """Handles the three-option crash recovery on startup."""
    files = get_account_files(account_name)
    if not os.path.exists(files["points_tmp"]) and not os.path.exists(files["log_tmp"]):
        return # No crash detected

    while True:
        print("\n--- Unsaved Session Found ---")
        print("An unsaved session was found from a previous run.")
        print("What would you like to do?")
        print("1. Save found data (Commit and start fresh)")
        print("2. Load found data (Continue the session)")
        print("3. Discard found data (Delete and start fresh)")
        choice = input("> ")

        if choice == '1':
            commit_session(files)
            return
        elif choice == '2':
            # Do nothing, the .tmp files will be used by the session
            print("Loading previous session...")
            return
        elif choice == '3':
            rollback_session(files)
            return
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

# --- Core Feature Functions ---

def add_points(files):
    """Handles the logic for adding points."""
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
            current_points = read_points(files["points_tmp"])
            new_total = current_points + points_to_add
            write_points(files["points_tmp"], new_total)
            append_log(files["log_tmp"], f"ADDED: +{points_to_add} points ({reason})")
            print("Points added to current session.")
        else:
            print("Action cancelled.")

    except ValueError:
        print("Invalid input. Please enter a whole number for points.")

def redeem_reward(files):
    """Handles the logic for redeeming a reward."""
    name = input("Enter the name of the reward: ")
    value_str = input("Enter the value of the reward (e.g., $20, 1h 30m): ")

    points_cost, error = parse_value_string(value_str)
    if error:
        print(f"Error: {error}")
        return

    current_points = read_points(files["points_tmp"])

    print(f"\nThe reward '{name}' costs {points_cost} points.")
    print(f"You currently have {current_points} points in this session.")

    if current_points >= points_cost:
        consent = input("Do you want to redeem this reward? (y/n): ").lower()
        if consent == 'y':
            new_total = current_points - points_cost
            write_points(files["points_tmp"], new_total)
            append_log(files["log_tmp"], f"REDEEMED: '{name}' for {points_cost} points")
            print("Reward redeemed in current session.")
        else:
            print("Action cancelled.")
    else:
        print(f"Sorry, you don't have enough points. You need {points_cost - current_points} more.")


def view_logs(files):
    """Displays the logs from the current session's .tmp file."""
    log_file = files["log_tmp"]
    print(f"\n--- Transaction Log for this Session ---")
    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        with open(log_file, 'r') as f:
            print(f.read())
    else:
        print("No transactions in this session yet.")
    print("----------------------------------------")


def switch_account():
    """Handles switching, creating, and loading user accounts."""
    new_account = input("Enter account name to switch to or create: ").strip()
    if not new_account:
        print("Account name cannot be empty.")
        return None

    files = get_account_files(new_account)
    if not os.path.exists(files["points"]):
        consent = input(f"Account '{new_account}' not found. Create it? (y/n): ").lower()
        if consent == 'y':
            write_points(files["points"], 0) # Create empty points file
            open(files["log"], 'w').close() # Create empty log file
            print(f"Account '{new_account}' created.")
        else:
            print("Account switch cancelled.")
            return None

    set_last_account(new_account)
    print(f"Switched to account: {new_account}")
    return new_account

# --- Main Program Loop ---

def main():
    """The main function to run the terminal application."""
    setup_data_dir()

    current_account = get_last_account()
    if not current_account:
        print("No accounts found. Let's create one.")
        current_account = switch_account()
        if not current_account:
            print("Cannot proceed without an account. Exiting.")
            return

    print(f"--- Welcome to Your Rewards Manager ---")
    print(f"Loading last used account: {current_account}")

    handle_crash_recovery(current_account)

    files = get_account_files(current_account)
    start_session(files)

    while True:
        points = read_points(files["points_tmp"])
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
            add_points(files)
        elif choice == "2":
            redeem_reward(files)
        elif choice == "3":
            # End current session before switching
            rollback_session(files) # Discard any uncommitted changes
            new_account_name = switch_account()
            if new_account_name:
                current_account = new_account_name
                files = get_account_files(current_account)
                handle_crash_recovery(current_account)
                start_session(files)
        elif choice == "4":
            view_logs(files)
        elif choice == "5":
            # End of session logic
            print("\n--- End of Session ---")
            original_log_size = os.path.getsize(files["log"]) if os.path.exists(files["log"]) else 0

            if os.path.exists(files["log_tmp"]):
                with open(files["log_tmp"], 'r') as f:
                    f.seek(original_log_size)
                    new_actions = f.read().strip()
                    if new_actions:
                        print("Logged actions this session:")
                        print(new_actions)
                    else:
                        print("No new actions were logged this session.")

            consent = input("Record actions? (y/n): ").lower()
            if consent == 'y':
                commit_session(files)
            else:
                rollback_session(files)

            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please enter a number from 1 to 5.")

if __name__ == "__main__":
    main()
