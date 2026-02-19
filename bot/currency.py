import aiohttp
import logging

logger = logging.getLogger(__name__)

# Fallback rates if NBU is down (to UAH)
FALLBACK_RATES = {
    "USD": 40.0,
    "EUR": 43.5,
    "UAH": 1.0
}

async def get_nbu_rate(currency_code: str) -> float:
    """
    Отримує курс валюти по відношенню до гривні (UAH) від НБУ.
    Повертає множник (наприклад, 1 USD = 40.0 UAH).
    """
    if currency_code == "UAH":
        return 1.0
        
    url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency_code}&json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        rate = float(data[0]["rate"])
                        logger.info(f"Отримано курс НБУ для {currency_code}: {rate}")
                        return rate
    except Exception as e:
        logger.error(f"Помилка при отриманні курсу {currency_code} від НБУ: {e}")
        
    logger.warning(f"API НБУ недоступне. Використовуємо fallback курс для {currency_code}")
    return FALLBACK_RATES.get(currency_code, 1.0)
