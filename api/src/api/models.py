from enum import Enum
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class DomainStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UIUser(Base):
    __tablename__ = "ui_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.user)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    proxy_user: Mapped["ProxyUser | None"] = relationship(
        back_populates="ui_user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    domains_added: Mapped[list["Domain"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="[Domain.created_by]",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("ui_users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(256), unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["UIUser"] = relationship(back_populates="refresh_tokens")


class ProxyUser(Base):
    __tablename__ = "proxy_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    ui_user_id: Mapped[int] = mapped_column(ForeignKey("ui_users.id", ondelete="CASCADE"), unique=True)
    pac_token: Mapped[str] = mapped_column(String(128), unique=True)
    proxy_user: Mapped[str] = mapped_column(String(64), unique=True)
    proxy_pass: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    ui_user: Mapped["UIUser"] = relationship(back_populates="proxy_user")


class DomainGroup(Base):
    __tablename__ = "domain_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(253), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    domains: Mapped[list["Domain"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("domain_groups.id", ondelete="CASCADE"))
    domain: Mapped[str] = mapped_column(String(253), unique=True)
    status: Mapped[DomainStatus] = mapped_column(SAEnum(DomainStatus), default=DomainStatus.pending)
    created_by: Mapped[int] = mapped_column(ForeignKey("ui_users.id"))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("ui_users.id"), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    group: Mapped["DomainGroup"] = relationship(back_populates="domains")
    created_by_user: Mapped["UIUser"] = relationship(
        foreign_keys=[created_by],
        back_populates="domains_added",
    )
