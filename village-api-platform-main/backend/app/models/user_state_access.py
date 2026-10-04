"""Tracks which states a user is allowed to query."""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserStateAccess(Base):
    __tablename__ = "user_state_access"
    __table_args__ = (
        UniqueConstraint("user_id", "state_id", name="uq_user_state_access"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("states.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    user = relationship("User", backref="state_access_list")
    state = relationship("State")
