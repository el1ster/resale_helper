import unittest
from engine import ValuationEngine

class TestValuationEngine(unittest.TestCase):

    def test_k_age_new_item(self):
        # Товар новий (0 місяців)
        k_age = ValuationEngine.calculate_k_age(0, 60)
        self.assertEqual(k_age, 1.0)

    def test_k_age_normal_decay(self):
        # Телефон (lifespan 60). В кінці строку життя (60 міс) має досягти RESIDUAL_VALUE_FLOOR (0.1)
        k_age = ValuationEngine.calculate_k_age(60, 60)
        self.assertAlmostEqual(k_age, 0.1, places=2)
        
        # Половина строку (30 міс). Експонента: (0.1)^(30/60) = sqrt(0.1) ≈ 0.316
        k_age_half = ValuationEngine.calculate_k_age(30, 60)
        self.assertAlmostEqual(k_age_half, 0.316, places=2)

    def test_k_age_residual_floor(self):
        # Товару 10 років (120 міс), але lifespan 5 років (60 міс).
        # Без обмеження ціна впала б до 0.01. З обмеженням має бути 0.1 (Floor)
        k_age = ValuationEngine.calculate_k_age(120, 60)
        self.assertEqual(k_age, 0.1)

    def test_new_old_stock(self):
        # Вінтажний телефон (15 років = 180 місяців). Lifespan = 60.
        # Фізичний стан - "sealed" (Запечатаний)
        k_age = ValuationEngine.calculate_k_age(180, 60, is_sealed=True)
        # Через New Old Stock логіку, k_age фіксується на високому рівні (0.8), ігноруючи Floor 0.1
        self.assertEqual(k_age, 0.8)

    def test_calculate_price_normal(self):
        # Базова ціна 1000, вік 30 міс (lifespan 60 -> k_age 0.316)
        # Всі інші коефіцієнти ідеальні (1.0)
        price = ValuationEngine.calculate_price(1000, 30, 60, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, phys_code="perfect")
        self.assertAlmostEqual(price, 316.22, places=1)

    def test_calculate_price_broken(self):
        # Розбитий телефон в кінці строку служби
        # base=1000, age=60 (k_age=0.1)
        # k_phys=0.5 (poor), k_tech=0.3 (broken)
        # final = 1000 * 0.1 * 0.5 * 0.3 = 15
        price = ValuationEngine.calculate_price(1000, 60, 60, 0.5, 0.3, 1.0, 1.0, 1.0, 1.0, phys_code="poor")
        self.assertAlmostEqual(price, 15.0, places=1)
        # Floor для брухту становить 1%, тому 15 проходить.

if __name__ == '__main__':
    unittest.main()
