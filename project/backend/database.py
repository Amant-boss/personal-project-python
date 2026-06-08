import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "sports_data.csv")

def ensure_db():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

def read_data() -> pd.DataFrame:
    ensure_db()
    if not os.path.exists(CSV_PATH):
        return pd.DataFrame(columns=[
            "first_name", "last_name", "team", "nationality",
            "position", "matches_played", "goals", "assists", "minutes_played"
        ])
    return pd.read_csv(CSV_PATH)

def save_new_csv(file_bytes: bytes):
    ensure_db()
    with open(CSV_PATH, "wb") as f:
        f.write(file_bytes)

def append_player_record(player_data: dict):
    ensure_db()
    new_row = pd.DataFrame([player_data])
    if not os.path.exists(CSV_PATH):
        new_row.to_csv(CSV_PATH, index=False)
    else:
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)

def update_player_record(old_first: str, old_last: str, updated_data: dict):
    ensure_db()
    df = read_data()
    match_mask = (df["first_name"].str.lower() == old_first.lower()) & (df["last_name"].str.lower() == old_last.lower())
    if not df[match_mask].empty:
        idx = df[match_mask].index[0]
        for col, val in updated_data.items():
            df.at[idx, col] = val
        df.to_csv(CSV_PATH, index=False)
        return True
    return False

def delete_player_record(first_name: str, last_name: str):
    ensure_db()
    df = read_data()
    initial_len = len(df)
    df = df[~((df["first_name"].str.lower() == first_name.lower()) & (df["last_name"].str.lower() == last_name.lower()))]
    if len(df) < initial_len:
        df.to_csv(CSV_PATH, index=False)
        return True
    return False