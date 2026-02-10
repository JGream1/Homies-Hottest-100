from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from db import init_db, SessionLocal, SubmissionRow
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

class TableData(BaseModel):
    name: str
    uniqueID: str
    rows: list

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_submissions():
    if not os.path.exists('submissions.json'):
        return []
    with open('submissions.json', 'r') as f:
        return [json.loads(line) for line in f]


app = FastAPI(lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'https://jgream1.github.io',
        'https://jgream1.github.io/Homies-Hottest-100'
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


# Submit shortlist data
@app.post('/submit')
def submit(payload: dict, db: Session = Depends(get_db)):
    name = payload['name']
    unique_id = payload['uniqueID']

    for row in payload['rows']:
        song, artist, notes = (row + ['', '', ''])[:3]
        if not any(x.strip() for x in [song, artist, notes]):
            continue

        db_row = SubmissionRow(
            homie=name,
            unique_id=unique_id,
            song=song,
            artist=artist,
            notes=notes
        )
        db.add(db_row)

    db.commit()
    return {'status': 'ok'}


# Return submitted shortlist data
@app.get('/submissions')
def get_submissions(db: Session = Depends(get_db)):
    rows = db.query(SubmissionRow).all()

    submissions = {}
    for r in rows:
        key = (r.homie, r.unique_id)
        submissions.setdefault(key, []).append([r.song, r.artist, r.notes])

    result = {
        'submissions': [
            {
                'name': homie,
                'uniqueID': uid,
                'rows': rows_list
            }
            for (homie, uid), rows_list in submissions.items()
        ]
    }
    return result


# Reset submissions data
@app.post('/reset')
def reset():
    open('submissions.json', 'w').close()
    return {'status': 'reset_complete'}