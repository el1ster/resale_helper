import sqlite3
import urllib.request
import os

# Update DB coefficients
db_path = 'resale_helper.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Increase multipliers slightly for better real-world matching
updates = [
    ("phys", "good", 0.90),
    ("phys", "fair", 0.75),
    ("phys", "poor", 0.55),
    ("brand", "apple", 1.25),
    ("brand", "premium", 1.10),
    ("brand", "mid", 0.95),
    ("brand", "budget", 0.80)
]

for factor, code, mult in updates:
    cursor.execute("UPDATE coefficients SET multiplier = ? WHERE factor_type = ? AND code = ?", (mult, factor, code))

conn.commit()
conn.close()
print("Database coefficients updated.")

# Download fonts
os.makedirs('assets', exist_ok=True)
fonts = {
    'Roboto-Regular.ttf': 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf',
    'Roboto-Bold.ttf': 'https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf'
}

for name, url in fonts.items():
    path = os.path.join('assets', name)
    if not os.path.exists(path):
        try:
            urllib.request.urlretrieve(url, path)
            print(f"Downloaded {name}")
        except Exception as e:
            print(f"Failed to download {name}: {e}")
    else:
        print(f"{name} already exists.")
