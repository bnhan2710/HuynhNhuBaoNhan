# Pydantic models
from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserList(BaseModel):
    users: List[UserResponse]
    total: int

# Message Schemas
class MessageBase(BaseModel):
    subject: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)

class MessageCreate(MessageBase):
    recipient_ids: List[UUID] = Field(..., min_items=1)

class MessageRecipientInfo(BaseModel):
    id: UUID
    recipient_id: UUID
    read: bool
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MessageResponse(MessageBase):
    id: UUID
    sender_id: UUID
    timestamp: datetime
    recipients: Optional[List[MessageRecipientInfo]] = None
    
    class Config:
        from_attributes = True

class MessageList(BaseModel):
    messages: List[MessageResponse]
    total: int
    
class MessageRecipientSchema(BaseModel):
    id: UUID
    message_id: UUID
    subject: Optional[str]
    content: str
    sender_id: UUID
    timestamp: datetime
    read: bool
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MessagesRecipientList(BaseModel):
    messages: List[MessageRecipientSchema]
    total: int

class MarkAsReadResponse(BaseModel):
    message_id: UUID
    recipient_id: UUID
    read: bool
    read_at: datetime
    
    class Config:
        from_attributes = True

