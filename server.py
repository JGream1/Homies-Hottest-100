from fastapi import FastAPI 
from pydantic import BaseModel 
import json 

app = FastAPI() 

class TableData(BaseModel): 
    rows: list 

@app.post("/submit") 
def submit(data: TableData): 
    with open("submissions.json", "a") as f:
        f.write(json.dumps(data.rows) + "\n")
    return {"status": "ok"}

@app.get("/submissions")
def get_submissions():
    try:
        with open("submissions.json", "r") as f:
            lines = f.readlines()
        return {"submissions": [json.loads(line) for line in lines]}
    except FileNotFoundError:
        return {"submissions": []}