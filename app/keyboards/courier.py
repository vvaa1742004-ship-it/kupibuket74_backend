from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.enums import OrderStatus
from app.models import Order


def courier_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Доступные заказы", callback_data="courier:available"))
    builder.row(InlineKeyboardButton(text="Мои заказы", callback_data="courier:mine"))
    builder.row(InlineKeyboardButton(text="Маршрут", callback_data="courier:route"))
    builder.row(InlineKeyboardButton(text="Моя статистика", callback_data="courier:stats"))
    return builder.as_markup()


def order_card_actions(order: Order) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if order.status == OrderStatus.NEW:
        builder.row(InlineKeyboardButton(text="Взять", callback_data=f"take:{order.id}"))
    if order.status == OrderStatus.ASSIGNED:
        builder.row(InlineKeyboardButton(text="Забрал из отдела", callback_data=f"pickup_done:{order.id}"))
    if order.status == OrderStatus.PICKED_UP:
        builder.row(InlineKeyboardButton(text="Доставлено", callback_data=f"delivered:{order.id}"))
        builder.row(InlineKeyboardButton(text="Проблема", callback_data=f"problem:{order.id}"))
    if order.status in {OrderStatus.ASSIGNED, OrderStatus.PICKED_UP}:
        builder.row(InlineKeyboardButton(text="Отказаться", callback_data=f"release:{order.id}"))
        builder.row(
            InlineKeyboardButton(text="Фото подтверждения", callback_data=f"proof:{order.id}")
        )
    builder.row(InlineKeyboardButton(text="Открыть заказ", callback_data=f"order:view:{order.id}"))
    return builder.as_markup()


def pagination_keyboard(prefix: str, page: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="⬅️", callback_data=f"{prefix}:{page - 1}")
    if has_more:
        builder.button(text="➡️", callback_data=f"{prefix}:{page + 1}")
    return builder.as_markup()


def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Включить отслеживание", request_location=True)],
        ],
        resize_keyboard=True,
    )

