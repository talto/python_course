from infrastructure.database import engine, SessionFactory
from infrastructure.orm import Base
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from domain.services import WarehouseService

Base.metadata.create_all(engine)


uow_factory = lambda: SqlAlchemyUnitOfWork(SessionFactory)

warehouse_service = WarehouseService(uow_factory)

def main():
    new_product = warehouse_service.create_product(
        name="test1",
        quantity=1,
        price=100,
    )
    print(f"Created product → {new_product}")

if __name__ == "__main__":
    main()
