"""Country model – root of the location hierarchy, enables future expansion."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)

    # Relationships
    states = relationship("State", back_populates="country", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Country id={self.id} name={self.name!r}>"
