from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.db import SessionFactory
from app.enums import OrderPriority, ReasonType
from app.models import PickupPoint, ProblemReason
from app.repositories.courier import CourierRepository
from app.services.orders import OrderService


async def main() -> None:
    async with SessionFactory() as session:
        await session.execute(delete(ProblemReason))
        await session.execute(delete(PickupPoint))

        points = [
            PickupPoint(
                name="Салон Центр",
                address_text="Москва, Тверская 1",
                lat=55.7579,
                lon=37.6156,
                base_eta_minutes=25,
                is_active=True,
            ),
            PickupPoint(
                name="Салон Юг",
                address_text="Москва, Варшавское шоссе 10",
                lat=55.7058,
                lon=37.6251,
                base_eta_minutes=35,
                is_active=True,
            ),
        ]
        session.add_all(points)
        session.add_all(
            [
                ProblemReason(code="NO_ANSWER", text="Клиент не отвечает", type=ReasonType.PROBLEM, sort_order=10),
                ProblemReason(code="BAD_ADDRESS", text="Неверный адрес", type=ReasonType.PROBLEM, sort_order=20),
                ProblemReason(code="REFUSED", text="Отказ получателя", type=ReasonType.PROBLEM, sort_order=30),
                ProblemReason(code="NO_ACCESS", text="Нет доступа", type=ReasonType.PROBLEM, sort_order=40),
                ProblemReason(code="OTHER", text="Другое", type=ReasonType.PROBLEM, sort_order=50),
                ProblemReason(code="CLIENT_CANCEL", text="Отмена клиентом", type=ReasonType.CANCELED, sort_order=10),
                ProblemReason(code="OUT_OF_STOCK", text="Нет в наличии", type=ReasonType.CANCELED, sort_order=20),
                ProblemReason(code="OTHER_CANCEL", text="Другое", type=ReasonType.CANCELED, sort_order=30),
            ]
        )

        courier_repo = CourierRepository(session)
        await courier_repo.upsert(100001, "Тестовый Курьер 1", "+79990000001")
        await courier_repo.upsert(100002, "Тестовый Курьер 2", "+79990000002")
        await session.commit()

        point = points[0]
        service = OrderService(session)
        for idx, priority in enumerate([OrderPriority.VIP, OrderPriority.URGENT, OrderPriority.NORMAL], start=1):
            await service.create_order(
                {
                    "order_number": f"TEST-{idx:03d}",
                    "customer_name": "Иван Заказчик",
                    "customer_phone": "+79991112233",
                    "recipient_name": f"Получатель {idx}",
                    "recipient_phone": f"+79990000{idx:03d}",
                    "delivery_window_start": datetime.now(timezone.utc) + timedelta(hours=1),
                    "delivery_window_end": datetime.now(timezone.utc) + timedelta(hours=2 + idx),
                    "comment": "Тестовый заказ",
                    "address_text": f"Москва, улица Пример {idx}",
                    "entrance": "1",
                    "floor": "2",
                    "apartment": f"{idx}",
                    "intercom_code": "12К",
                    "details": "Позвонить за 10 минут",
                    "lat": 55.75 + idx * 0.01,
                    "lon": 37.61 + idx * 0.01,
                    "pickup_point_id": point.id,
                    "priority": priority,
                },
                actor_tg_user_id=0,
            )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
