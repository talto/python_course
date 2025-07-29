# infrastructure/orm.py
from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class ProductORM(Base):
    __tablename__ = "products"
    id       = Column(Integer, primary_key=True)
    name     = Column(String)
    quantity = Column(Integer)
    price    = Column(Float)

class OrderORM(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)

order_product_associations = Table(
    "order_product_associations", Base.metadata,       # ← исправил опечатку
    Column("order_id",   ForeignKey("orders.id")),
    Column("product_id", ForeignKey("products.id")),
)

OrderORM.products = relationship(
    "ProductORM",
    secondary=order_product_associations,
)
