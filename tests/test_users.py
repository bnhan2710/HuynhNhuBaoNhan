import pytest
import pytest_asyncio
from uuid import uuid4


class TestUserManagement:

    @pytest.mark.asyncio
    async def test_create_user(self, client):
        """Test creating a user successfully."""
        user_data = {
            "email": "test@example.com",
            "name": "Test User"
        }
        response = await client.post("/api/v1/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["name"] == user_data["name"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client):
        user_data = {"email": "getuser@example.com", "name": "Get User"}
        create_response = await client.post("/api/v1/users", json=user_data)
        assert create_response.status_code == 201
        created_user = create_response.json()
        
        # Then get the user by ID
        user_id = created_user["id"]
        response = await client.get(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == created_user["email"]
        assert data["name"] == created_user["name"]
    
    @pytest.mark.asyncio
    async def test_list_users(self, client):
        users_data = [
            {"email": "user1@example.com", "name": "User One"},
            {"email": "user2@example.com", "name": "User Two"},
            {"email": "user3@example.com", "name": "User Three"}
        ]
        
        for user_data in users_data:
            response = await client.post("/api/v1/users", json=user_data)
            assert response.status_code == 201

        response = await client.get("/api/v1/users")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3
        assert len(data["users"]) == 3
