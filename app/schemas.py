# Pydantic models
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime


class UserList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    users: List[UserResponse]
    total: int


# Message Schemas
class MessageBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    subject: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    
    recipient_ids: List[UUID] = Field(..., min_items=1)


class MessageRecipientInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    recipient_id: UUID
    read: bool
    read_at: Optional[datetime] = None


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    sender_id: UUID
    timestamp: datetime
    recipients: Optional[List[MessageRecipientInfo]] = None


class MessageList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    messages: List[MessageResponse]
    total: int


class MessageRecipientSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    message_id: UUID
    subject: Optional[str]
    content: str
    sender_id: UUID
    timestamp: datetime
    read: bool
    read_at: Optional[datetime] = None


class MessagesRecipientList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    messages: List[MessageRecipientSchema]
    total: int


class MarkAsReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    message_id: UUID
    recipient_id: UUID
    read: bool
    read_at: datetime