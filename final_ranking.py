from db import SessionLocal, CleanedSong
import requests
import re
import pandas as pd


##### CLEAN SONGS FROM SUBMISSIONS #####

url = 'https://homies-hottest-100.onrender.com/top50_submissions'
data = requests.get(url).json()

print(data)