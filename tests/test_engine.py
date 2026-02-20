import unittest
from engine import ValuationEngine

class TestValuationEngine(unittest.TestCase):

    def test_k_age_new_item(self):
        # Товар новий (0 місяців)
        k_age = ValuationEngine.calculate_k_age(0, 60)
        self.assertEqual(k_age, 1.0)

    def test_k_age_normal_decay(self):
        # Телефон (lifespan 60). В кінці строку життя має досягти ~ Floor + 5% (0.25)
        k_age = ValuationEngine.calculate_k_age(60, 60, brand_multiplier=1.0)
        self.assertAlmostEqual(k_age, 0.25, places=2)
        
        # Половина строку (30 міс)
        k_age_half = ValuationEngine.calculate_k_age(30, 60, brand_multiplier=1.0)
        self.assertTrue(0.25 < k_age_half < 1.0)

    def test_k_age_residual_floor(self):
        # Товару 10 років (120 міс), але lifespan 5 років (60 міс).
        # Обмеження для електроніки: 0.20 (20%)
        k_age = ValuationEngine.calculate_k_age(120, 60, brand_multiplier=1.0)
        self.assertAlmostEqual(k_age, 0.20, places=2)

    def test_new_old_stock(self):
        # Вінтажний телефон (15 років = 180 місяців). Lifespan = 60.
        # Фізичний стан - "sealed" (Запечатаний)
        k_age = ValuationEngine.calculate_k_age(180, 60, is_sealed=True)
        # Через New Old Stock логіку, k_age фіксується на рівні 0.8
        self.assertAlmostEqual(k_age, 0.8, places=1)

    def test_calculate_price_normal(self):
        # Базова ціна 1000, вік 60 міс (lifespan 60 -> k_age ~ 0.25)
        # Всі інші коефіцієнти ідеальні (1.0)
        price = ValuationEngine.calculate_price(1000, 60, 60, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, phys_code="perfect")
        self.assertAlmostEqual(price, 250.0, places=0)

    def test_calculate_price_broken(self):
        # Розбитий телефон в кінці строку служби
        # base=1000, age=60 (k_age=0.25)
        # k_phys=0.5 (poor), k_tech=0.3 (broken)
        # final = 1000 * 0.25 * 0.5 * 0.3 = 37.5
        price = ValuationEngine.calculate_price(1000, 60, 60, 0.5, 0.3, 1.0, 1.0, 1.0, 1.0, phys_code="poor")
        self.assertAlmostEqual(price, 37.5, places=1)

if __name__ == '__main__':
    unittest.main()
