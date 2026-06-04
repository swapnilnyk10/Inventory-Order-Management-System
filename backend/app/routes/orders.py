from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import Order, OrderItem, Product, Customer
from app.schemas.schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    if not db.query(Customer).filter(Customer.id == data.customer_id).first():
        raise HTTPException(404, "Customer not found")
    if not data.items:
        raise HTTPException(400, "Order must have at least one item")

    total = 0.0
    resolved = []
    for item in data.items:
        p = db.query(Product).filter(Product.id == item.product_id).first()
        if not p:
            raise HTTPException(404, f"Product {item.product_id} not found")
        if p.quantity < item.quantity:
            raise HTTPException(
                400,
                f"Insufficient stock for '{p.name}'. Available: {p.quantity}, requested: {item.quantity}"
            )
        total += p.price * item.quantity
        resolved.append((p, item.quantity, p.price))

    order = Order(customer_id=data.customer_id, total_amount=round(total, 2))
    db.add(order)
    db.flush()

    for p, qty, price in resolved:
        db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=qty, unit_price=price))
        p.quantity -= qty

    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(404, "Order not found")
    return o


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(404, "Order not found")
    for item in o.items:
        item.product.quantity += item.quantity  # restore stock
    db.delete(o)
    db.commit()
