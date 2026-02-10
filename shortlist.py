import requests
import re
import pandas as pd
import os
import requests


##### CLEAN SONGS FROM SUBMISSIONS #####

url = 'https://homies-hottest-100.onrender.com/submissions'
data = requests.get(url).json()

# Clean free text values
def clean_text(s):
    if not isinstance(s, str):
        return ''
    
    s = s.upper()
    s = s.replace('-', ' ')
    s = re.sub(r'[^\w\s]', '', s)
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
df['Song'] = df['Song'].apply(clean_text)
df['Artist'] = df['Artist'].apply(clean_text)
df['Notes'] = df['Notes'].apply(clean_text)
df = df[df['Song'].str.strip() != '']

final = (
    df.sort_values(['Artist', 'Song', 'Homie'])
      .groupby(['Song', 'Artist'], as_index=False)
      .agg({
          'Song': 'first',          # original text
          'Artist': 'first',
          'Notes': 'first',
          'Homie': lambda x: ', '.join(sorted(set(x)))
      })
)

print(final)


##### GET COVER ART FOR EACH SONG #####

covers_dir = 'covers'
os.makedirs(covers_dir, exist_ok=True)

# Download image from url to path
def download_image(url, path):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)

# Return safe file path name
def safe_filename(s):
    return "".join(c for c in s if c.isalnum() or c in (" ", "-", "_")).rstrip()

# Search iTunes for cover art
def search_itunes(song, artist, notes):
    query = f'{song} {artist} {notes}'
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

# Return file path for cover art image
def get_cover_for_row(row):
    image_url = search_itunes(song, artist, notes)

    if not image_url:
        return None
    
    filename = safe_filename(f'{row['Artist']} - {row['Song']}.jpg')
    path = os.path.join(covers_dir, filename)
    download_image(image_url, path)

    return path

# Add cover art path for each song
final['ImagePath'] = final.apply(get_cover_for_row, axis=1)
print(final)