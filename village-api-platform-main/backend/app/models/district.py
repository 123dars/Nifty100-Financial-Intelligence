from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (
        UniqueConstraint("code", "state_id", name="uq_district_code_state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("states.id"), nullable=False
    )