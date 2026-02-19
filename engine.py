import math

class ValuationEngine:
    """
    Математичний рушій для розрахунку залишкової вартості активів.
    Використовує експоненційну модель амортизації з урахуванням залишкової вартості (Price Floor)
    та обробкою крайових випадків типу New Old Stock (NOS).
    """

    # Мінімальна залишкова вартість (10% від базової ціни)
    RESIDUAL_VALUE_FLOOR = 0.10
    
    # Поріг вінтажності (якщо вік перевищує lifespan у цей раз, товар вважається потенційним ретро)
    VINTAGE_MULTIPLIER_THRESHOLD = 1.5

    @classmethod
    def calculate_k_age(cls, age_months: int, lifespan_months: int, is_sealed: bool = False) -> float:
        """
        Розрахунок коефіцієнта віку (амортизації) за експоненційною моделлю.
        
        Формула: K_age = (1 - d)^age_months
        де d - місячний коефіцієнт знецінення, розрахований так, щоб 
        за час lifespan_months вартість впала до RESIDUAL_VALUE_FLOOR.
        """
        if age_months <= 0:
            return 1.0

        if lifespan_months <= 0:
            raise ValueError("lifespan_months повинен бути більше 0")

        # Розрахунок місячного decay rate (d)
        # RESIDUAL_VALUE_FLOOR = (1 - d)^lifespan_months
        # ln(RESIDUAL_VALUE_FLOOR) = lifespan_months * ln(1 - d)
        # 1 - d = exp(ln(RESIDUAL_VALUE_FLOOR) / lifespan_months)
        one_minus_d = math.exp(math.log(cls.RESIDUAL_VALUE_FLOOR) / lifespan_months)
        
        k_age = math.pow(one_minus_d, age_months)

        # Обробка крайового випадку "New Old Stock" (Вінтаж + Запаковано)
        is_vintage = age_months >= (lifespan_months * cls.VINTAGE_MULTIPLIER_THRESHOLD)
        if is_sealed and is_vintage:
            # Для запечатаного ретро-товару ми суттєво пом'якшуємо амортизацію.
            # Наприклад, фіксуємо k_age на рівні 0.8 (товар лише трохи втрачає в ціні через застарілість)
            return max(k_age, 0.8)

        # Звичайна залишкова вартість не може впасти нижче RESIDUAL_VALUE_FLOOR
        return max(k_age, cls.RESIDUAL_VALUE_FLOOR)

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
        
        k_age = cls.calculate_k_age(age_months, lifespan_months, is_sealed)

        # Якщо пристрій повністю зламаний ("broken" з multiplier ~0.3), 
        # ми дозволяємо ціні впасти нижче базового RESIDUAL_VALUE_FLOOR, оскільки це вже брухт.
        if k_tech < 0.5:
            floor = 0.01 # 1% для брухту
        else:
            floor = cls.RESIDUAL_VALUE_FLOOR

        final_price = base_price * k_age * k_phys * k_tech * k_comp * k_warn * k_brand * k_urgent

        # Захист "підвалу" цін
        min_possible_price = base_price * floor
        
        return max(final_price, min_possible_price)
