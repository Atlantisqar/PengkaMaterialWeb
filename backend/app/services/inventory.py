import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models import (
    IdempotencyRecord,
    InventoryLot,
    Material,
    ProjectReservation,
    StockMovement,
    Stocktake,
)


class InventoryService:
    """The only application service allowed to mutate stock quantities."""

    def __init__(self, db: Session, user_id: int, request_id: str):
        self.db = db
        self.user_id = user_id
        self.request_id = request_id

    def _material(self, material_id: int) -> Material:
        material = self.db.scalar(
            select(Material)
            .where(Material.id == material_id, Material.is_deleted.is_(False))
            .with_for_update()
        )
        if not material:
            raise BusinessError("MATERIAL_NOT_FOUND", "物料不存在", 404)
        return material

    def _cached(self, endpoint: str, key: str) -> dict | None:
        record = self.db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == self.user_id,
                IdempotencyRecord.endpoint == endpoint,
                IdempotencyRecord.key == key,
            )
        )
        return record.response if record else None

    def _save_result(self, endpoint: str, key: str, result: dict) -> None:
        self.db.add(
            IdempotencyRecord(user_id=self.user_id, endpoint=endpoint, key=key, response=result)
        )

    def _movement(
        self,
        material: Material,
        operation_type: str,
        quantity_delta: Decimal,
        before_quantity: Decimal,
        before_reserved: Decimal,
        key: str,
        reason: str,
        notes: str = "",
        project_id: int | None = None,
        source_location_id: int | None = None,
        target_location_id: int | None = None,
        reversal_of_id: int | None = None,
    ) -> StockMovement:
        movement = StockMovement(
            movement_no=f"MV-{uuid.uuid4().hex[:18].upper()}",
            material_id=material.id,
            operation_type=operation_type,
            quantity_delta=quantity_delta,
            before_quantity=before_quantity,
            after_quantity=material.quantity,
            before_reserved=before_reserved,
            after_reserved=material.reserved_quantity,
            operator_id=self.user_id,
            project_id=project_id,
            source_location_id=source_location_id,
            target_location_id=target_location_id,
            reversal_of_id=reversal_of_id,
            reason=reason,
            notes=notes,
            request_id=self.request_id,
            idempotency_key=key,
        )
        self.db.add(movement)
        self.db.flush()
        return movement

    @staticmethod
    def _result(material: Material, movement: StockMovement, extra: dict | None = None) -> dict:
        result = {
            "movement_id": movement.id,
            "movement_no": movement.movement_no,
            "material_id": material.id,
            "quantity": str(material.quantity),
            "reserved_quantity": str(material.reserved_quantity),
            "available_quantity": str(material.available_quantity),
        }
        result.update(extra or {})
        return result

    def _execute(self, endpoint: str, key: str, callback) -> dict:
        cached = self._cached(endpoint, key)
        if cached is not None:
            return {**cached, "idempotent_replay": True}
        try:
            result = callback()
            self._save_result(endpoint, key, result)
            self.db.commit()
            return result
        except IntegrityError:
            self.db.rollback()
            cached = self._cached(endpoint, key)
            if cached is not None:
                return {**cached, "idempotent_replay": True}
            raise
        except Exception:
            self.db.rollback()
            raise

    def inbound(
        self,
        material_id: int,
        quantity: Decimal,
        key: str,
        reason: str,
        notes="",
        operation_type="inbound",
    ) -> dict:
        def action():
            material = self._material(material_id)
            before, reserved = material.quantity, material.reserved_quantity
            material.quantity += quantity
            movement = self._movement(
                material, operation_type, quantity, before, reserved, key, reason, notes
            )
            return self._result(material, movement)

        return self._execute(operation_type, key, action)

    def inbound_batch(
        self,
        entries: list[dict],
        key: str,
        reason: str,
        result: dict,
        *,
        operation_type: str = "initial",
        endpoint: str = "cable_import",
    ) -> dict:
        """Apply one atomic import while retaining one movement per material."""

        def action():
            movements = []
            for index, entry in enumerate(entries):
                quantity = Decimal(str(entry["quantity"]))
                if quantity <= 0 or quantity != quantity.to_integral_value():
                    raise BusinessError(
                        "INVALID_IMPORT_QUANTITY",
                        "批量入库数量必须是大于 0 的整数",
                    )
                material = self._material(int(entry["material_id"]))
                before, reserved = material.quantity, material.reserved_quantity
                material.quantity += quantity
                movement_key = f"{key[:88]}-{index + 1}"
                movement = self._movement(
                    material,
                    operation_type,
                    quantity,
                    before,
                    reserved,
                    movement_key,
                    reason,
                    str(entry.get("notes") or ""),
                )
                movements.append(
                    {
                        "movement_id": movement.id,
                        "movement_no": movement.movement_no,
                        "material_id": material.id,
                        "quantity_delta": int(quantity),
                        "quantity": int(material.quantity),
                    }
                )
            return {**result, "movements": movements}

        return self._execute(endpoint, key, action)

    def outbound(
        self,
        material_id: int,
        quantity: Decimal,
        key: str,
        reason: str,
        notes="",
        operation_type="outbound",
        project_id=None,
    ) -> dict:
        def action():
            material = self._material(material_id)
            if quantity > material.available_quantity:
                raise BusinessError(
                    "INSUFFICIENT_AVAILABLE_STOCK",
                    "可用库存不足",
                    details={
                        "material_id": material.id,
                        "requested": str(quantity),
                        "available": str(material.available_quantity),
                    },
                )
            before, reserved = material.quantity, material.reserved_quantity
            material.quantity -= quantity
            movement = self._movement(
                material,
                operation_type,
                -quantity,
                before,
                reserved,
                key,
                reason,
                notes,
                project_id=project_id,
            )
            return self._result(material, movement)

        return self._execute(operation_type, key, action)

    def scrap(self, material_id: int, quantity: Decimal, key: str, reason: str, notes="") -> dict:
        return self.outbound(material_id, quantity, key, reason, notes, "scrap")

    def refund(self, material_id: int, quantity: Decimal, key: str, reason: str, notes="") -> dict:
        return self.inbound(material_id, quantity, key, reason, notes, "refund")

    def reserve(
        self, material_id: int, project_id: int, quantity: Decimal, key: str, reason: str, notes=""
    ) -> dict:
        def action():
            material = self._material(material_id)
            if quantity > material.available_quantity:
                raise BusinessError("INSUFFICIENT_AVAILABLE_STOCK", "可用库存不足")
            before, reserved = material.quantity, material.reserved_quantity
            reservation = self.db.scalar(
                select(ProjectReservation)
                .where(
                    ProjectReservation.project_id == project_id,
                    ProjectReservation.material_id == material_id,
                )
                .with_for_update()
            )
            if not reservation:
                reservation = ProjectReservation(
                    project_id=project_id, material_id=material_id, quantity=0
                )
                self.db.add(reservation)
            reservation.quantity += quantity
            material.reserved_quantity += quantity
            movement = self._movement(
                material,
                "reserve",
                Decimal(0),
                before,
                reserved,
                key,
                reason,
                notes,
                project_id=project_id,
            )
            return self._result(
                material, movement, {"reservation_quantity": str(reservation.quantity)}
            )

        return self._execute("reserve", key, action)

    def cancel_reservation(
        self, material_id: int, project_id: int, quantity: Decimal, key: str, reason: str, notes=""
    ) -> dict:
        def action():
            material = self._material(material_id)
            reservation = self.db.scalar(
                select(ProjectReservation)
                .where(
                    ProjectReservation.project_id == project_id,
                    ProjectReservation.material_id == material_id,
                )
                .with_for_update()
            )
            if not reservation or quantity > reservation.quantity:
                raise BusinessError("INSUFFICIENT_PROJECT_RESERVATION", "项目预留数量不足")
            before, reserved = material.quantity, material.reserved_quantity
            reservation.quantity -= quantity
            material.reserved_quantity -= quantity
            movement = self._movement(
                material,
                "cancel_reservation",
                Decimal(0),
                before,
                reserved,
                key,
                reason,
                notes,
                project_id=project_id,
            )
            return self._result(
                material, movement, {"reservation_quantity": str(reservation.quantity)}
            )

        return self._execute("cancel_reservation", key, action)

    def reservation_to_outbound(
        self, material_id: int, project_id: int, quantity: Decimal, key: str, reason: str, notes=""
    ) -> dict:
        def action():
            material = self._material(material_id)
            reservation = self.db.scalar(
                select(ProjectReservation)
                .where(
                    ProjectReservation.project_id == project_id,
                    ProjectReservation.material_id == material_id,
                )
                .with_for_update()
            )
            if not reservation or quantity > reservation.quantity:
                raise BusinessError("INSUFFICIENT_PROJECT_RESERVATION", "项目预留数量不足")
            before, reserved = material.quantity, material.reserved_quantity
            reservation.quantity -= quantity
            reservation.consumed_quantity += quantity
            material.quantity -= quantity
            material.reserved_quantity -= quantity
            movement = self._movement(
                material,
                "reservation_to_outbound",
                -quantity,
                before,
                reserved,
                key,
                reason,
                notes,
                project_id=project_id,
            )
            return self._result(
                material, movement, {"reservation_quantity": str(reservation.quantity)}
            )

        return self._execute("reservation_to_outbound", key, action)

    def adjust(
        self, material_id: int, actual_quantity: Decimal, key: str, reason: str, notes=""
    ) -> dict:
        def action():
            material = self._material(material_id)
            if actual_quantity < material.reserved_quantity:
                raise BusinessError("ADJUSTMENT_BELOW_RESERVED", "盘点数量不能低于已预留数量")
            before, reserved = material.quantity, material.reserved_quantity
            delta = actual_quantity - before
            material.quantity = actual_quantity
            stocktake = Stocktake(
                stocktake_no=f"ST-{uuid.uuid4().hex[:14].upper()}",
                material_id=material.id,
                book_quantity=before,
                actual_quantity=actual_quantity,
                difference=delta,
                reason=reason,
                operator_id=self.user_id,
            )
            self.db.add(stocktake)
            movement = self._movement(
                material, "adjust", delta, before, reserved, key, reason, notes
            )
            return self._result(
                material,
                movement,
                {"difference": str(delta), "stocktake_no": stocktake.stocktake_no},
            )

        return self._execute("adjust", key, action)

    def transfer(
        self,
        material_id: int,
        quantity: Decimal,
        source_id: int,
        target_id: int,
        key: str,
        reason: str,
        notes="",
    ) -> dict:
        def action():
            if source_id == target_id:
                raise BusinessError("SAME_LOCATION", "来源和目标库位不能相同")
            material = self._material(material_id)
            source = self.db.scalar(
                select(InventoryLot)
                .where(
                    InventoryLot.material_id == material_id, InventoryLot.location_id == source_id
                )
                .with_for_update()
            )
            if not source or source.quantity < quantity:
                raise BusinessError("INSUFFICIENT_LOCATION_STOCK", "来源库位库存不足")
            target = self.db.scalar(
                select(InventoryLot)
                .where(
                    InventoryLot.material_id == material_id, InventoryLot.location_id == target_id
                )
                .with_for_update()
            )
            if not target:
                target = InventoryLot(material_id=material_id, location_id=target_id, quantity=0)
                self.db.add(target)
            source.quantity -= quantity
            target.quantity += quantity
            movement = self._movement(
                material,
                "transfer",
                Decimal(0),
                material.quantity,
                material.reserved_quantity,
                key,
                reason,
                notes,
                source_location_id=source_id,
                target_location_id=target_id,
            )
            return self._result(material, movement)

        return self._execute("transfer", key, action)

    def reverse(self, movement_id: int, key: str, reason: str, notes="") -> dict:
        def action():
            original = self.db.scalar(
                select(StockMovement).where(StockMovement.id == movement_id).with_for_update()
            )
            if not original:
                raise BusinessError("MOVEMENT_NOT_FOUND", "原流水不存在", 404)
            if original.operation_type in {
                "reserve",
                "cancel_reservation",
                "reservation_to_outbound",
                "transfer",
                "reverse",
            }:
                raise BusinessError(
                    "REVERSAL_REQUIRES_BUSINESS_OPERATION", "该类型流水必须通过对应业务操作纠正"
                )
            if self.db.scalar(
                select(StockMovement.id).where(StockMovement.reversal_of_id == original.id)
            ):
                raise BusinessError("ALREADY_REVERSED", "该流水已冲正")
            material = self._material(original.material_id)
            before, reserved = material.quantity, material.reserved_quantity
            new_quantity = material.quantity - original.quantity_delta
            if new_quantity < material.reserved_quantity:
                raise BusinessError("REVERSAL_VIOLATES_STOCK", "冲正会破坏库存约束")
            material.quantity = new_quantity
            movement = self._movement(
                material,
                "reverse",
                -original.quantity_delta,
                before,
                reserved,
                key,
                reason,
                notes,
                reversal_of_id=original.id,
            )
            return self._result(material, movement, {"reversal_of_id": original.id})

        return self._execute("reverse", key, action)
