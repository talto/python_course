from domain.models import Product, Order
from domain.repositories import ProductRepository, OrderRepository

class InMemoryProductRepository(ProductRepository):
    def __init__(self):
        self.data = []
        self._id = 1

    def add(self, product):
        product.id = self._id
        self._id += 1
        self.data.append(product)

    def get(self, product_id):
        return next((p for p in self.data if p.id == product_id), None)

    def list(self):
        return list(self.data)

class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self.data = []
        self._id = 1

    def add(self, order):
        order.id = self._id
        self._id += 1
        self.data.append(order)

    def get(self, order_id):
        return next((o for o in self.data if o.id == order_id), None)

    def list(self):
        return list(self.data)

def test_add_and_get_product():
    repo = InMemoryProductRepository()
    p = Product(id=None, name="test", quantity=1, price=1.0)
    repo.add(p)
    assert p.id == 1
    assert repo.get(1).name == "test"
    assert len(repo.list()) == 1

def test_add_and_get_order():
    p = Product(id=1, name="apple", quantity=1, price=1.0)
    repo = InMemoryOrderRepository()
    o = Order(id=None, products=[p])
    repo.add(o)
    assert o.id == 1
    assert repo.get(1).products[0].name == "apple"
    assert len(repo.list()) == 1
