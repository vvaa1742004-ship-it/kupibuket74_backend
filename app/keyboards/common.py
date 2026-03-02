from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cancel_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def yes_no_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data=confirm_data),
        InlineKeyboardButton(text="Отмена", callback_data=cancel_data),
    )
    return builder.as_markup()


def webapp_keyboard(label: str, url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url)))
    return builder.as_markup()
