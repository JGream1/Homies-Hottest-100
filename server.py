from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jgream1.github.io",
        "https://jgream1.github.io/Homies-Hottest-100"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TableData(BaseModel):
    name: str
    uniqueID: str
    rows: list

def load_submissions():
    if not os.path.exists("submissions.json"):
        return []
    with open("submissions.json", "r") as f:
        return [json.loads(line) for line in f]

# Submit shortlist data
@app.post("/submit")
def submit(data: TableData):
    submissions = load_submissions()

    for entry in submissions:
        if entry["name"] == data.name or entry["uniqueID"] == data.uniqueID:
            return {"error": "already_submitted"}

    new_entry = {
        "name": data.name,
        "uniqueID": data.uniqueID,
        "rows": data.rows
    }

    with open("submissions.json", "a") as f:
        f.write(json.dumps(new_entry) + "\n")

    return {"status": "ok"}

# Return submitted shortlist data
@app.get("/submissions")
def get_submissions():
    return {"submissions": load_submissions()}

# Reset submissions data
@app.post("/reset")
def reset():
    open("submissions.json", "w").close()
    return {"status": "reset_complete"}