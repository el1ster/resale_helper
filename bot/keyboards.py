from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import crud

def get_categories_kb() -> InlineKeyboardMarkup:
    """Генерує інлайн-клавіатуру з усіма доступними категоріями."""
    builder = InlineKeyboardBuilder()
    categories = crud.get_categories()
    
    for cat in categories:
        builder.button(text=cat['name_ua'], callback_data=f"cat_{cat['id']}")
        
    builder.adjust(1) # По одній кнопці в ряд
    return builder.as_markup()

def get_age_presets_kb() -> InlineKeyboardMarkup:
    """Генерує клавіатуру з пресетами для віку."""
    builder = InlineKeyboardBuilder()
    
    # Значення callback_data - це кількість місяців
    presets = [
        ("Менше місяця", "age_0"),
        ("Півроку", "age_6"),
        ("1 рік", "age_12"),
        ("2 роки", "age_24"),
        ("3 роки", "age_36"),
        ("5 років", "age_60"),
        ("Ввести вручну ✍️", "age_manual")
    ]
    
    for text, cb_data in presets:
        builder.button(text=text, callback_data=cb_data)
        
    builder.adjust(2) # По дві кнопки в ряд
    return builder.as_markup()

def get_factor_kb(factor_type: str) -> InlineKeyboardMarkup:
    """Генерує клавіатуру для вибору коефіцієнтів (фізичний стан, комплектація тощо)."""
    builder = InlineKeyboardBuilder()
    coeffs = crud.get_coefficients(factor_type)
    
    for coeff in coeffs:
        builder.button(text=coeff['name_ua'], callback_data=f"factor_{factor_type}_{coeff['code']}")
        
    builder.adjust(1)
    return builder.as_markup()
