from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class User:
    id: int
    username: str
    role: str
    created_at: datetime

@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    category: str
    created_at: datetime
    updated_at: datetime

@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

@dataclass
class Order:
    id: int
    username: str
    status: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: Optional[List[OrderItem]] = None

@dataclass
class InventoryTransaction:
    id: int
    product_id: int
    transaction_type: str
    quantity_change: int
    reference_id: Optional[str]
    notes: Optional[str]
    created_at: datetime

@dataclass
class CartItem:
    id: int
    username: str
    product_id: int
    product_name: str
    quantity: int
    price: float
    stock_quantity: int
    created_at: datetime
