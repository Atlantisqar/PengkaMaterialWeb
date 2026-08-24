import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select

from app.api.deps import DB, CurrentUser, require
from app.core.exceptions import BusinessError
from app.models import BomItem, Project, PurchaseOrder
from app.schemas.domain import BomData, ProjectData, PurchaseOrderData
from app.services.audit import add_audit

router = APIRouter(tags=["项目与采购"])


def serialize(obj, fields):
    return {k: getattr(obj, k) for k in fields}


PROJECT_FIELDS = [
    "id",
    "code",
    "name",
    "manager_id",
    "status",
    "start_date",
    "end_date",
    "notes",
    "members",
    "created_at",
    "updated_at",
]


@router.get("/projects")
def projects(db: DB, user: CurrentUser):
    return [
        serialize(x, PROJECT_FIELDS)
        for x in db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    ]


@router.post("/projects", status_code=201, dependencies=[Depends(require("project:manage"))])
def create_project(p: ProjectData, request: Request, db: DB, user: CurrentUser):
    if db.scalar(select(Project.id).where(Project.code == p.code)):
        raise BusinessError("PROJECT_CODE_EXISTS", "项目编号已存在", 409)
    item = Project(**p.model_dump())
    db.add(item)
    db.flush()
    add_audit(db, user.id, "project.create", "project", str(item.id), request.state.request_id)
    db.commit()
    return serialize(item, PROJECT_FIELDS)


@router.get("/projects/{item_id}")
def get_project(item_id: int, db: DB, user: CurrentUser):
    item = db.get(Project, item_id)
    if not item:
        raise BusinessError("PROJECT_NOT_FOUND", "项目不存在", 404)
    data = serialize(item, PROJECT_FIELDS)
    data["bom"] = [
        serialize(x, ["id", "version", "material_id", "required_quantity", "notes"])
        for x in db.scalars(select(BomItem).where(BomItem.project_id == item_id)).all()
    ]
    return data


@router.put("/projects/{item_id}", dependencies=[Depends(require("project:manage"))])
def update_project(item_id: int, p: ProjectData, request: Request, db: DB, user: CurrentUser):
    item = db.get(Project, item_id)
    if not item:
        raise BusinessError("PROJECT_NOT_FOUND", "项目不存在", 404)
    for k, v in p.model_dump().items():
        setattr(item, k, v)
    add_audit(db, user.id, "project.update", "project", str(item.id), request.state.request_id)
    db.commit()
    return serialize(item, PROJECT_FIELDS)


@router.post(
    "/projects/{item_id}/bom", status_code=201, dependencies=[Depends(require("project:manage"))]
)
def add_bom(item_id: int, p: BomData, db: DB, user: CurrentUser):
    if not db.get(Project, item_id):
        raise BusinessError("PROJECT_NOT_FOUND", "项目不存在", 404)
    item = BomItem(project_id=item_id, **p.model_dump())
    db.add(item)
    db.commit()
    return serialize(
        item, ["id", "project_id", "version", "material_id", "required_quantity", "notes"]
    )


@router.get("/purchase-orders", dependencies=[Depends(require("purchase:manage"))])
def purchase_orders(db: DB, user: CurrentUser):
    fields = [
        "id",
        "order_no",
        "supplier_id",
        "status",
        "items",
        "total_amount",
        "expected_date",
        "created_by_id",
        "created_at",
    ]
    return [
        serialize(x, fields)
        for x in db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())).all()
    ]


@router.post(
    "/purchase-orders", status_code=201, dependencies=[Depends(require("purchase:manage"))]
)
def create_purchase_order(p: PurchaseOrderData, db: DB, user: CurrentUser):
    total = sum(float(x.get("quantity", 0)) * float(x.get("unit_price", 0)) for x in p.items)
    item = PurchaseOrder(
        order_no=f"PO-{uuid.uuid4().hex[:14].upper()}",
        supplier_id=p.supplier_id,
        items=p.items,
        total_amount=total,
        expected_date=p.expected_date,
        created_by_id=user.id,
    )
    db.add(item)
    db.commit()
    return serialize(item, ["id", "order_no", "status", "total_amount"])
