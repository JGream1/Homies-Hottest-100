import os
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class SubmissionRow(Base):
    __tablename__ = 'submission_rows'

    id = Column(Integer, primary_key=True, index=True)
    homie = Column(String(100), index=True)
    unique_id = Column(String(100), index=True)
    song = Column(Text)
    artist = Column(Text)
    notes = Column(Text)

class CleanedSong(Base):
    __tablename__ = 'cleaned_songs'

    id = Column(Integer, primary_key=True, index=True)
    song = Column(Text, index=True)
    artist = Column(Text, index=True)
    notes = Column(Text)
    image_url = Column(Text)

class Top50Row(Base):
    __tablename__ = 'top50_rows'

    id = Column(Integer, primary_key=True, index=True)
    homie = Column(String(100), index=True)
    unique_id = Column(String(100), index=True)
    rank = Column(Integer, index=True)
    song = Column(Text)
    artist = Column(Text)
    image_url = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)