from datetime import datetime

from pydantic import BaseModel


class TicketItem(BaseModel):
    index: int
    name: str
    price: float
    quantity: float
    total: float


class Ticket(BaseModel):
    dt: datetime
    seller: bytes
    items: list[TicketItem]
    total: float
