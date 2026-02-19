from aiogram.fsm.state import State, StatesGroup

class ValuationFSM(StatesGroup):
    """
    Машина станів (FSM) для процесу оцінки активу.
    Кожен крок відповідає за збір одного з множників математичної моделі.
    """
    choosing_category = State()   # Вибір категорії товару (id -> lifespan_months)
    entering_base_price = State() # Введення базової (початкової) ціни
    entering_age = State()        # Введення віку товару (місяці/роки)
    
    # Вибір коефіцієнтів
    choosing_phys = State()       # Фізичний стан (K_phys)
    choosing_tech = State()       # Технічний стан (K_tech)
    choosing_comp = State()       # Комплектація (K_comp)
    choosing_warn = State()       # Гарантія (K_warn)
    choosing_brand = State()      # Ліквідність бренду (K_brand)
    choosing_urgent = State()     # Терміновість (K_urgent)
