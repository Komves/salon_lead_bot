from aiogram.fsm.state import State, StatesGroup


class LeadFlow(StatesGroup):
    choosing_service = State()
    choosing_specialist = State()
    entering_date = State()
    entering_time = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()


class AdminReplyFlow(StatesGroup):
    entering_message = State()


class AdminEditTimeFlow(StatesGroup):
    entering_datetime = State()
