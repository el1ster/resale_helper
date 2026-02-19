import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.states import ValuationFSM
from bot import keyboards
import crud
from engine import ValuationEngine

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Вітаю у <b>EVS Bot</b> — Універсальній системі оцінки активів!

"
        "Я допоможу вам розрахувати справедливу ринкову вартість будь-якого товару (від смартфона до дивана).

"
        "Щоб розпочати нову оцінку, використовуйте команду /evaluate",
        parse_mode="HTML"
    )

@router.message(Command("evaluate"))
async def cmd_evaluate(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📦 <b>Крок 1/8: Виберіть категорію товару</b>
"
        "Що саме ми будемо оцінювати?",
        reply_markup=keyboards.get_categories_kb(),
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.choosing_category)

@router.callback_query(ValuationFSM.choosing_category, F.data.startswith("cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[1])
    category = crud.get_category_by_id(cat_id)
    
    if not category:
        await callback.answer("Категорію не знайдено!", show_alert=True)
        return

    # Зберігаємо вибрані дані у пам'ять FSM
    await state.update_data(
        category_id=cat_id,
        category_name=category["name_ua"],
        lifespan_months=category["lifespan_months"]
    )
    
    await callback.message.edit_text(
        f"✅ Обрано: <b>{category['name_ua']}</b>

"
        "💰 <b>Крок 2/8: Введіть початкову (базову) вартість</b>
"
        "Скільки такий або аналогічний товар зараз коштує НОВИМ у магазині?
"
        "<i>Напишіть просто число (наприклад, 15000)</i>",
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.entering_base_price)

@router.message(ValuationFSM.entering_base_price)
async def process_base_price(message: Message, state: FSMContext):
    # Очищуємо текст від можливих пробілів чи символів валют, намагаємось знайти число
    text = message.text.replace(" ", "").replace(",", ".")
    match = re.search(r"(\d+(\.\d+)?)", text)
    
    if not match:
        await message.answer("⚠️ Будь ласка, введіть коректне число (наприклад: 15000).")
        return
        
    base_price = float(match.group(1))
    
    if base_price <= 0:
        await message.answer("⚠️ Вартість повинна бути більшою за нуль.")
        return

    await state.update_data(base_price=base_price)
    
    await message.answer(
        f"✅ Базова ціна: <b>{base_price}</b>

"
        "⏳ <b>Крок 3/8: Скільки часу цьому товару?</b>
"
        "Оберіть з варіантів нижче, або натисніть 'Ввести вручну' для вводу свого значення.",
        reply_markup=keyboards.get_age_presets_kb(),
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.entering_age)

@router.callback_query(ValuationFSM.entering_age, F.data.startswith("age_"))
async def process_age_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "manual":
        await callback.message.edit_text(
            "✍️ Введіть вік товару текстом.
"
            "Наприклад: <i>15 міс</i>, <i>3 роки</i>, або просто число місяців.",
            parse_mode="HTML"
        )
        # Стейт не змінюємо, чекаємо текст у process_age_text
        return

    age_months = int(action)
    await _proceed_to_phys_state(callback.message, state, age_months)

@router.message(ValuationFSM.entering_age)
async def process_age_text(message: Message, state: FSMContext):
    text = message.text.lower()
    
    # Простий парсер: шукаємо числа і ключові слова "рік/рок/лет/year" або "міс/мес/month"
    match_num = re.search(r"(\d+(\.\d+)?)", text)
    if not match_num:
        await message.answer("⚠️ Не вдалося розпізнати число. Спробуйте ще раз, наприклад: <i>1.5 роки</i> або <i>18 міс</i>.", parse_mode="HTML")
        return
        
    num = float(match_num.group(1))
    
    is_years = bool(re.search(r"(рік|рок|лет|year|р)", text))
    is_months = bool(re.search(r"(міс|мес|month|м)", text))
    
    # Якщо розмірність не вказана (тільки число)
    if not is_years secured and not is_months:
        # Якщо число мале (напр < 15), за замовчуванням вважаємо це роками, якщо більше - місяцями
        if num <= 15:
            is_years = True
        else:
            is_months = True

    age_months = int(num * 12) if is_years else int(num)
    
    await _proceed_to_phys_state(message, state, age_months)

async def _proceed_to_phys_state(message: Message, state: FSMContext, age_months: int):
    await state.update_data(age_months=age_months)
    
    # Для редагування повідомлення (якщо прийшов колбек) або відправки нового (якщо текст)
    text = (
        f"✅ Вік: <b>{age_months} міс.</b>

"
        "🔎 <b>Крок 4/8: Фізичний стан</b>
"
        "Оцініть зовнішній вигляд товару (подряпини, вм'ятини, стан корпусу)."
    )
    
    try:
        await message.edit_text(text, reply_markup=keyboards.get_factor_kb("phys"), parse_mode="HTML")
    except:
        await message.answer(text, reply_markup=keyboards.get_factor_kb("phys"), parse_mode="HTML")
        
    await state.set_state(ValuationFSM.choosing_phys)

# --- Універсальний обробник для факторів ---
async def process_factor(callback: CallbackQuery, state: FSMContext, factor_type: str, next_state: State, next_step_num: int, next_step_name: str, next_factor: str):
    code = callback.data.split("_")[2]
    coeff = crud.get_coefficient_by_code(factor_type, code)
    
    if not coeff:
        await callback.answer("Помилка: Коефіцієнт не знайдено!", show_alert=True)
        return

    await state.update_data({
        f"{factor_type}_code": code,
        f"{factor_type}_multiplier": coeff["multiplier"],
        f"{factor_type}_name": coeff["name_ua"]
    })
    
    await callback.message.edit_text(
        f"✅ Обрано: <b>{coeff['name_ua']}</b>

"
        f"🔎 <b>Крок {next_step_num}/8: {next_step_name}</b>
",
        reply_markup=keyboards.get_factor_kb(next_factor) if next_factor else None,
        parse_mode="HTML"
    )
    await state.set_state(next_state)


@router.callback_query(ValuationFSM.choosing_phys, F.data.startswith("factor_phys_"))
async def process_phys(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "phys", ValuationFSM.choosing_tech, 5, "Технічний стан (справність)", "tech")

@router.callback_query(ValuationFSM.choosing_tech, F.data.startswith("factor_tech_"))
async def process_tech(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "tech", ValuationFSM.choosing_comp, 6, "Комплектація (коробка, аксесуари)", "comp")

@router.callback_query(ValuationFSM.choosing_comp, F.data.startswith("factor_comp_"))
async def process_comp(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "comp", ValuationFSM.choosing_warn, 7, "Гарантія", "warn")

@router.callback_query(ValuationFSM.choosing_warn, F.data.startswith("factor_warn_"))
async def process_warn(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "warn", ValuationFSM.choosing_brand, 8, "Ліквідність бренду", "brand")

@router.callback_query(ValuationFSM.choosing_brand, F.data.startswith("factor_brand_"))
async def process_brand(callback: CallbackQuery, state: FSMContext):
    # Останній крок - Терміновість не входить в 8 кроків товару, це налаштування продажу
    code = callback.data.split("_")[2]
    coeff = crud.get_coefficient_by_code("brand", code)
    await state.update_data(brand_code=code, brand_multiplier=coeff["multiplier"], brand_name=coeff["name_ua"])
    
    await callback.message.edit_text(
        f"✅ Обрано: <b>{coeff['name_ua']}</b>

"
        f"⏱ <b>Фінальний крок: Терміновість продажу</b>
"
        "Наскільки швидко ви хочете продати товар?",
        reply_markup=keyboards.get_factor_kb("urgent"),
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.choosing_urgent)

@router.callback_query(ValuationFSM.choosing_urgent, F.data.startswith("factor_urgent_"))
async def process_urgent_and_calculate(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_")[2]
    coeff = crud.get_coefficient_by_code("urgent", code)
    await state.update_data(urgent_code=code, urgent_multiplier=coeff["multiplier"], urgent_name=coeff["name_ua"])
    
    # Отримуємо всі дані
    data = await state.get_data()
    
    # Розрахунок
    try:
        final_price = ValuationEngine.calculate_price(
            base_price=data["base_price"],
            age_months=data["age_months"],
            lifespan_months=data["lifespan_months"],
            k_phys=data["phys_multiplier"],
            k_tech=data["tech_multiplier"],
            k_comp=data["comp_multiplier"],
            k_warn=data["warn_multiplier"],
            k_brand=data["brand_multiplier"],
            k_urgent=data["urgent_multiplier"],
            phys_code=data["phys_code"]
        )
        
        # Відправляємо результат
        await callback.message.edit_text(
            f"📊 <b>Звіт про оцінку</b>
"
            f"Категорія: {data['category_name']}
"
            f"Базова ціна: {data['base_price']}
"
            f"Вік: {data['age_months']} міс.
"
            f"Стан: {data['phys_name']} / {data['tech_name']}

"
            f"💵 <b>Справедлива ринкова ціна: {final_price:.2f}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Виникла помилка при розрахунку: {e}")
        
    await state.clear()
