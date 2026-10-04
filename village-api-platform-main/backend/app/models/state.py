from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    country_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("countries.id"), nullable=True
    )

    # Relationships
    country = relationship("Country", back_populates="states", lazy="selectin")
