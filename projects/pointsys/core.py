import os
import datetime
import struct
import re
import shutil

# --- Configuration ---
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CORE_DIR, "data")
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
        return True, None
    except IOError as e:
        return False, f"Error writing points file: {e}"

def append_log(filepath, entry):
    """Appends a timestamped entry to the log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_entry = f"[{timestamp}] {entry}"
    try:
        with open(filepath, 'a') as f:
            f.write(full_entry + "\n")
        return True, None
    except IOError as e:
        return False, f"Error writing to log file: {e}"

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
    shutil.move(files["points_tmp"], files["points"])
    shutil.move(files["log_tmp"], files["log"])
    return "Changes saved successfully."

def rollback_session(files):
    """Discards changes by deleting .tmp files."""
    if os.path.exists(files["points_tmp"]): os.remove(files["points_tmp"])
    if os.path.exists(files["log_tmp"]): os.remove(files["log_tmp"])
    return "Session changes have been discarded."

def has_crashed(account_name):
    files = get_account_files(account_name)
    return os.path.exists(files["points_tmp"]) or os.path.exists(files["log_tmp"])

# --- Core Feature Functions ---

def add_points(files, points_to_add, reason):
    """Handles the logic for adding points."""
    current_points = read_points(files["points_tmp"])
    new_total = current_points + points_to_add
    write_points(files["points_tmp"], new_total)
    append_log(files["log_tmp"], f"ADDED: +{points_to_add} points ({reason})")
    return f"Points added to current session."

def redeem_reward(files, name, points_cost):
    """Handles the logic for redeeming a reward."""
    current_points = read_points(files["points_tmp"])
    if current_points >= points_cost:
        new_total = current_points - points_cost
        write_points(files["points_tmp"], new_total)
        append_log(files["log_tmp"], f"REDEEMED: '{name}' for {points_cost} points")
        return "Reward redeemed in current session.", None
    else:
        return None, f"Sorry, you don't have enough points. You need {points_cost - current_points} more."


def view_logs(files):
    """Displays the logs from the current session's .tmp file."""
    log_file = files["log_tmp"]
    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        with open(log_file, 'r') as f:
            return f.read()
    else:
        return "No transactions in this session yet."

def create_account(account_name):
    """Creates a new account."""
    files = get_account_files(account_name)
    if not os.path.exists(files["points"]):
        write_points(files["points"], 0) # Create empty points file
        open(files["log"], 'w').close() # Create empty log file
        return f"Account '{account_name}' created."
    return f"Account '{account_name}' already exists."

def account_exists(account_name):
    files = get_account_files(account_name)
    return os.path.exists(files["points"])