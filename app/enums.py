from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"
    COURIER = "COURIER"


class OrderStatus(StrEnum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    PROBLEM = "PROBLEM"
    CANCELED = "CANCELED"


class ReasonType(StrEnum):
    PROBLEM = "PROBLEM"
    CANCELED = "CANCELED"


class OrderPriority(StrEnum):
    VIP = "VIP"
    URGENT = "URGENT"
    NORMAL = "NORMAL"


class BatchStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

