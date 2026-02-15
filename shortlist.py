from db import SessionLocal, CleanedSong
import requests
import re
import pandas as pd


##### CLEAN SONGS FROM SUBMISSIONS #####

url = 'https://homies-hottest-100.onrender.com/submissions'
data = requests.get(url).json()

# Clean free text values
def clean_text(s):
    if not isinstance(s, str):
        return ''
    
    s = s.upper()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'\s+', ' ', s)

    return s.strip()

# Flatten and remove empty rows
records = []
for sub in data['submissions']:
    homie = sub['name']
    for song, artist, notes in sub['rows']:
        if any(x.strip() for x in [song, artist, notes]):
            records.append({
                'Song': song,
                'Artist': artist,
                'Notes': notes,
                'Homie': homie
            })

# Normalise to find duplicates
df = pd.DataFrame(records)
print(df)
df['Song'] = df['Song'].apply(clean_text)
df['Artist'] = df['Artist'].apply(clean_text)
df['Notes'] = df['Notes'].apply(clean_text)
df = df[df['Song'].str.strip() != '']

final = (
    df.sort_values(['Artist', 'Song', 'Homie'])
      .groupby(['Song', 'Artist'], as_index=False)
      .agg({
          'Song': 'first',
          'Artist': 'first',
          'Notes': 'first',
          'Homie': lambda x: ', '.join(sorted(set(x)))
      })
)


##### GET COVER ART FOR EACH SONG #####

# Search iTunes for cover art
def search_itunes(song, artist):
    query = f'{song} {artist}'
    url = 'https://itunes.apple.com/search'
    params = {
        'term': query,
        'media': 'music',
        'limit': 1
    }
    
    r = requests.get(url, params=params)
    data = r.json()

    results = data.get('results', [])
    if not results:
        return None
    
    artwork = results[0].get('artworkUrl100')
    if not artwork:
        return None
    
    return artwork.replace('100x100bb.jpg', '600x600bb.jpg')

# Add cleaned submission data and image url to cleaned song DB
session = SessionLocal()
session.query(CleanedSong).delete()

for _, row in final.iterrows():
    image_url = search_itunes(row['Song'], row['Artist'])
    cleaned = CleanedSong(
        song=row['Song'],
        artist=row['Artist'],
        notes=row['Notes'],
        image_url=image_url
    )
    session.add(cleaned)

session.commit()
session.close()