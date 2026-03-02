from __future__ import annotations

from app.repositories.order import OrderRepository


class AnalyticsService:
    def __init__(self, session) -> None:
        self.repo = OrderRepository(session)

    async def summary_text(self) -> str:
        courier_stats = await self.repo.stats_per_courier()
        pickup_stats = await self.repo.stats_per_pickup_point()
        courier_lines = [
            (
                f"{row['courier_id']}: взято {row['taken']}, выполнено {row['delivered']}, "
                f"ср. {row['avg_minutes']} мин, проблемных {row['problem_pct']}%, "
                f"просрочек {row['late_pct']}%"
            )
            for row in courier_stats
        ] or ["Нет данных"]
        point_lines = [
            f"{row['pickup_point_id']}: {row['orders']} заказов, ср. {round(float(row['avg_minutes'] or 0), 1)} мин"
            for row in pickup_stats
        ] or ["Нет данных"]
        return "Курьеры:\n" + "\n".join(courier_lines) + "\n\nТочки выдачи:\n" + "\n".join(point_lines)

