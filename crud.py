import sqlite3
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
