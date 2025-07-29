from typing import List, Callable
from .models import Product, Order
from domain.unit_of_work import UnitOfWork

class WarehouseService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory     

    def create_product(self, *, name: str, quantity: int, price: float) -> Product:
        with self._uow_factory() as uow:    
            product = Product(id=None, name=name, quantity=quantity, price=price)
            uow.products.add(product)
            return product

    def create_order(self, *, products: List[Product]) -> Order:
        with self._uow_factory() as uow:
            order = Order(id=None, products=products)
            uow.orders.add(order)
            return order
