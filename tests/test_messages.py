import pytest
import pytest_asyncio


class TestMessaging:

    @pytest.mark.asyncio
    async def test_send_message(self, client):
        sender_data = {"email": "sender@example.com", "name": "Sender User"}
        sender_response = await client.post("/api/v1/users", json=sender_data)
        assert sender_response.status_code == 201
        sender = sender_response.json()
        
        recipient_data = {"email": "recipient@example.com", "name": "Recipient User"}
        recipient_response = await client.post("/api/v1/users", json=recipient_data)
        assert recipient_response.status_code == 201
        recipient = recipient_response.json()
        
        # Send a message
        message_data = {
            "subject": "Test Message",
            "content": "This is a test message content.",
            "recipient_ids": [recipient["id"]]
        }
        response = await client.post(
            f"/api/v1/messages?sender_id={sender['id']}",
            json=message_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == message_data["subject"]
        assert data["content"] == message_data["content"]
        assert data["sender_id"] == sender["id"]
        assert "id" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_sent_messages(self, client):

        sender_data = {"email": "sender2@example.com", "name": "Sender User 2"}
        sender_response = await client.post("/api/v1/users", json=sender_data)
        assert sender_response.status_code == 201
        sender = sender_response.json()
        
        recipient_data = {"email": "recipient2@example.com", "name": "Recipient User 2"}
        recipient_response = await client.post("/api/v1/users", json=recipient_data)
        assert recipient_response.status_code == 201
        recipient = recipient_response.json()
        
        for i in range(2):
            message_data = {
                "subject": f"Sent Message {i}",
                "content": f"Content of sent message {i}",
                "recipient_ids": [recipient["id"]]
            }
            response = await client.post(
                f"/api/v1/messages?sender_id={sender['id']}",
                json=message_data
            )
            assert response.status_code == 201
        
        response = await client.get(f"/api/v1/messages/{sender['id']}/sent-messages")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["messages"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_inbox_messages(self, client):

        sender_data = {"email": "sender3@example.com", "name": "Sender User 3"}
        sender_response = await client.post("/api/v1/users", json=sender_data)
        assert sender_response.status_code == 201
        sender = sender_response.json()
        
        recipient_data = {"email": "recipient3@example.com", "name": "Recipient User 3"}
        recipient_response = await client.post("/api/v1/users", json=recipient_data)
        assert recipient_response.status_code == 201
        recipient = recipient_response.json()
        
        for i in range(2):
            message_data = {
                "subject": f"Inbox Message {i}",
                "content": f"Content of inbox message {i}",
                "recipient_ids": [recipient["id"]]
            }
            response = await client.post(
                f"/api/v1/messages?sender_id={sender['id']}",
                json=message_data
            )
            assert response.status_code == 201
        
        response = await client.get(f"/api/v1/messages/{recipient['id']}/inbox-messages")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["messages"]) == 2
        
        for msg in data["messages"]:
            assert msg["read"] == False
            assert msg["read_at"] is None


class TestReadStatus:

    @pytest.mark.asyncio
    async def test_mark_message_as_read(self, client):
        sender_data = {"email": "sender4@example.com", "name": "Sender User 4"}
        sender_response = await client.post("/api/v1/users", json=sender_data)
        assert sender_response.status_code == 201
        sender = sender_response.json()
        
        recipient_data = {"email": "recipient4@example.com", "name": "Recipient User 4"}
        recipient_response = await client.post("/api/v1/users", json=recipient_data)
        assert recipient_response.status_code == 201
        recipient = recipient_response.json()
        
        # Send a message
        message_data = {
            "subject": "Read Test Message",
            "content": "This message will be marked as read.",
            "recipient_ids": [recipient["id"]]
        }
        response = await client.post(
            f"/api/v1/messages?sender_id={sender['id']}",
            json=message_data
        )
        assert response.status_code == 201
        message = response.json()
        
        # Mark message as read
        response = await client.patch(
            f"/api/v1/messages/{message['id']}/users/{recipient['id']}/read"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message_id"] == message["id"]
        assert data["recipient_id"] == recipient["id"]
        assert data["read"] == True
        assert "read_at" in data
    
    @pytest.mark.asyncio
    async def test_get_unread_messages(self, client):

        sender_data = {"email": "sender5@example.com", "name": "Sender User 5"}
        sender_response = await client.post("/api/v1/users", json=sender_data)
        assert sender_response.status_code == 201
        sender = sender_response.json()
        
        recipient_data = {"email": "recipient5@example.com", "name": "Recipient User 5"}
        recipient_response = await client.post("/api/v1/users", json=recipient_data)
        assert recipient_response.status_code == 201
        recipient = recipient_response.json()
        
        # Send multiple messages
        sent_messages = []
        for i in range(3):
            message_data = {
                "subject": f"Unread Message {i}",
                "content": f"Content of unread message {i}",
                "recipient_ids": [recipient["id"]]
            }
            response = await client.post(
                f"/api/v1/messages?sender_id={sender['id']}",
                json=message_data
            )
            assert response.status_code == 201
            sent_messages.append(response.json())
        
        # Mark one message as read
        response = await client.patch(
            f"/api/v1/messages/{sent_messages[0]['id']}/users/{recipient['id']}/read"
        )
        assert response.status_code == 200
        
        # Get unread messages
        response = await client.get(f"/api/v1/messages/{recipient['id']}/unread-messages")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2  # Only 2 unread messages remain
        assert len(data["messages"]) == 2
        
        # Verify all returned messages are unread
        for msg in data["messages"]:
            assert msg["read"] == False
            assert msg["read_at"] is None
