from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from app.enums import OrderPriority
from app.models import Order


def priority_weight(priority: OrderPriority) -> int:
    return {
        OrderPriority.VIP: 0,
        OrderPriority.URGENT: 1,
        OrderPriority.NORMAL: 2,
    }[priority]


def priority_label(priority: OrderPriority) -> str:
    return {
        OrderPriority.VIP: "🔴 VIP",
        OrderPriority.URGENT: "🟠 Срочный",
        OrderPriority.NORMAL: "⚪️ Обычный",
    }[priority]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return round(2 * radius * asin(sqrt(a)), 2)


def maps_link(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"


def order_card_text(order: Order, route_position: int | None = None, extra_eta: int | None = None) -> str:
    priority = priority_label(order.priority)
    position = f"Маршрут: {route_position}\n" if route_position else ""
    eta = extra_eta if extra_eta is not None else order.eta_minutes
    phones = f"Заказчик: {order.customer_phone}\nПолучатель: {order.recipient_phone}"
    pickup_name = order.pickup_point.name if order.pickup_point else "Не указана"
    return (
        f"{priority}\n"
        f"{position}"
        f"№ {order.order_number}\n"
        f"Статус: {order.status.value}\n"
        f"Адрес: {order.address_text}\n"
        f"Окно: {order.delivery_window_start:%d.%m %H:%M} - {order.delivery_window_end:%H:%M}\n"
        f"Точка: {pickup_name}\n"
        f"ETA: {eta or '-'} мин\n"
        f"{phones}\n"
        f"Комментарий: {order.comment or '-'}"
    )

