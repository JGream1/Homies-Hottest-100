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