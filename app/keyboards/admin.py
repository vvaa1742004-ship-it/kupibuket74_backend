from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.enums import OrderPriority
from app.models import Order, PickupPoint, ProblemReason
from app.services.formatters import priority_label


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Создать заказ", callback_data="admin:create_order"))
    builder.row(InlineKeyboardButton(text="Найти заказ", callback_data="admin:search"))
    builder.row(InlineKeyboardButton(text="Аналитика", callback_data="admin:analytics"))
    builder.row(InlineKeyboardButton(text="Курьеры", callback_data="admin:couriers"))
    builder.row(InlineKeyboardButton(text="Сбросить мою форму", callback_data="admin:reset_form"))
    return builder.as_markup()


def pickup_points_keyboard(points: list[PickupPoint]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for point in points:
        builder.row(InlineKeyboardButton(text=point.name, callback_data=f"pickup:{point.id}"))
    return builder.as_markup()


def priority_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for priority in OrderPriority:
        builder.row(
            InlineKeyboardButton(
                text=priority_label(priority), callback_data=f"priority:{priority.value}"
            )
        )
    return builder.as_markup()


def order_admin_actions(order: Order) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Открыть", callback_data=f"order:view:{order.id}"))
    builder.row(InlineKeyboardButton(text="Отменить", callback_data=f"order:cancel:{order.id}"))
    builder.row(InlineKeyboardButton(text="PROBLEM", callback_data=f"order:problem:{order.id}"))
    builder.row(InlineKeyboardButton(text="Сменить приоритет", callback_data=f"order:reprio:{order.id}"))
    return builder.as_markup()


def reason_keyboard(reasons: list[ProblemReason], prefix: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for reason in reasons:
        builder.row(
            InlineKeyboardButton(text=reason.text, callback_data=f"{prefix}:{reason.id}")
        )
    return builder.as_markup()

