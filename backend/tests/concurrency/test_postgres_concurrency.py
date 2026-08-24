import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.exceptions import BusinessError
from app.models import Material, Project, Role, StockMovement, User
from app.services.inventory import InventoryService

POSTGRES_URL = os.getenv("TEST_POSTGRES_URL")


@pytest.mark.skipif(not POSTGRES_URL, reason="需要独立 PostgreSQL 测试库和行级锁")
def test_all_concurrent_stock_scenarios():
    """Real PostgreSQL test: outbound, reserve, mixed operations and duplicate retries."""
    engine = create_engine(POSTGRES_URL, pool_size=10)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid.uuid4().hex[:10]
    with sessions() as db:
        role = Role(name=f"并发测试-{suffix}", permissions=["*"])
        db.add(role)
        db.flush()
        user = User(
            username=f"concurrent-{suffix}",
            full_name="并发测试",
            password_hash="not-used",
            role_id=role.id,
        )
        db.add(user)
        db.flush()
        projects = [
            Project(code=f"CP-{suffix}-{index}", name=f"并发项目 {index}", manager_id=user.id)
            for index in range(2)
        ]
        db.add_all(projects)
        db.commit()
        user_id = user.id
        project_ids = [project.id for project in projects]

    def new_material(label: str) -> int:
        with sessions() as db:
            item = Material(
                code=f"CON-{label}-{suffix}",
                name=f"并发物料 {label}",
                quantity=Decimal("5"),
                created_by_id=user_id,
            )
            db.add(item)
            db.commit()
            return item.id

    def run_parallel(actions):
        def execute(action):
            try:
                with sessions() as db:
                    return "success", action(InventoryService(db, user_id, str(uuid.uuid4())))
            except BusinessError as exc:
                return "error", exc.code

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(execute, actions))

    outbound_id = new_material("outbound")
    results = run_parallel(
        [
            lambda service, index=index: service.outbound(
                outbound_id, Decimal("4"), f"out-{index}-{suffix}", "并发出库"
            )
            for index in range(2)
        ]
    )
    assert sorted(status for status, _ in results) == ["error", "success"]

    reserve_id = new_material("reserve")
    results = run_parallel(
        [
            lambda service, index=index: service.reserve(
                reserve_id,
                project_ids[index],
                Decimal("4"),
                f"reserve-{index}-{suffix}",
                "并发预留",
            )
            for index in range(2)
        ]
    )
    assert sorted(status for status, _ in results) == ["error", "success"]

    mixed_id = new_material("mixed")
    results = run_parallel(
        [
            lambda service: service.outbound(
                mixed_id, Decimal("4"), f"mixed-out-{suffix}", "混合出库"
            ),
            lambda service: service.reserve(
                mixed_id,
                project_ids[0],
                Decimal("4"),
                f"mixed-reserve-{suffix}",
                "混合预留",
            ),
        ]
    )
    assert sorted(status for status, _ in results) == ["error", "success"]

    retry_id = new_material("retry")
    same_key = f"same-retry-{suffix}"
    results = run_parallel(
        [
            lambda service: service.outbound(retry_id, Decimal("4"), same_key, "超时后重试")
            for _ in range(2)
        ]
    )
    assert [status for status, _ in results] == ["success", "success"]
    with sessions() as db:
        assert db.get(Material, retry_id).quantity == Decimal("1")
        assert (
            db.scalar(
                select(func.count(StockMovement.id)).where(
                    StockMovement.material_id == retry_id,
                    StockMovement.operation_type == "outbound",
                )
            )
            == 1
        )
        quantities = db.scalars(
            select(Material.quantity).where(
                Material.id.in_([outbound_id, reserve_id, mixed_id, retry_id])
            )
        ).all()
        assert all(quantity >= 0 for quantity in quantities)
