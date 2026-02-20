from PIL import Image, ImageDraw, ImageFont
import io
import os
import re
import textwrap

def clean_factor_name(name: str) -> str:
    """Видаляє текст у дужках (включаючи самі дужки) для чистого відображення у чеку."""
    return re.sub(r'\s*\(.*?\)', '', str(name)).strip()

def generate_receipt_image(snapshot: dict, final_price: float) -> io.BytesIO:
    """Генерує PNG-зображення з красивим чеком/сертифікатом оцінки."""
    width, height = 750, 950
    # Темний преміальний фон
    img = Image.new('RGB', (width, height), color=(24, 24, 27))
    draw = ImageDraw.Draw(img)
    
    try:
        font_path_reg = os.path.join("assets", "Roboto-Regular.ttf")
        font_path_bold = os.path.join("assets", "Roboto-Bold.ttf")
        
        # Намагаємось використати завантажені шрифти Roboto
        font_title = ImageFont.truetype(font_path_bold, 42)
        font_subtitle = ImageFont.truetype(font_path_reg, 32)
        font_text = ImageFont.truetype(font_path_reg, 26)
        font_bold = ImageFont.truetype(font_path_bold, 28)
        font_price = ImageFont.truetype(font_path_bold, 52)
    except IOError:
        # Fallback якщо шрифти не знайдено
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_price = ImageFont.load_default()

    # Заголовок
    report_num = snapshot.get('user_report_num', '')
    title_text = f"EVS Bot: Сертифікат Оцінки #{report_num}" if report_num else "EVS Bot: Сертифікат Оцінки"
    draw.text((50, 50), title_text, fill=(255, 255, 255), font=font_title)
    draw.line((50, 110, 700, 110), fill=(100, 100, 100), width=2)

    # Базова інформація
    currency = snapshot.get('currency', 'UAH')
    base_price = snapshot.get('base_price', 0)
    
    y = 140
    # Отримуємо назву товару і робимо перенесення рядків (wrap)
    item_name = snapshot.get('item_name', snapshot.get('category_name', 'Невідомо'))
    wrapped_name = textwrap.wrap(item_name, width=32)
    
    draw.text((50, y), "Товар:", fill=(150, 150, 150), font=font_text)
    for line in wrapped_name:
        draw.text((250, y), line, fill=(255, 255, 255), font=font_bold)
        y += 40
        
    y += 10
    draw.text((50, y), "Новий коштує:", fill=(150, 150, 150), font=font_text)
    draw.text((250, y), f"{base_price:,.2f} {currency}", fill=(255, 255, 255), font=font_bold)
    
    y += 50
    draw.text((50, y), "Вік:", fill=(150, 150, 150), font=font_text)
    k_age = snapshot.get('age_multiplier', 1.0)
    draw.text((250, y), f"{snapshot.get('age_months', 0)} міс.", fill=(255, 255, 255), font=font_bold)
    draw.text((620, y), f"x{k_age:.2f}", fill=(200, 200, 200), font=font_bold) # Множник віку

    y += 50
    draw.line((50, y, 700, y), fill=(100, 100, 100), width=1)
    
    # Фактори
    y += 30
    draw.text((50, y), "Деталі оцінки (фактори зносу):", fill=(200, 200, 200), font=font_subtitle)
    
    y += 60
    line_height = 45
    
    def format_multiplier(m: float) -> str:
        color = (255, 80, 80) if m < 1.0 else (80, 255, 80) if m > 1.0 else (200, 200, 200)
        return f"x{m:.2f}", color

    factors = [
        ("Фізичний стан", snapshot.get('phys_name'), snapshot.get('phys_multiplier')),
        ("Технічний стан", snapshot.get('tech_name'), snapshot.get('tech_multiplier')),
        ("Комплектація", snapshot.get('comp_name'), snapshot.get('comp_multiplier')),
        ("Гарантія", snapshot.get('warn_name'), snapshot.get('warn_multiplier')),
        ("Бренд", snapshot.get('brand_name'), snapshot.get('brand_multiplier')),
        ("Терміновість", snapshot.get('urgent_name'), snapshot.get('urgent_multiplier')),
    ]
    
    for label, name, mult in factors:
        if name and mult is not None:
            # Назва фактору
            draw.text((50, y), f"{label}:", fill=(150, 150, 150), font=font_text)
            
            # Чиста назва без дужок
            clean_name = clean_factor_name(name)
            if len(clean_name) > 23:
                clean_name = clean_name[:20] + "..."
            draw.text((270, y), clean_name, fill=(255, 255, 255), font=font_text)
            
            # Множник вирівнюємо жорстко по правій стороні
            mult_str, color = format_multiplier(mult)
            draw.text((620, y), mult_str, fill=color, font=font_bold)
            y += line_height

    y -= 15
    draw.line((50, y+30, 700, y+30), fill=(100, 100, 100), width=2)
    
    # Фінальна ціна
    y += 60
    draw.text((50, y), "СПРАВЕДЛИВА РИНКОВА ВАРТІСТЬ", fill=(200, 200, 200), font=font_subtitle)
    
    y += 60
    draw.text((50, y), f"{final_price:,.2f} {currency}", fill=(16, 185, 129), font=font_price) # Смарагдовий зелений

    # Зберігаємо в BytesIO
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio
