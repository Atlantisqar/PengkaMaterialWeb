from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(100), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped[Role] = relationship()


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship()


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(64), unique=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Location(Base, TimestampMixin):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(32), default="bin")
    full_path: Mapped[str] = mapped_column(String(500))
    manager: Mapped[str] = mapped_column(String(100), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organizer_style: Mapped[str | None] = mapped_column(String(32))
    organizer_left_module: Mapped[str | None] = mapped_column(String(16))
    organizer_right_module: Mapped[str | None] = mapped_column(String(16))
    bin_material_name: Mapped[str] = mapped_column(String(200), default="")
    bin_quantity: Mapped[int | None] = mapped_column()
    bin_content_notes: Mapped[str] = mapped_column(Text, default="")


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    contact: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    lead_time_days: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Material(Base, TimestampMixin):
    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_material_quantity_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_material_reserved_nonnegative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_material_reserved_lte_quantity"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"))
    mpn: Mapped[str] = mapped_column(String(200), default="", index=True)
    specification: Mapped[str] = mapped_column(String(300), default="")
    package: Mapped[str] = mapped_column(String(100), default="")
    footprint: Mapped[str] = mapped_column(String(100), default="")
    manufacturer: Mapped[str] = mapped_column(String(200), default="")
    supplier_part_number: Mapped[str] = mapped_column(String(200), default="")
    unit: Mapped[str] = mapped_column(String(20), default="pcs")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    target_stock: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    barcode: Mapped[str] = mapped_column(String(200), default="")
    lifecycle_status: Mapped[str] = mapped_column(String(32), default="active")
    rohs_status: Mapped[str] = mapped_column(String(32), default="unknown")
    datasheet_url: Mapped[str] = mapped_column(String(500), default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    category: Mapped[Category | None] = relationship()
    location: Mapped[Location | None] = relationship()
    supplier: Mapped[Supplier | None] = relationship()

    @property
    def available_quantity(self) -> Decimal:
        return self.quantity - self.reserved_quantity


class InventoryLot(Base, TimestampMixin):
    __tablename__ = "inventory_lots"
    __table_args__ = (
        UniqueConstraint("material_id", "location_id", name="uq_lot_material_location"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default="planning")
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text, default="")
    members: Mapped[list[int]] = mapped_column(JSON, default=list)


class BomItem(Base, TimestampMixin):
    __tablename__ = "bom_items"
    __table_args__ = (UniqueConstraint("project_id", "version", "material_id", name="uq_bom_item"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    version: Mapped[str] = mapped_column(String(32), default="V1")
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    notes: Mapped[str] = mapped_column(Text, default="")


class ProjectReservation(Base, TimestampMixin):
    __tablename__ = "project_reservations"
    __table_args__ = (
        UniqueConstraint("project_id", "material_id", name="uq_project_material_reservation"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    consumed_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))


class Loan(Base, TimestampMixin):
    __tablename__ = "loans"
    id: Mapped[int] = mapped_column(primary_key=True)
    loan_no: Mapped[str] = mapped_column(String(64), unique=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    borrower_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    returned_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="borrowed")
    notes: Mapped[str] = mapped_column(Text, default="")


class Stocktake(Base, TimestampMixin):
    __tablename__ = "stocktakes"
    id: Mapped[int] = mapped_column(primary_key=True)
    stocktake_no: Mapped[str] = mapped_column(String(64), unique=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    book_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    difference: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    reason: Mapped[str] = mapped_column(Text)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(primary_key=True)
    movement_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"), index=True)
    operation_type: Mapped[str] = mapped_column(String(40), index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    before_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    after_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    before_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    after_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    loan_id: Mapped[int | None] = mapped_column(ForeignKey("loans.id"))
    source_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    target_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    reversal_of_id: Mapped[int | None] = mapped_column(ForeignKey("stock_movements.id"))
    reason: Mapped[str] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, default="")
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("user_id", "endpoint", "key", name="uq_idempotency_scope"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    endpoint: Mapped[str] = mapped_column(String(100))
    key: Mapped[str] = mapped_column(String(100))
    response: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(String(64), default="")
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str] = mapped_column(String(64), default="")
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    expected_date: Mapped[date | None] = mapped_column(Date)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
