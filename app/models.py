# SQLAlchemy or Tortoise models
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender", foreign_keys="Message.sender_id"
    )
    received_messages: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient", back_populates="recipient"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        "User", back_populates="sent_messages", foreign_keys=[sender_id]
    )
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient", back_populates="message", cascade="all, delete-orphan"
    )


class MessageRecipient(Base):
    __tablename__ = "message_recipients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id"), nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="recipients")
    recipient: Mapped["User"] = relationship(
        "User", back_populates="received_messages", foreign_keys=[recipient_id]
    )
