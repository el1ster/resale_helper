from PIL import Image, ImageDraw, ImageFont
import io
import os

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
        font_title = ImageFont.truetype(font_path_bold, 46)
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
    draw.text((50, 50), "EVS Bot: Сертифікат Оцінки", fill=(255, 255, 255), font=font_title)
    draw.line((50, 110, 700, 110), fill=(100, 100, 100), width=2)

    # Базова інформація
    currency = snapshot.get('currency', 'UAH')
    base_price = snapshot.get('base_price', 0)
    
    y = 140
    # Обрізаємо задовгі назви категорій
    cat_name = snapshot.get('category_name', 'Невідомо')
    if len(cat_name) > 35:
        cat_name = cat_name[:32] + "..."
        
    draw.text((50, y), "Товар:", fill=(150, 150, 150), font=font_text)
    draw.text((250, y), f"{cat_name}", fill=(255, 255, 255), font=font_bold)
    
    y += 50
    draw.text((50, y), "Новий коштує:", fill=(150, 150, 150), font=font_text)
    draw.text((250, y), f"{base_price:,.2f} {currency}", fill=(255, 255, 255), font=font_bold)
    
    y += 50
    draw.text((50, y), "Вік:", fill=(150, 150, 150), font=font_text)
    draw.text((250, y), f"{snapshot.get('age_months', 0)} міс.", fill=(255, 255, 255), font=font_bold)

    draw.line((50, y+50, 700, y+50), fill=(100, 100, 100), width=1)
    
    # Фактори
    y += 80
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
            
            # Значення (обрізаємо до 20 символів щоб не налізало на множник)
            val_text = str(name)
            if len(val_text) > 23:
                val_text = val_text[:20] + "..."
            draw.text((270, y), val_text, fill=(255, 255, 255), font=font_text)
            
            # Множник вирівнюємо жорстко по правій стороні
            mult_str, color = format_multiplier(mult)
            draw.text((620, y), mult_str, fill=color, font=font_bold)
            y += line_height

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
