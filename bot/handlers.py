import re
import json
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.states import ValuationFSM
from bot import keyboards
from bot import currency
from bot import receipt
import crud
from engine import ValuationEngine

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} ({message.from_user.username}) started the bot.")
    await message.answer(
        "👋 Вітаю у <b>EVS Bot</b> — Універсальній системі оцінки активів!\n\n"
        "Я допоможу вам розрахувати справедливу ринкову вартість будь-якого товару (від смартфона до дивана).\n\n"
        "Щоб розпочати нову оцінку, використовуйте команду /evaluate",
        parse_mode="HTML"
    )

@router.message(Command("evaluate"))
async def cmd_evaluate(message: Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} started a new evaluation.")
    await message.answer(
        "📦 <b>Крок 1/9: Виберіть категорію товару</b>\n"
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
        logger.warning(f"User {callback.from_user.id} clicked invalid category: {cat_id}")
        await callback.answer("Категорію не знайдено! Спробуйте ще раз.", show_alert=True)
        return

    logger.info(f"User {callback.from_user.id} chose category: {category['name_ua']} (id: {cat_id})")

    await state.update_data(
        category_id=cat_id,
        category_name=category["name_ua"],
        lifespan_months=category["lifespan_months"]
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Пропустити", callback_data="skip_name")
    
    await callback.message.edit_text(
        f"✅ Обрано: <b>{category['name_ua']}</b>\n\n"
        "📝 <b>Крок 1.5/9: Введіть назву товару (Опціонально)</b>\n"
        "Введіть точну назву (наприклад, <i>iPhone 13 Pro</i> або <i>Диван IKEA</i>), щоб вона відображалась у звіті.\n"
        "Або натисніть «Пропустити».",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.entering_item_name)

@router.message(ValuationFSM.entering_item_name)
async def process_item_name_text(message: Message, state: FSMContext):
    item_name = message.text.strip()
    await state.update_data(item_name=item_name)
    logger.info(f"User {message.from_user.id} entered custom item name: {item_name}")
    await proceed_to_currency(message, state, is_callback=False)

@router.callback_query(ValuationFSM.entering_item_name, F.data == "skip_name")
async def process_item_name_skip(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(item_name=data['category_name'])
    logger.info(f"User {callback.from_user.id} skipped custom item name.")
    await proceed_to_currency(callback.message, state, is_callback=True)

async def proceed_to_currency(message: Message, state: FSMContext, is_callback=False):
    data = await state.get_data()
    text = (
        f"✅ Товар: <b>{data['item_name']}</b>\n\n"
        "💱 <b>Крок 2/9: Оберіть валюту</b>\n"
        "В якій валюті ви будете вказувати початкову вартість?"
    )
    if is_callback:
        await message.edit_text(text, reply_markup=keyboards.get_currency_kb(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=keyboards.get_currency_kb(), parse_mode="HTML")
    await state.set_state(ValuationFSM.choosing_currency)

@router.callback_query(ValuationFSM.choosing_currency, F.data.startswith("curr_"))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    curr_code = callback.data.split("_")[1]
    logger.info(f"User {callback.from_user.id} chose currency: {curr_code}")
    await state.update_data(currency=curr_code)
    
    await callback.message.edit_text(
        f"✅ Валюта: <b>{curr_code}</b>\n\n"
        "💰 <b>Крок 3/9: Введіть початкову (базову) вартість</b>\n"
        f"Скільки такий або аналогічний товар зараз коштує НОВИМ у магазині ({curr_code})?\n"
        "<i>Напишіть просто число (наприклад, 15000)</i>",
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.entering_base_price)

@router.message(ValuationFSM.entering_base_price)
async def process_base_price(message: Message, state: FSMContext):
    text = message.text.replace(" ", "").replace(",", ".")
    match = re.search(r"(\d+(\.\d+)?)", text)
    
    if not match:
        logger.warning(f"User {message.from_user.id} entered invalid price: {message.text}")
        await message.answer("⚠️ Будь ласка, введіть коректне число (наприклад: 15000).")
        return
        
    base_price = float(match.group(1))
    
    if base_price <= 0:
        logger.warning(f"User {message.from_user.id} entered zero/negative price: {base_price}")
        await message.answer("⚠️ Вартість повинна бути більшою за нуль.")
        return

    logger.info(f"User {message.from_user.id} entered base price: {base_price}")
    await state.update_data(base_price=base_price)
    data = await state.get_data()
    
    await message.answer(
        f"✅ Базова ціна: <b>{base_price} {data['currency']}</b>\n\n"
        "⏳ <b>Крок 4/9: Скільки часу цьому товару?</b>\n"
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
            "✍️ Введіть вік товару текстом.\n"
            "Наприклад: <i>15 міс</i>, <i>3 роки</i>, або просто число місяців.",
            parse_mode="HTML"
        )
        return

    age_months = int(action)
    await _proceed_to_phys_state(callback.message, state, age_months, callback.from_user.id)

@router.message(ValuationFSM.entering_age)
async def process_age_text(message: Message, state: FSMContext):
    text = message.text.lower()
    
    match_num = re.search(r"(\d+(\.\d+)?)", text)
    if not match_num:
        logger.warning(f"User {message.from_user.id} entered invalid age text: {message.text}")
        await message.answer("⚠️ Не вдалося розпізнати число. Спробуйте ще раз, наприклад: <i>1.5 роки</i> або <i>18 міс</i>.", parse_mode="HTML")
        return
        
    num = float(match_num.group(1))
    
    is_years = bool(re.search(r"(рік|рок|лет|year|р)", text))
    is_months = bool(re.search(r"(міс|мес|month|м)", text))
    
    # Якщо одиниці виміру не вказані, запитуємо користувача
    if not is_years and not is_months:
        await state.update_data(pending_age_num=num)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="Років", callback_data="age_unit_years")
        builder.button(text="Місяців", callback_data="age_unit_months")
        builder.adjust(2)
        
        await message.answer(
            f"Ви ввели число <b>{num}</b>. Це роки чи місяці?", 
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return

    age_months = int(num * 12) if is_years else int(num)
    await _proceed_to_phys_state(message, state, age_months, message.from_user.id)

@router.callback_query(ValuationFSM.entering_age, F.data.startswith("age_unit_"))
async def process_age_unit_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    num = data.get("pending_age_num")
    
    if not num:
        await callback.answer("Помилка, введіть вік ще раз.", show_alert=True)
        return
        
    if "years" in callback.data:
        age_months = int(num * 12)
    else:
        age_months = int(num)
        
    await callback.message.delete()
    await _proceed_to_phys_state(callback.message, state, age_months, callback.from_user.id)


async def _proceed_to_phys_state(message: Message, state: FSMContext, age_months: int, user_id: int):
    logger.info(f"User {user_id} entered age: {age_months} months")
    await state.update_data(age_months=age_months)
    
    text = (
        f"✅ Вік: <b>{age_months} міс.</b>\n\n"
        "🔎 <b>Крок 5/9: Фізичний стан</b>\n"
        "Оцініть зовнішній вигляд товару (подряпини, вм'ятини, стан корпусу)."
    )
    
    try:
        await message.edit_text(text, reply_markup=keyboards.get_factor_kb("phys"), parse_mode="HTML")
    except:
        await message.answer(text, reply_markup=keyboards.get_factor_kb("phys"), parse_mode="HTML")
        
    await state.set_state(ValuationFSM.choosing_phys)

# --- Універсальний обробник для факторів ---
async def process_factor(callback: CallbackQuery, state: FSMContext, factor_type: str, next_state: State, next_step_num: int, next_step_name: str, next_factor: str):
    # Код може містити підкреслення (напр. 'minor_issues'). 
    # Тому беремо все після префіксу "factor_{factor_type}_"
    prefix = f"factor_{factor_type}_"
    code = callback.data[len(prefix):]
    
    coeff = crud.get_coefficient_by_code(factor_type, code)
    
    if not coeff:
        logger.error(f"User {callback.from_user.id} clicked missing coefficient: {factor_type}_{code}")
        await callback.answer(f"Помилка: Критерій '{code}' не знайдено! Зверніться до підтримки.", show_alert=True)
        return

    logger.info(f"User {callback.from_user.id} chose {factor_type}: {coeff['name_ua']} (x{coeff['multiplier']})")

    await state.update_data({
        f"{factor_type}_code": code,
        f"{factor_type}_multiplier": coeff["multiplier"],
        f"{factor_type}_name": coeff["name_ua"]
    })
    
    # Додаємо кнопку "⬅️ Назад" до клавіатури наступного кроку
    builder = InlineKeyboardBuilder()
    if next_factor:
        coeffs = crud.get_coefficients(next_factor)
        for c in coeffs:
            builder.button(text=c['name_ua'], callback_data=f"factor_{next_factor}_{c['code']}")
    builder.button(text="⬅️ Назад", callback_data=f"back_to_{factor_type}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"✅ Обрано: <b>{coeff['name_ua']}</b>\n\n"
        f"🔎 <b>Крок {next_step_num}/9: {next_step_name}</b>\n",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(next_state)


@router.callback_query(F.data.startswith("back_to_"))
async def process_back_button(callback: CallbackQuery, state: FSMContext):
    target = callback.data.split("_")[2]
    
    # Визначаємо, куди повертатися, та який текст/клавіатуру показати
    if target == "phys":
        await state.set_state(ValuationFSM.choosing_phys)
        data = await state.get_data()
        await callback.message.edit_text(
            f"✅ Вік: <b>{data.get('age_months', 0)} міс.</b>\n\n"
            "🔎 <b>Крок 5/9: Фізичний стан</b>\n"
            "Оцініть зовнішній вигляд товару (подряпини, вм'ятини, стан корпусу).",
            reply_markup=keyboards.get_factor_kb("phys"),
            parse_mode="HTML"
        )
    elif target == "tech":
        await state.set_state(ValuationFSM.choosing_tech)
        data = await state.get_data()
        builder = InlineKeyboardBuilder()
        coeffs = crud.get_coefficients("tech")
        for c in coeffs:
            builder.button(text=c['name_ua'], callback_data=f"factor_tech_{c['code']}")
        builder.button(text="⬅️ Назад", callback_data="back_to_phys")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"✅ Обрано: <b>{data.get('phys_name', '')}</b>\n\n"
            f"🔎 <b>Крок 6/9: Технічний стан (справність)</b>\n",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif target == "comp":
        await state.set_state(ValuationFSM.choosing_comp)
        data = await state.get_data()
        builder = InlineKeyboardBuilder()
        coeffs = crud.get_coefficients("comp")
        for c in coeffs:
            builder.button(text=c['name_ua'], callback_data=f"factor_comp_{c['code']}")
        builder.button(text="⬅️ Назад", callback_data="back_to_tech")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"✅ Обрано: <b>{data.get('tech_name', '')}</b>\n\n"
            f"🔎 <b>Крок 7/9: Комплектація (коробка, аксесуари)</b>\n",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif target == "warn":
        await state.set_state(ValuationFSM.choosing_warn)
        data = await state.get_data()
        builder = InlineKeyboardBuilder()
        coeffs = crud.get_coefficients("warn")
        for c in coeffs:
            builder.button(text=c['name_ua'], callback_data=f"factor_warn_{c['code']}")
        builder.button(text="⬅️ Назад", callback_data="back_to_comp")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"✅ Обрано: <b>{data.get('comp_name', '')}</b>\n\n"
            f"🔎 <b>Крок 8/9: Гарантія</b>\n",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif target == "brand":
        await state.set_state(ValuationFSM.choosing_brand)
        data = await state.get_data()
        builder = InlineKeyboardBuilder()
        coeffs = crud.get_coefficients("brand")
        for c in coeffs:
            builder.button(text=c['name_ua'], callback_data=f"factor_brand_{c['code']}")
        builder.button(text="⬅️ Назад", callback_data="back_to_warn")
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"✅ Обрано: <b>{data.get('warn_name', '')}</b>\n\n"
            f"🔎 <b>Крок 9/9: Ліквідність бренду</b>\n",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

@router.callback_query(ValuationFSM.choosing_phys, F.data.startswith("factor_phys_"))
async def process_phys(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "phys", ValuationFSM.choosing_tech, 6, "Технічний стан (справність)", "tech")

@router.callback_query(ValuationFSM.choosing_tech, F.data.startswith("factor_tech_"))
async def process_tech(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "tech", ValuationFSM.choosing_comp, 7, "Комплектація (коробка, аксесуари)", "comp")

@router.callback_query(ValuationFSM.choosing_comp, F.data.startswith("factor_comp_"))
async def process_comp(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "comp", ValuationFSM.choosing_warn, 8, "Гарантія", "warn")

@router.callback_query(ValuationFSM.choosing_warn, F.data.startswith("factor_warn_"))
async def process_warn(callback: CallbackQuery, state: FSMContext):
    await process_factor(callback, state, "warn", ValuationFSM.choosing_brand, 9, "Ліквідність бренду", "brand")

@router.callback_query(ValuationFSM.choosing_brand, F.data.startswith("factor_brand_"))
async def process_brand(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_")[2]
    coeff = crud.get_coefficient_by_code("brand", code)
    
    if not coeff:
        logger.error(f"User {callback.from_user.id} clicked missing brand: {code}")
        await callback.answer(f"Помилка: Бренд '{code}' не знайдено!", show_alert=True)
        return
        
    logger.info(f"User {callback.from_user.id} chose brand: {coeff['name_ua']} (x{coeff['multiplier']})")
    
    await state.update_data(brand_code=code, brand_multiplier=coeff["multiplier"], brand_name=coeff["name_ua"])
    
    await callback.message.edit_text(
        f"✅ Обрано: <b>{coeff['name_ua']}</b>\n\n"
        f"⏱ <b>Фінальний крок: Терміновість продажу</b>\n"
        "Наскільки швидко ви хочете продати товар?",
        reply_markup=keyboards.get_factor_kb("urgent"),
        parse_mode="HTML"
    )
    await state.set_state(ValuationFSM.choosing_urgent)

@router.callback_query(ValuationFSM.choosing_urgent, F.data.startswith("factor_urgent_"))
async def process_urgent_and_calculate(callback: CallbackQuery, state: FSMContext):
    # Код може містити підкреслення
    prefix = "factor_urgent_"
    code = callback.data[len(prefix):]
    
    coeff = crud.get_coefficient_by_code("urgent", code)
    
    if not coeff:
        logger.error(f"User {callback.from_user.id} clicked missing urgent code: {code}")
        await callback.answer(f"Помилка: Критерій '{code}' не знайдено!", show_alert=True)
        return
        
    logger.info(f"User {callback.from_user.id} chose urgent: {coeff['name_ua']} (x{coeff['multiplier']})")
    await state.update_data(urgent_code=code, urgent_multiplier=coeff["multiplier"], urgent_name=coeff["name_ua"])
    
    snapshot = await state.get_data()
    
    try:
        # Розраховуємо K_age окремо для відображення, враховуючи бренд
        k_age = ValuationEngine.calculate_k_age(
            age_months=snapshot["age_months"], 
            lifespan_months=snapshot["lifespan_months"], 
            is_sealed=(snapshot.get("phys_code") == "sealed"),
            brand_multiplier=snapshot.get("brand_multiplier", 1.0)
        )
        snapshot["age_multiplier"] = k_age
        
        # 1. Фінальний розрахунок
        final_price = ValuationEngine.calculate_price(
            base_price=snapshot["base_price"],
            age_months=snapshot["age_months"],
            lifespan_months=snapshot["lifespan_months"],
            k_phys=snapshot["phys_multiplier"],
            k_tech=snapshot["tech_multiplier"],
            k_comp=snapshot["comp_multiplier"],
            k_warn=snapshot["warn_multiplier"],
            k_brand=snapshot["brand_multiplier"],
            k_urgent=snapshot["urgent_multiplier"],
            phys_code=snapshot["phys_code"]
        )
        
        logger.info(f"User {callback.from_user.id} valuation calculated: {final_price:.2f} {snapshot['currency']} (k_age={k_age:.2f})")

        nbu_info = ""
        if snapshot["currency"] != "UAH":
            rate = await currency.get_nbu_rate(snapshot["currency"])
            final_price_uah = final_price * rate
            nbu_info = f"\n🔄 <i>(~ {final_price_uah:,.2f} UAH за курсом НБУ)</i>"

        # 2. Збереження
        user_id = crud.get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username or "unknown"
        )
        
        val_id, user_report_num = crud.save_valuation(
            user_id=user_id,
            category_id=snapshot["category_id"],
            base_price=snapshot["base_price"],
            currency_code=snapshot["currency"],
            final_price=final_price,
            snapshot=snapshot
        )

        # 3. Маркдаун чек
        report = (
            f"📊 <b>Звіт про оцінку #{user_report_num}</b> <i>(Системний ID: {val_id})</i>\n\n"
            f"📦 <b>Товар:</b> {snapshot.get('item_name', snapshot['category_name'])}\n"
            f"💵 <b>Новий коштує:</b> {snapshot['base_price']:,.2f} {snapshot['currency']}\n"
            f"⏳ <b>Вік:</b> {snapshot['age_months']} міс. (x{k_age:.2f})\n\n"
            f"<b>Критерії зносу:</b>\n"
            f"• Стан: {snapshot['phys_name']} (x{snapshot['phys_multiplier']})\n"
            f"• Технічно: {snapshot['tech_name']} (x{snapshot['tech_multiplier']})\n"
            f"• Комплект: {snapshot['comp_name']} (x{snapshot['comp_multiplier']})\n"
            f"• Гарантія: {snapshot['warn_name']} (x{snapshot['warn_multiplier']})\n"
            f"• Бренд: {snapshot['brand_name']} (x{snapshot['brand_multiplier']})\n"
            f"• Продаж: {snapshot['urgent_name']} (x{snapshot['urgent_multiplier']})\n\n"
            f"💰 <b>Справедлива ринкова ціна:</b>\n"
            f"<code>{final_price:,.2f} {snapshot['currency']}</code>{nbu_info}"
        )

        await callback.message.edit_text(
            report,
            reply_markup=keyboards.get_receipt_actions_kb(val_id),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error calculating price: {e}", exc_info=True)
        await callback.message.answer(f"❌ Виникла помилка при розрахунку: {e}")
        
    await state.clear()

@router.callback_query(F.data.startswith("receipt_img_"))
async def process_receipt_image(callback: CallbackQuery):
    val_id = int(callback.data.split("_")[2])
    valuation = crud.get_valuation(val_id)
    
    if not valuation:
        logger.warning(f"User {callback.from_user.id} requested missing receipt #{val_id}")
        await callback.answer("Оцінку не знайдено в базі.", show_alert=True)
        return
        
    await callback.answer("Генерую фото-сертифікат... ⏳")
    logger.info(f"User {callback.from_user.id} generated image receipt for valuation #{val_id}")
    
    snapshot = json.loads(valuation["snapshot_json"])
    final_price = valuation["final_price"]
    
    img_io = receipt.generate_receipt_image(snapshot, final_price)
    
    photo = BufferedInputFile(img_io.read(), filename=f"evs_receipt_{val_id}.png")
    
    user_report_num = snapshot.get("user_report_num", val_id)
    await callback.message.answer_photo(
        photo=photo,
        caption=f"📸 Ваш сертифікат оцінки #{user_report_num}."
    )

@router.callback_query()
async def process_unknown_callback(callback: CallbackQuery):
    logger.warning(f"User {callback.from_user.id} triggered unknown or expired callback: {callback.data}")
    await callback.answer("Ця кнопка більше не активна або сталася помилка. Спробуйте /evaluate знову.", show_alert=True)
