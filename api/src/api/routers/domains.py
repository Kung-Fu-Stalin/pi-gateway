import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.auth import get_current_user, require_admin
from api.database import get_db
from api.models import UIUser, DomainGroup, Domain, DomainStatus
from api.services.squid import write_domains, reload_squid


router = APIRouter(prefix="/api/groups", tags=["domains"])

DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


class GroupCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if not DOMAIN_RE.match(v):
            raise ValueError("Invalid domain name")
        return v


class DomainCreate(BaseModel):
    domain: str

    @field_validator("domain")
    @classmethod
    def domain_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if not DOMAIN_RE.match(v):
            raise ValueError("Invalid domain name")
        return v


class RejectRequest(BaseModel):
    reason: str | None = None


async def get_approved_domains(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Domain).where(Domain.status == DomainStatus.approved)
    )
    return [d.domain for d in result.scalars().all()]


async def sync_squid(db: AsyncSession) -> None:
    domains = await get_approved_domains(db)
    write_domains(domains)
    reload_squid()


# ВАЖНО: /pending и /domains/* должны быть ДО /{group_id}
@router.get("/pending")
async def list_pending(
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(require_admin),
):
    result = await db.execute(
        select(Domain).where(Domain.status == DomainStatus.pending)
    )
    domains = result.scalars().all()
    return [
        {
            "id": d.id,
            "domain": d.domain,
            "group_id": d.group_id,
            "created_by": d.created_by,
            "created_at": d.created_at,
        }
        for d in domains
    ]


@router.post("/domains/{domain_id}/approve")
async def approve_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(require_admin),
):
    domain = await db.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    if domain.status == DomainStatus.approved:
        return {"ok": True}

    domain.status = DomainStatus.approved
    domain.reviewed_by = user.id
    domain.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await sync_squid(db)
    return {"ok": True}


@router.post("/domains/{domain_id}/reject")
async def reject_domain(
    domain_id: int,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(require_admin),
):
    domain = await db.get(Domain, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    was_approved = domain.status == DomainStatus.approved
    domain.status = DomainStatus.rejected
    domain.reviewed_by = user.id
    domain.reviewed_at = datetime.now(timezone.utc)
    domain.reject_reason = body.reason
    await db.commit()

    # Если был approved — нужно убрать из domains.txt
    if was_approved:
        await sync_squid(db)

    return {"ok": True}


@router.get("")
async def list_groups(
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(get_current_user),
):
    result = await db.execute(
        select(DomainGroup).options(selectinload(DomainGroup.domains))
    )
    groups = result.scalars().all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "created_at": g.created_at,
            "domains": [
                {
                    "id": d.id,
                    "domain": d.domain,
                    "status": d.status,
                    "created_by": d.created_by,
                    "reject_reason": d.reject_reason,
                    "created_at": d.created_at,
                }
                for d in g.domains
            ],
        }
        for g in groups
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreate,
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(get_current_user),
):
    existing = await db.execute(select(DomainGroup).where(DomainGroup.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group already exists")

    group = DomainGroup(name=body.name)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return {"id": group.id, "name": group.name}


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(require_admin),
):
    group = await db.get(DomainGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()
    await sync_squid(db)


@router.post("/{group_id}/domains", status_code=status.HTTP_201_CREATED)
async def add_domain(
    group_id: int,
    body: DomainCreate,
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(get_current_user),
):
    group = await db.get(DomainGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = await db.execute(select(Domain).where(Domain.domain == body.domain))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain already exists")

    domain = Domain(
        group_id=group_id,
        domain=body.domain,
        status=DomainStatus.pending,
        created_by=user.id,
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)
    return {"id": domain.id, "domain": domain.domain, "status": domain.status}


@router.delete("/{group_id}/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    group_id: int,
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(get_current_user),
):
    domain = await db.get(Domain, domain_id)
    if not domain or domain.group_id != group_id:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Обычный пользователь может удалять только свои домены
    if user.role != "admin" and domain.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    await db.delete(domain)
    await db.commit()
    await sync_squid(db)