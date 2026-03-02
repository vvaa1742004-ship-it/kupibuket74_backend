from __future__ import annotations

from app.models import Order
from app.services.formatters import haversine_km, priority_weight


class RoutingService:
    @staticmethod
    def reorder(orders: list[Order], origin: tuple[float, float] | None) -> list[Order]:
        def distance(order: Order) -> float:
            if origin and order.lat is not None and order.lon is not None:
                return haversine_km(origin[0], origin[1], order.lat, order.lon)
            if order.pickup_point and order.lat is not None and order.lon is not None:
                return haversine_km(order.pickup_point.lat, order.pickup_point.lon, order.lat, order.lon)
            return 9999.0

        return sorted(
            orders,
            key=lambda item: (
                priority_weight(item.priority),
                item.delivery_window_end,
                distance(item),
                item.created_at,
            ),
        )

