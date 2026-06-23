from fastapi import FastAPI, UploadFile, File, HTTPException
from schemas import PlayerCreateSchema, ComparisonRequestSchema
from database import read_data, save_new_csv, append_player_record, update_player_record, delete_player_record
import pandas as pd
import numpy as np

app = FastAPI()


@app.get("/players")
def get_all_players():
    df = read_data()
    return df.to_dict(orient="records")


@app.post("/player/add")
def add_player(player: PlayerCreateSchema):
    append_player_record(player.model_dump())
    return {"status": "success"}


@app.put("/player/update")
def update_player(old_first: str, old_last: str, player: PlayerCreateSchema):
    success = update_player_record(old_first, old_last, player.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="Original player record not found")
    return {"status": "success"}


@app.delete("/player/delete")
def delete_player(first_name: str, last_name: str):
    success = delete_player_record(first_name, last_name)
    if not success:
        raise HTTPException(status_code=404, detail="Player record not found")
    return {"status": "success"}


@app.post("/upload")
def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    bytes_data = file.file.read()
    save_new_csv(bytes_data)
    return {"status": "success"}


@app.get("/player/{last_name}/stats")
def get_player_stats(last_name: str):
    df = read_data()
    df_match = df[df["last_name"].str.lower() == last_name.lower()]
    if df_match.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    player_row = df_match.iloc[0]
    player_sport = player_row["sport"]

    # Filter by sport so ranking belongs only to that sport branch
    df_sport = df[df["sport"].str.lower() == player_sport.lower()].copy()
    df_sport["temp_involvements"] = df_sport["goals"] + df_sport["assists"]
    df_sport["rank_val"] = df_sport["temp_involvements"].rank(ascending=False, method="min")

    player_rank = int(df_sport[df_sport["last_name"].str.lower() == last_name.lower()].iloc[0]["rank_val"])

    mins = player_row["minutes_played"]
    goals = player_row["goals"]
    goals_per_90 = round((goals / mins) * 90, 2) if mins > 0 else 0.0
    involvements = int(goals + player_row["assists"])

    return {
        "first_name": player_row["first_name"],
        "last_name": player_row["last_name"],
        "sport": player_sport,
        "team": player_row["team"],
        "position": player_row["position"],
        "nationality": player_row["nationality"],
        "matches_played": int(player_row["matches_played"]),
        "goals": int(goals),
        "assists": int(player_row["assists"]),
        "minutes_played": int(mins),
        "goals_per_90": goals_per_90,
        "goal_involvements": involvements,
        "rank": player_rank
    }


@app.post("/compare")
def compare_players(req: ComparisonRequestSchema):
    df = read_data()
    p1_df = df[df["last_name"].str.lower() == req.p1.lower()]
    p2_df = df[df["last_name"].str.lower() == req.p2.lower()]

    if p1_df.empty or p2_df.empty:
        raise HTTPException(status_code=404, detail="One or both players not found")

    row1 = p1_df.iloc[0]
    row2 = p2_df.iloc[0]
    name1 = row1["last_name"]
    name2 = row2["last_name"]

    return [
        {"metrics": "Matches Played", name1: int(row1["matches_played"]), name2: int(row2["matches_played"])},
        {"metrics": "Goals", name1: int(row1["goals"]), name2: int(row2["goals"])},
        {"metrics": "Assists", name1: int(row1["assists"]), name2: int(row2["assists"])},
        {"metrics": "Goals per 90",
         name1: round((row1["goals"] / row1["minutes_played"]) * 90, 2) if row1["minutes_played"] > 0 else 0,
         name2: round((row2["goals"] / row2["minutes_played"]) * 90, 2) if row2["minutes_played"] > 0 else 0}
    ]


@app.get("/player/{last_name}/predict")
def get_player_prediction(last_name: str):
    df = read_data()
    df_match = df[df["last_name"].str.lower() == last_name.lower()]
    if df_match.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    row = df_match.iloc[0]
    total_goals = row["goals"]
    total_games = row["matches_played"]
    avg_goals = total_goals / total_games if total_games > 0 else 0

    trend = []
    current_trend = avg_goals

    for g in range(1, 6):
        noise = np.random.normal(0, 0.1)
        hist_g = max(0.0, round(avg_goals + noise, 2))
        current_trend = round(current_trend * 1.02, 2)
        trend.append({
            "games": f"Game {g}",
            "historical_goals": hist_g,
            "predicted_trend": current_trend
        })

    for p in range(6, 9):
        current_trend = round(current_trend * 1.03, 2)
        trend.append({
            "games": f"Next {p - 5}",
            "historical_goals": None,
            "predicted_trend": current_trend
        })

    return trend