
from typing import TypedDict, List, Optional, NewType

from datetime import datetime


PDF_File = NewType('PDF_File', bytes)


class HtmlCssPathType(TypedDict):
    html: str
    css: str


class ItemInPurchasedItem(TypedDict):
    id: int
    name: str
    price: float


class PurchasedItem(TypedDict):
    item: ItemInPurchasedItem
    total_items: int


class InvoiceType(TypedDict):
    id: int
    owner: str
    email: str
    date: datetime
    purchased_items: List[PurchasedItem]
    total_price: Optional[float]
