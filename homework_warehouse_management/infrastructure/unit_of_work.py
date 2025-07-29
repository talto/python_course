from domain.unit_of_work import UnitOfWork
from infrastructure.repositories import (
    SqlAlchemyProductRepository,
    SqlAlchemyOrderRepository,
)

class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session = None
        self.products = None
        self.orders = None

    def __enter__(self):
        self.session = self._session_factory()
        self.products = SqlAlchemyProductRepository(self.session)
        self.orders   = SqlAlchemyOrderRepository(self.session)
        self.session.begin()
        return self

    def __exit__(self, exc_type, exc_val, tb):
        try:
            self.rollback() if exc_type else self.commit()
        finally:
            self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()