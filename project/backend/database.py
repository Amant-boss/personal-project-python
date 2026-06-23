import os
import sqlite3
import io
import pandas as pd

# Dummy line to satisfy IDE module usage requirements
_ = pd.DataFrame()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "players.db")


def ensure_db():
    """Ensures the data directory exists and initializes the SQLite database file."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Connecting to the file path automatically creates 'players.db' if it doesn't exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the internal table structure if it hasn't been made yet
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            first_name TEXT,
            last_name TEXT,
            sport TEXT,
            team TEXT,
            nationality TEXT,
            position TEXT,
            matches_played INTEGER,
            goals INTEGER,
            assists INTEGER,
            minutes_played INTEGER
        )
    """)
    conn.commit()
    conn.close()


# CRITICAL: This line forces Python to build the players.db file immediately on startup
ensure_db()


def read_data() -> pd.DataFrame:
    """Reads the SQL database and returns it as a Pandas DataFrame for the API."""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM players", conn)
    conn.close()
    return df


def save_new_csv(file_bytes: bytes):
    """Parses an uploaded CSV file and completely overwrites the SQL rows
    while safely preserving the original schema rules."""
    ensure_db()
    df = pd.read_csv(io.BytesIO(file_bytes))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # FIX: Clear out the rows instead of dropping the table entirely
    cursor.execute("DELETE FROM players")
    conn.commit()

    # Append the new CSV data safely into the verified table structure
    df.to_sql("players", conn, if_exists="append", index=False)
    conn.close()


def append_player_record(player_data: dict):
    """Inserts a new manual player row directly into the SQLite table."""
    ensure_db()
    df = pd.DataFrame([player_data])
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("players", conn, if_exists="append", index=False)
    conn.close()


def update_player_record(old_first: str, old_last: str, updated_data: dict):
    """Updates an existing player matching their unique first and last name combination."""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        UPDATE players 
        SET first_name=?, last_name=?, sport=?, team=?, nationality=?, position=?, 
            matches_played=?, goals=?, assists=?, minutes_played=?
        WHERE LOWER(first_name) = LOWER(?) AND LOWER(last_name) = LOWER(?)
    """
    cursor.execute(query, (
        updated_data["first_name"], updated_data["last_name"], updated_data["sport"], updated_data["team"],
        updated_data["nationality"], updated_data["position"], updated_data["matches_played"],
        updated_data["goals"], updated_data["assists"], updated_data["minutes_played"],
        old_first, old_last
    ))

    # Check if a row was actually altered
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0


def delete_player_record(first_name: str, last_name: str):
    """Deletes a targeted player record matching the provided first and last name."""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM players WHERE LOWER(first_name) = LOWER(?) AND LOWER(last_name) = LOWER(?)",
        (first_name, last_name)
    )

    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0