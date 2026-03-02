from aiogram.fsm.state import State, StatesGroup


class OrderCreateStates(StatesGroup):
    pickup_point = State()
    priority = State()
    order_number = State()
    customer = State()
    recipient = State()
    delivery_window = State()
    address = State()
    comment = State()
    confirm = State()


class ProblemStates(StatesGroup):
    choose_reason = State()
    custom_reason = State()
    proof_photo = State()
    proof_comment = State()

