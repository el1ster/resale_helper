import sqlite3
import json
from typing import List, Dict, Any, Optional
from database import DB_PATH

def get_categories() -> List[Dict[str, Any]]:
    """Повертає всі категорії, відсортовані за sort_order."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name_ua, lifespan_months FROM categories ORDER BY sort_order")
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return categories

def get_category_by_id(cat_id: int) -> Optional[Dict[str, Any]]:
    """Повертає категорію за її ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name_ua, lifespan_months FROM categories WHERE id = ?", (cat_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_coefficients(factor_type: str) -> List[Dict[str, Any]]:
    """Повертає коефіцієнти певного типу (напр., 'phys', 'tech'), відсортовані за sort_order."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT code, name_ua, multiplier FROM coefficients WHERE factor_type = ? ORDER BY sort_order", (factor_type,))
    coeffs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return coeffs

def get_coefficient_by_code(factor_type: str, code: str) -> Optional[Dict[str, Any]]:
    """Повертає конкретний коефіцієнт за його типом та кодом."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT code, name_ua, multiplier FROM coefficients WHERE factor_type = ? AND code = ?", (factor_type, code))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_or_create_user(telegram_id: int, username: str) -> int:
    """Знаходить користувача за telegram_id або створює нового. Повертає внутрішній id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    if row:
        user_id = row[0]
    else:
        cursor.execute("INSERT INTO users (telegram_id, username) VALUES (?, ?)", (telegram_id, username))
        user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def save_valuation(user_id: int, category_id: int, base_price: float, currency_code: str, final_price: float, snapshot: dict) -> tuple[int, int]:
    """Зберігає розрахунок у базу даних та повертає id запису та порядковий номер звіту для цього користувача."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Визначаємо порядковий номер звіту для користувача
    cursor.execute("SELECT COUNT(*) FROM valuations WHERE user_id = ?", (user_id,))
    user_report_num = cursor.fetchone()[0] + 1
    
    # Зберігаємо номер у snapshot для генерації квитанцій
    snapshot['user_report_num'] = user_report_num
    snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    
    cursor.execute("""
        INSERT INTO valuations (user_id, category_id, base_price, currency_code, final_price, snapshot_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, category_id, base_price, currency_code, final_price, snapshot_json))
    val_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return val_id, user_report_num

def get_valuation(val_id: int) -> Optional[Dict[str, Any]]:
    """Повертає запис про оцінку за ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM valuations WHERE id = ?", (val_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
