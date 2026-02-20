import sqlite3
import os

DB_PATH = 'resale_helper.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Балансування коефіцієнтів
# 1. Фізичний стан
cursor.execute("UPDATE coefficients SET multiplier = 1.15 WHERE factor_type = 'phys' AND code = 'sealed'")
cursor.execute("UPDATE coefficients SET multiplier = 1.00 WHERE factor_type = 'phys' AND code = 'perfect'")
cursor.execute("UPDATE coefficients SET multiplier = 0.85 WHERE factor_type = 'phys' AND code = 'good'")
cursor.execute("UPDATE coefficients SET multiplier = 0.70 WHERE factor_type = 'phys' AND code = 'fair'")
cursor.execute("UPDATE coefficients SET multiplier = 0.40 WHERE factor_type = 'phys' AND code = 'poor'")

# 2. Бренд (оновлюємо та переназиваємо для кращої преміальності)
cursor.execute("UPDATE coefficients SET name_ua = 'Ексклюзив / Apple', multiplier = 1.20 WHERE factor_type = 'brand' AND code = 'apple'")
cursor.execute("UPDATE coefficients SET name_ua = 'Преміум (Samsung, Sony, Dyson)', multiplier = 1.05 WHERE factor_type = 'brand' AND code = 'premium'")
cursor.execute("UPDATE coefficients SET name_ua = 'Середній сегмент (Xiaomi, Asus, LG)', multiplier = 0.90 WHERE factor_type = 'brand' AND code = 'mid'")
cursor.execute("UPDATE coefficients SET name_ua = 'Бюджетний (Ноунейм, дешевий Китай)', multiplier = 0.75 WHERE factor_type = 'brand' AND code = 'budget'")

# 3. Технічний стан (робимо брухт ще дешевшим)
cursor.execute("UPDATE coefficients SET multiplier = 0.15 WHERE factor_type = 'tech' AND code = 'broken'")
cursor.execute("UPDATE coefficients SET multiplier = 0.50 WHERE factor_type = 'tech' AND code = 'partial_defect'")
cursor.execute("UPDATE coefficients SET multiplier = 0.80 WHERE factor_type = 'tech' AND code = 'minor_issues'")

conn.commit()
conn.close()

print("Базу даних успішно збалансовано (версія 3).")
