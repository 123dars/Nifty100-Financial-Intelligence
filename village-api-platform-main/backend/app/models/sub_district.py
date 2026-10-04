from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SubDistrict(Base):
    __tablename__ = "sub_districts"
    __table_args__ = (
        UniqueConstraint("code", "district_id", name="uq_subdistrict_code_district"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("districts.id"), nullable=False
    )