from domain.models import Product, Order

def test_product_fields():
    p = Product(id=1, name="apple", quantity=10, price=3.5)
    assert p.id == 1
    assert p.name == "apple"
    assert p.quantity == 10
    assert p.price == 3.5

def test_order_fields():
    p1 = Product(id=1, name="apple", quantity=10, price=3.5)
    p2 = Product(id=2, name="banana", quantity=5, price=2.0)
    o = Order(id=100, products=[p1, p2])
    assert o.id == 100
    assert o.products == [p1, p2]