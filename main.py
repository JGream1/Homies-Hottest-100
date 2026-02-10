from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from db import init_db, SessionLocal, SubmissionRow, CleanedSong, Top50Row
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

    # Check if this person/device already submitted
    existing = (
        db.query(SubmissionRow)
          .filter(
              (SubmissionRow.homie == name) |
              (SubmissionRow.unique_id == unique_id)
          )
          .first()
    )

    if existing:
        return {"error": "already_submitted"}

    # Save rows
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


# Reset submissions DBs
@app.post('/reset')
def reset(db: Session = Depends(get_db)):
    db.query(SubmissionRow).delete()
    db.query(CleanedSong).delete()
    db.commit()
    return {"status": "reset_complete"}


# Reset top 50 list DB
@app.post('/reset_top50')
def reset_top50(db: Session = Depends(get_db)):
    db.query(Top50Row).delete()
    db.commit()
    return {"status": "top50_reset_complete"}


# Reset submissions data
@app.post('/reset')
def reset(db: Session = Depends(get_db)):
    # Clear old shortlist submissions
    db.query(SubmissionRow).delete()

    # Clear cleaned shortlist songs
    db.query(CleanedSong).delete()

    db.commit()
    return {"status": "reset_complete"}


# Return list of cleaned song dicts from DB
@app.get('/cleaned_songs')
def cleaned_songs(db: Session = Depends(get_db)):
    rows = db.query(CleanedSong).all()
    return [
        {
            "song": r.song,
            "artist": r.artist,
            "notes": r.notes,
            "image_url": r.image_url
        }
        for r in rows
    ]


# Add homie's top 50 lists to DB
@app.post('/submit_top50')
def submit_top50(payload: dict, db: Session = Depends(get_db)):
    name = payload['name']
    unique_id = payload['uniqueID']
    ranked = payload['ranked']  # list of 50 items (or nulls)

    # Prevent duplicate submissions
    existing = (
        db.query(Top50Row)
          .filter(
              (Top50Row.homie == name) |
              (Top50Row.unique_id == unique_id)
          )
          .first()
    )
    if existing:
        return {"error": "already_submitted"}

    # Save each ranking row
    for index, item in enumerate(ranked, start=1):
        if item is None:
            continue

        db_row = Top50Row(
            homie=name,
            unique_id=unique_id,
            rank=index,
            song=item['song'],
            artist=item['artist'],
            image_url=item['image_url']
        )
        db.add(db_row)

    db.commit()
    return {"status": "ok"}