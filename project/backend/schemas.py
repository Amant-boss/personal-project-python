from pydantic import BaseModel

class PlayerCreateSchema(BaseModel):
    first_name: str
    last_name: str
    team: str
    nationality: str
    position: str
    matches_played: int
    goals: int
    assists: int
    minutes_played: int

class ComparisonRequestSchema(BaseModel):
    p1: str
    p2: str