from domain.services import WarehouseService
from domain.models import Product, Order
from domain.unit_of_work import UnitOfWork

class FakeRepo:
    def __init__(self):
        self.items = []
        self._id = 1

    def add(self, obj):
        obj.id = self._id
        self._id += 1
        self.items.append(obj)

    def get(self, obj_id):
        return next((i for i in self.items if i.id == obj_id), None)

    def list(self):
        return list(self.items)

class DummyUoW(UnitOfWork):
    def __enter__(self):
        self.products = FakeRepo()
        self.orders = FakeRepo()
        return self
    def __exit__(self, *args): pass
    def commit(self): pass
    def rollback(self): pass

def test_create_product_and_assign_id():
    service = WarehouseService(lambda: DummyUoW())
    product = service.create_product(name="keyboard", quantity=5, price=250.0)
    assert product.id == 1

def test_create_order_with_products():
    service = WarehouseService(lambda: DummyUoW())
    p = Product(id=1, name="mouse", quantity=3, price=100.0)
    with DummyUoW() as uow:
        uow.products.add(p)

    order = service.create_order(products=[p])
    assert order.products[0].name == "mouse"
