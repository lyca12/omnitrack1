# models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"

class OrderStatus(Enum):
    PLACED = "placed"
    PAID = "paid"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass
class User:
    id: int
    username: str
    role: UserRole
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Product:
    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    category: Optional[str]
    low_stock_threshold: int = 10
    sku:Optional[str] = None

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.low_stock_threshold

@dataclass
class OrderItem:
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

@dataclass
class Order:
    id: int
    username: str
    status: OrderStatus
    total_amount: float
    items: List[OrderItem]
    created_at: datetime
    updated_at: datetime

@dataclass
class CartItem:
    product_id: int
    name: str
    price: float
    quantity: int
    stock_quantity: int
