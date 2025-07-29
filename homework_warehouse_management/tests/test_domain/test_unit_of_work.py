import pytest
from domain.unit_of_work import UnitOfWork

def test_unit_of_work_interface():
    class DummyUoW(UnitOfWork):
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def commit(self): pass
        def rollback(self): pass

    uow = DummyUoW()
    with uow:
        uow.commit()
        uow.rollback()
