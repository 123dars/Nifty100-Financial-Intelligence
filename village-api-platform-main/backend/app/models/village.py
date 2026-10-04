from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Village(Base):
    __tablename__ = "villages"
    __table_args__ = (
        UniqueConstraint("code", "sub_district_id", name="uq_village_code_subdistrict"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sub_district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sub_districts.id"), nullable=False
    )