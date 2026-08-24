from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.exceptions import BusinessError
from app.models import InventoryLot, Material, Project, User
from app.services.inventory import InventoryService


def svc(db, user_id):
    return InventoryService(db, user_id, "unit-request")


def test_available_quantity_formula(material, admin):
    with SessionLocal() as db:
        item = db.get(Material, material["id"])
        item.quantity = Decimal("10")
        item.reserved_quantity = Decimal("3")
        db.commit()
        assert item.available_quantity == Decimal("7")


def test_inbound_outbound_and_insufficient(material, admin):
    with SessionLocal() as db:
        service = svc(db, admin["id"])
        result = service.inbound(material["id"], Decimal("10"), "unit-inbound", "采购到货")
        assert Decimal(result["quantity"]) == 10
        result = service.outbound(material["id"], Decimal("4"), "unit-outbound", "研发领料")
        assert Decimal(result["quantity"]) == 6
        with pytest.raises(BusinessError, match="可用库存不足"):
            service.outbound(material["id"], Decimal("7"), "unit-too-much", "超额领料")


def test_idempotency(material, admin):
    with SessionLocal() as db:
        service = svc(db, admin["id"])
        first = service.inbound(material["id"], Decimal("5"), "same-key-123", "首次")
        second = service.inbound(material["id"], Decimal("5"), "same-key-123", "重试")
        assert first["movement_id"] == second["movement_id"]
        assert second["idempotent_replay"] is True
        assert db.get(Material, material["id"]).quantity == 5


def test_reservation_cancel_and_convert(material, admin):
    with SessionLocal() as db:
        user = db.get(User, admin["id"])
        project = Project(code=f"P-{material['id']}", name="测试项目", manager_id=user.id)
        db.add(project)
        db.commit()
        service = svc(db, user.id)
        service.inbound(material["id"], Decimal("10"), "reserve-stock", "初始")
        reserved = service.reserve(
            material["id"], project.id, Decimal("6"), "reserve-key", "项目备料"
        )
        assert (
            Decimal(reserved["reserved_quantity"]) == 6
            and Decimal(reserved["available_quantity"]) == 4
        )
        cancelled = service.cancel_reservation(
            material["id"], project.id, Decimal("2"), "cancel-key", "需求减少"
        )
        assert Decimal(cancelled["reserved_quantity"]) == 4
        converted = service.reservation_to_outbound(
            material["id"], project.id, Decimal("4"), "convert-key", "项目领用"
        )
        assert Decimal(converted["quantity"]) == 6 and Decimal(converted["reserved_quantity"]) == 0


def test_scrap_refund_adjust_and_reverse(material, admin):
    with SessionLocal() as db:
        service = svc(db, admin["id"])
        service.inbound(material["id"], Decimal("12"), "misc-stock", "初始")
        scrap = service.scrap(material["id"], Decimal("2"), "scrap-key", "损坏")
        assert Decimal(scrap["quantity"]) == 10
        refund = service.refund(material["id"], Decimal("3"), "refund-key", "退回")
        assert Decimal(refund["quantity"]) == 13
        adjusted = service.adjust(material["id"], Decimal("11"), "adjust-key", "实盘差异")
        assert Decimal(adjusted["difference"]) == -2
        reversed_result = service.reverse(scrap["movement_id"], "reverse-key", "误报废冲正")
        assert Decimal(reversed_result["quantity"]) == 13


def test_location_transfer(material, admin):
    from app.models import Location

    with SessionLocal() as db:
        source = Location(
            code=f"SRC-{material['id']}", name="源库位", type="bin", full_path="源库位"
        )
        target = Location(
            code=f"DST-{material['id']}", name="目标库位", type="bin", full_path="目标库位"
        )
        db.add_all([source, target])
        db.flush()
        db.add(
            InventoryLot(material_id=material["id"], location_id=source.id, quantity=Decimal("8"))
        )
        db.commit()
        result = svc(db, admin["id"]).transfer(
            material["id"], Decimal("3"), source.id, target.id, "transfer-key", "整理库位"
        )
        assert Decimal(result["quantity"]) == 0
        lots = db.scalars(
            select(InventoryLot)
            .where(InventoryLot.material_id == material["id"])
            .order_by(InventoryLot.location_id)
        ).all()
        assert sorted(x.quantity for x in lots) == [Decimal("3"), Decimal("5")]
