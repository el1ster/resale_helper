import math

class ValuationEngine:
    """
    Математичний рушій для розрахунку залишкової вартості активів.
    Використовує динамічну експоненційну модель.
    """

    # Мінімальна залишкова вартість (Price Floor) залежить від стану, але базова - 20%
    BASE_RESIDUAL_VALUE_FLOOR = 0.20
    VINTAGE_MULTIPLIER_THRESHOLD = 1.5

    @classmethod
    def calculate_k_age(cls, age_months: int, lifespan_months: int, is_sealed: bool = False) -> float:
        """
        Розрахунок коефіцієнта віку (амортизації) за логістично-експоненційною моделлю.
        """
        if age_months <= 0:
            return 1.0

        if lifespan_months <= 0:
            raise ValueError("lifespan_months повинен бути більше 0")

        # Для меблів (lifespan_months >= 360) знецінення відбувається набагато повільніше (floor 40%)
        # Для електроніки (lifespan_months <= 120) floor 20%
        floor = cls.BASE_RESIDUAL_VALUE_FLOOR
        if lifespan_months >= 360:
            floor = 0.40
        elif lifespan_months >= 240:
            floor = 0.30

        # Обробка "Новий у коробці" але старий
        is_vintage = age_months >= (lifespan_months * cls.VINTAGE_MULTIPLIER_THRESHOLD)
        if is_sealed and is_vintage:
            return max(1.0 - (age_months * 0.005), 0.8) # Майже не втрачає в ціні

        # Динамічний розрахунок темпу старіння (half-life)
        # Використовуємо формулу K = Floor + (1 - Floor) * e^(-k * t)
        # Підбираємо k так, щоб на етапі lifespan_months ціна досягала Floor + 5%
        target_value = floor + 0.05
        # 1 - d = exp(ln((target - floor) / (1 - floor)) / lifespan)
        k = -math.log((target_value - floor) / (1.0 - floor)) / lifespan_months
        
        k_age = floor + (1.0 - floor) * math.exp(-k * age_months)

        return max(k_age, floor)

    @classmethod
    def calculate_price(
        cls, 
        base_price: float, 
        age_months: int, 
        lifespan_months: int, 
        k_phys: float, 
        k_tech: float, 
        k_comp: float, 
        k_warn: float, 
        k_brand: float, 
        k_urgent: float,
        phys_code: str = "good"
    ) -> float:
        """
        Головна функція розрахунку фінальної вартості.
        """
        if base_price <= 0:
            raise ValueError("base_price повинен бути більшим за 0")

        is_sealed = (phys_code == "sealed")
        
        # 1. Вік
        k_age = cls.calculate_k_age(age_months, lifespan_months, is_sealed)

        # 2. Множники
        multipliers_product = k_phys * k_tech * k_comp * k_warn * k_brand * k_urgent
        
        # 3. Базова формула
        final_price = base_price * k_age * multipliers_product

        # 4. Абсолютний захист (якщо брухт - дозволяємо впасти до 2%, інакше мінімум 10% від бази * k_urgent)
        if k_tech < 0.5:
            min_possible_price = base_price * 0.02
        else:
            # Навіть якщо все погано, робоча річ не може коштувати менше 10% (з урахуванням терміновості)
            min_possible_price = base_price * 0.10 * k_urgent
        
        return max(final_price, min_possible_price)
