from pydantic import BaseModel


class FoodPandaItem(BaseModel):
    name: str
    quantity: int
    price: float

class Customer(BaseModel):
    name: str
    email: str
    phone: str

class Restaurant(BaseModel):
    name: str
    address: str
    phone: str

class FoodPandaOrder(BaseModel):
    order_id: str
    items: list[FoodPandaItem]
    customer: Customer
    restaurant: Restaurant
    total_amount: float
    order_timestamp: str
    delivery_address: str
    other_fees: float
    delivery_timestamp: str
    refund_status: str
    refund_amount: float
    refund_method: str
    

current_order : FoodPandaOrder = FoodPandaOrder(
    order_id="12345",
    items=[
        FoodPandaItem(name="Burger", quantity=2, price=6),
        FoodPandaItem(name="Fries", quantity=1, price=3),
    ],
    customer=Customer(name="John Doe", email="john.doe@example.com", phone="123-456-7890"),
    restaurant=Restaurant(name="Burger King", address="123 Main St", phone="123-456-7890"),
    total_amount=10,
    other_fees=2,
    order_timestamp="2023-10-01 12:00:00",
    delivery_address="456 Oak Ave",
    delivery_timestamp="2023-10-01 13:00:00",
    refund_status="None",
    refund_amount=0,
    refund_method="None"
)