import sqlite3
import os

DB_PATH = 'resale_helper.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Повернення загублених кодів у базу
updates = [
    # Технічний стан
    ("UPDATE coefficients SET code = 'minor_issues' WHERE factor_type = 'tech' AND code = 'minor'",),
    ("UPDATE coefficients SET code = 'partial_defect' WHERE factor_type = 'tech' AND code = 'partial'",),
    
    # Комплектація
    ("UPDATE coefficients SET code = 'device_only' WHERE factor_type = 'comp' AND code = 'device'",)
]

for q in updates:
    try:
        cursor.execute(q[0])
    except sqlite3.Error as e:
        print(f"Error: {e}")

# 2. М'яка лінійна амортизація для меблів
# Меблі втрачають ціну значно повільніше, і їх Floor має бути вищим
# Це буде враховано в engine.py

conn.commit()
conn.close()

print("Базу даних виправлено.")
