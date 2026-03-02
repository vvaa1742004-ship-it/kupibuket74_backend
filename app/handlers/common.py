from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.config import settings
from app.enums import Role
from app.keyboards.admin import admin_menu
from app.keyboards.common import webapp_keyboard
from app.keyboards.courier import courier_menu, location_keyboard

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, role: Role | None) -> None:
    if role == Role.ADMIN:
        await message.answer("Панель администратора", reply_markup=admin_menu())
        await message.answer(
            "Mini App",
            reply_markup=webapp_keyboard(
                "Открыть панель администратора", f"{settings.webapp_base_url}/admin"
            ),
        )
        return
    if role == Role.COURIER:
        await message.answer("Панель курьера", reply_markup=courier_menu())
        await message.answer(
            "Mini App",
            reply_markup=webapp_keyboard(
                "Открыть панель курьера", f"{settings.webapp_base_url}/courier"
            ),
        )
        await message.answer("Трекинг", reply_markup=location_keyboard())
        return
    await message.answer("Доступ закрыт. Обратитесь к администратору.")


@router.message(F.text == "❌ Отмена")
async def cancel_form(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Состояние очищено")


@router.message(F.text == "⬅️ Назад")
async def back_form(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    history = data.get("history", [])
    if not history:
        await message.answer("Назад недоступно")
        return
    prev = history.pop()
    await state.set_data({**data, "history": history})
    await state.set_state(prev)
    await message.answer("Вернулся на предыдущий шаг")
