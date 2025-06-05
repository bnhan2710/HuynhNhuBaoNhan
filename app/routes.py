# FastAPI routes
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .db import get_db
from .models import User, Message, MessageRecipient
from .schemas import (
    UserCreate, UserResponse, UserList,
    MessageCreate, MessageResponse, MessageRecipientSchema, MessagesRecipientList, MessageList,
    MarkAsReadResponse
)

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):

    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):

    user = await db.execute(select(User).where(User.id == user_id))
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.get("/users", response_model=UserList)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):

    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar_one()
    
    users_result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = users_result.scalars().all()
    
    return UserList(users=users, total=total)




# Message APIs
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    sender_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    sender_result = await db.execute(select(User).where(User.id == sender_id))
    sender = sender_result.scalar_one_or_none()
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender not found"
        )
    
    recipients_result = await db.execute(
        select(User).where(User.id.in_(message_data.recipient_ids))
    )
    recipients = recipients_result.scalars().all()
    
    if len(recipients) != len(message_data.recipient_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more recipients not found"
        )

    message = Message(
        sender_id=sender_id,
        subject=message_data.subject,
        content=message_data.content
    )
    db.add(message)
    await db.flush() 
    
    message_recipients = []
    for recipient in recipients:
        msg_recipient = MessageRecipient(
            message_id=message.id,
            recipient_id=recipient.id
        )
        db.add(msg_recipient)
        message_recipients.append(msg_recipient)
    
    await db.commit()
    await db.refresh(message)
    
    recipient_info = []
    for i, recipient in enumerate(recipients):
        recipient_info.append({
            "id": message_recipients[i].id,
            "recipient_id": recipient.id,
            "read": False,
            "read_at": None
        })
    
    return MessageResponse(
        id=message.id,
        subject=message.subject,
        content=message.content,
        sender_id=sender.id,
        timestamp=message.timestamp,
        recipients=recipient_info
    )

@router.get("/messages/{sender_id}/sent-messages", response_model=MessageList)
async def get_sent_messages(
    sender_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    
    user_result = await db.execute(select(User).where(User.id == sender_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    total_result = await db.execute(
        select(func.count(Message.id)).where(Message.sender_id == sender_id)
    )
    total = total_result.scalar_one()

    messages_query = (
        select(Message)
        .options(selectinload(Message.recipients).selectinload(MessageRecipient.recipient))
        .where(Message.sender_id == sender_id)
        .order_by(Message.timestamp.desc())
    )

    result = await db.execute(messages_query)
    messages_data = result.scalars().all()
    
    messages = []
    for message in messages_data:
        recipient_info = []
        for recipient_rel in message.recipients:
            recipient_info.append({
                "id": recipient_rel.id,
                "recipient_id": recipient_rel.recipient_id,
                "read": recipient_rel.read,
                "read_at": recipient_rel.read_at
            })

        messages.append(MessageResponse(
            id=message.id,
            subject=message.subject,
            content=message.content,
            sender_id=message.sender_id,
            timestamp=message.timestamp,
            recipients=recipient_info
        ))
    
    return MessageList(messages=messages, total=total)

@router.get("/messages/{recipient_id}/inbox-messages", response_model=MessagesRecipientList)
async def get_inbox_messages(
    recipient_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    user_result = await db.execute(select(User).where(User.id == recipient_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    messages_query = (
        select(MessageRecipient)
        .options(selectinload(MessageRecipient.message).selectinload(Message.sender))
        .where(MessageRecipient.recipient_id == recipient_id)
        .join(Message, MessageRecipient.message_id == Message.id)
        .order_by(Message.timestamp.desc())
    )
    
    result = await db.execute(messages_query)
    message_recipients = result.scalars().all()
    
    messages = []
    for msg_recipient in message_recipients:
        message = msg_recipient.message  
        messages.append(MessageRecipientSchema(
            id=msg_recipient.id,
            message_id=message.id,
            subject=message.subject,
            content=message.content,
            sender_id=message.sender_id,
            timestamp=message.timestamp,
            read=msg_recipient.read,
            read_at=msg_recipient.read_at
        ))
    
    return MessagesRecipientList(messages=messages, total=len(messages))

@router.get("/messages/{user_id}/unread-messages", response_model=MessagesRecipientList)
async def get_unread_messages(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    messages_query = (
        select(MessageRecipient)
        .options(selectinload(MessageRecipient.message).selectinload(Message.sender))
        .where(
            MessageRecipient.recipient_id == user_id,
            MessageRecipient.read == False
        )
        .join(Message, MessageRecipient.message_id == Message.id)
        .order_by(Message.timestamp.desc())
    )
    result = await db.execute(messages_query)
    message_recipients = result.scalars().all()
    messages = []
    for msg_recipient in message_recipients:
        message = msg_recipient.message  
        messages.append(MessageRecipientSchema(
            id=msg_recipient.id,
            message_id=message.id,
            subject=message.subject,
            content=message.content,
            sender_id=message.sender_id,
            timestamp=message.timestamp,
            read=msg_recipient.read,
            read_at=msg_recipient.read_at
        ))
    return MessagesRecipientList(messages=messages, total=len(messages))

@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message_with_recipients(message_id: UUID, db: AsyncSession = Depends(get_db)):
    message_result = await db.execute(
        select(Message, User.name.label("sender_name"), User.email.label("sender_email"))
        .join(User, Message.sender_id == User.id)
        .where(Message.id == message_id)
    )
    message_data = message_result.first()
    
    if not message_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    message = message_data.Message
    
    recipients_result = await db.execute(
        select(MessageRecipient)
        .join(User, MessageRecipient.recipient_id == User.id)
        .where(MessageRecipient.message_id == message_id)
        .order_by(User.name)
    )
    recipients_data = recipients_result.all()
    
    recipient_info = []
    for row in recipients_data:
        msg_recipient = row.MessageRecipient
        recipient_info.append({
            "id": msg_recipient.id,
            "recipient_id": msg_recipient.recipient_id,
            "read": msg_recipient.read,
            "read_at": msg_recipient.read_at
        })
    
    return MessageResponse(
        id=message.id,
        subject=message.subject,
        content=message.content,
        sender_id=message.sender_id,
        sender_name=message_data.sender_name,
        sender_email=message_data.sender_email,
        timestamp=message.timestamp,
        recipients=recipient_info
    )

@router.patch("/messages/{message_id}/users/{user_id}/read", response_model=MarkAsReadResponse)
async def mark_message_as_read(
    user_id: UUID,
    message_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    
    msg_recipient_result = await db.execute(
        select(MessageRecipient)
        .where(
            MessageRecipient.message_id == message_id,
            MessageRecipient.recipient_id == user_id
        )
    )
    msg_recipient = msg_recipient_result.scalar_one_or_none()
    
    if not msg_recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    if msg_recipient.read:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is already marked as read"
        )
    
    read_time = datetime.now()
    await db.execute(
        update(MessageRecipient)
        .where(MessageRecipient.id == msg_recipient.id)
        .values(read=True, read_at=read_time)
    )
    await db.commit()
    
    return MarkAsReadResponse(
        message_id=message_id,
        recipient_id=user_id,
        read=True,
        read_at=read_time
    )
