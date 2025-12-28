from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey, JSON
from datetime import datetime


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    # すべて複数
    categories: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )  # ["dress", "outer"]

    colors: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )  # ["white", "black"]

    seasons: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )  # ["spring", "autumn"]

    size: Mapped[str] = mapped_column(String)
    material: Mapped[str] = mapped_column(String)

    image_path: Mapped[str] = mapped_column(String)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
