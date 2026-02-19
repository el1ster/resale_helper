import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_PATH = "resale_helper.db"

def init_db(db_path: str = DB_PATH) -> None:
    """Ініціалізація бази даних та створення таблиць, якщо вони не існують."""
    conn = sqlite3.connect(db_path)
    
    # Увімкнення підтримки зовнішніх ключів у SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        # 1. Таблиця користувачів
        # Зберігає налаштування користувача (наприклад, обрану валюту)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                currency_code TEXT DEFAULT 'UAH',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Таблиця категорій (вони ж групи амортизації)
        # Оскільки ми оперуємо глобальними категоріями, об'єднуємо UI-назву та термін служби
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ua TEXT NOT NULL UNIQUE,
                lifespan_months INTEGER NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)

        # 3. Таблиця коефіцієнтів
        # EAV-подібна структура для UI-кнопок та математики
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coefficients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_type TEXT NOT NULL,
                code TEXT NOT NULL,
                name_ua TEXT NOT NULL,
                multiplier REAL NOT NULL,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(factor_type, code)
            )
        """)

        # 4. Таблиця історій оцінок (Лог)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS valuations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                base_price REAL NOT NULL,
                currency_code TEXT NOT NULL,
                final_price REAL NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE RESTRICT
            )
        """)

        conn.commit()
        logger.info("Базу даних успішно ініціалізовано.")
    except sqlite3.Error as e:
        logger.error(f"Помилка при ініціалізації бази даних: {e}")
        conn.rollback()
    finally:
        conn.close()

def seed_db(db_path: str = DB_PATH) -> None:
    """Наповнення бази даних початковими (seed) даними: категоріями та коефіцієнтами."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Базові категорії (Групи амортизації)
    categories = [
        # name_ua, lifespan_months, sort_order
        ("📱 Гаджети (смартфони, планшети, розумні годинники)", 60, 1), # 5 років
        ("💻 Комп'ютерна техніка (ПК, ноутбуки, комплектуючі)", 84, 2), # 7 років
        ("📺 Побутова техніка (ТВ, аудіо, кухонна техніка)", 120, 3), # 10 років
        ("🛋 Меблі та інтер'єр", 360, 4), # 30 років
        ("📷 Фото та відео техніка", 120, 5), # 10 років
        ("🎸 Музичні інструменти", 240, 6), # 20 років
        ("🚴 Спортивний інвентар (велосипеди, тренажери)", 120, 7), # 10 років
        ("🚗 Авто/Мото аксесуари", 84, 8), # 7 років
        ("🛠 Промислове обладнання та інструменти", 180, 9) # 15 років
    ]

    # 2. Базові коефіцієнти
    # factor_type: phys (фізичний стан), tech (технічний стан), comp (комплектація), 
    # warn (гарантія), brand (ліквідність бренду), urgent (терміновість продажу)
    coefficients = [
        # factor_type, code, name_ua, multiplier, sort_order
        
        # Фізичний стан (K_phys)
        ("phys", "perfect", "Ідеальний (як новий, без слідів)", 1.0, 1),
        ("phys", "good", "Хороший (дрібні подряпини/потертості)", 0.85, 2),
        ("phys", "fair", "Задовільний (помітні сліди використання)", 0.70, 3),
        ("phys", "poor", "Поганий (сильні пошкодження корпусу)", 0.50, 4),

        # Технічний стан (K_tech)
        ("tech", "perfect", "Повністю справний", 1.0, 1),
        ("tech", "minor_issues", "Дрібні недоліки (напр., слабка АКБ)", 0.85, 2),
        ("tech", "partial_defect", "Частково несправний (не працює одна функція)", 0.60, 3),
        ("tech", "broken", "Несправний (під ремонт або на запчастини)", 0.30, 4),

        # Комплектація (K_comp)
        ("comp", "full", "Повний оригінальний комплект", 1.0, 1),
        ("comp", "partial", "Частковий (немає коробки або кабелю)", 0.90, 2),
        ("comp", "device_only", "Лише сам пристрій", 0.80, 3),

        # Наявність гарантії (K_warn)
        ("warn", "valid", "Дійсна офіційна гарантія", 1.10, 1), # Збільшує вартість!
        ("warn", "expired", "Гарантія закінчилась", 1.0, 2),
        ("warn", "none", "Без гарантії / Невідомо", 0.95, 3),

        # Ліквідність бренду (K_brand)
        ("brand", "apple", "Apple", 1.15, 1), # Висока ліквідність
        ("brand", "premium", "Преміум (Samsung, Sony, Dyson і т.д.)", 1.0, 2),
        ("brand", "mid", "Середній сегмент (Xiaomi, LG, Asus і т.д.)", 0.90, 3),
        ("brand", "budget", "Бюджетний (ноунейм, Китай)", 0.75, 4),
        ("brand", "not_applicable", "Не має значення (напр. шафа)", 1.0, 5), # Для меблів

        # Терміновість продажу (K_urgent)
        ("urgent", "normal", "Не поспішаю (продаж 1-2 місяці)", 1.0, 1),
        ("urgent", "fast", "Швидкий продаж (1-2 тижні)", 0.85, 2),
        ("urgent", "now", "Терміновий викуп (1-2 дні)", 0.70, 3)
    ]

    try:
        cursor.executemany("""
            INSERT OR IGNORE INTO categories (name_ua, lifespan_months, sort_order)
            VALUES (?, ?, ?)
        """, categories)

        cursor.executemany("""
            INSERT OR IGNORE INTO coefficients (factor_type, code, name_ua, multiplier, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, coefficients)

        conn.commit()
        logger.info("Базу даних успішно наповнено базовими даними.")
    except sqlite3.Error as e:
        logger.error(f"Помилка при наповненні бази даних: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Налаштування логування для автономного запуску
    logging.basicConfig(level=logging.INFO)
    init_db()
    seed_db()
