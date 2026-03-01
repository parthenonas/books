import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app import app  

client = TestClient(app)


@pytest.fixture
def mock_token_header():
    return {"Authorization": "Bearer mockToken"}

@pytest.fixture
def mock_user_dto():
    return {
        "id": 1,
        "user_name": "test_user",
        "first_name": "John",
        "last_name": "Doe",
        "status": 1
    }

@pytest.fixture
def mock_update_dto():
    return {
        "id": 1,
        "user_name": "test_user",
        "first_name": "Jane",
        "last_name": "Smith",
        "status": 1
    }


@pytest.fixture
def mock_post_dto():
    return {
        "id": 1,
        "user_id": 1,
        "content": "Test post content",
        "reply_to_id": None,
        "created_at": "2024-01-01T10:00:00",
        "likes_count": 0,
        "views_count": 0
    }


@pytest.fixture
def mock_post_create_dto():
    return {
        "content": "Test post content",
        "reply_to_id": None
    }


@pytest.fixture
def mock_posts_list(mock_post_dto):
    return [mock_post_dto]


def test_get_all_posts_success(mock_token_header, mock_posts_list, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.get_all_posts", return_value=mock_posts_list):
        response = client.get("/api/posts?limit=10&offset=0", headers=mock_token_header)
        
    assert response.status_code == 200
    assert response.json() == mock_posts_list


def test_get_all_posts_with_filters_success(mock_token_header, mock_posts_list, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.get_all_posts", return_value=mock_posts_list):
        response = client.get(
            "/api/posts?limit=5&offset=10&reply_to_id=2&owner_id=3&search=test", 
            headers=mock_token_header
        )
        
    assert response.status_code == 200
    assert response.json() == mock_posts_list


def test_get_all_posts_failure(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.get_all_posts", side_effect=Exception("Service error")):
        response = client.get("/api/posts", headers=mock_token_header)
        
    assert response.status_code == 400
    assert response.json() == {"detail": "Service error"}


def test_create_post_success(mock_token_header, mock_post_create_dto, mock_post_dto, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.create_post", return_value=mock_post_dto):
        response = client.post("/api/posts", headers=mock_token_header, json=mock_post_create_dto)
        
    assert response.status_code == 201
    assert response.json() == mock_post_dto


def test_create_post_failure(mock_token_header, mock_post_create_dto, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.create_post", side_effect=Exception("Service error")):
        response = client.post("/api/posts", headers=mock_token_header, json=mock_post_create_dto)
        
    assert response.status_code == 400
    assert response.json() == {"detail": "Service error"}


def test_create_post_validation_failure(mock_token_header, mock_user):
    invalid_dto = {"content": ""}  # пустой контент
    with patch("controllers.post_controller.get_current_user", return_value=mock_user):
        response = client.post("/api/posts", headers=mock_token_header, json=invalid_dto)
        
    assert response.status_code == 422


def test_delete_post_success(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.delete_post", return_value=None):
        response = client.delete("/api/posts/1", headers=mock_token_header)
        
    assert response.status_code == 204


def test_delete_post_invalid_id(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user):
        response = client.delete("/api/posts/abc", headers=mock_token_header)
        
    assert response.status_code == 422


def test_delete_post_not_found(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.delete_post", side_effect=Exception("Post not found")):
        response = client.delete("/api/posts/999", headers=mock_token_header)
        
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_delete_post_zero_id(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user):
        response = client.delete("/api/posts/0", headers=mock_token_header)
        
    assert response.status_code == 422


def test_view_post_success(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.view_post", return_value=None):
        response = client.post("/api/posts/1/view", headers=mock_token_header)
        
    assert response.status_code == 201


def test_view_post_invalid_id(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user):
        response = client.post("/api/posts/abc/view", headers=mock_token_header)
        
    assert response.status_code == 422


def test_view_post_not_found(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.view_post", side_effect=Exception("Post not found")):
        response = client.post("/api/posts/999/view", headers=mock_token_header)
        
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_like_post_success(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.like_post", return_value=None):
        response = client.post("/api/posts/1/like", headers=mock_token_header)
        
    assert response.status_code == 201


def test_like_post_invalid_id(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user):
        response = client.post("/api/posts/abc/like", headers=mock_token_header)
        
    assert response.status_code == 422


def test_like_post_not_found(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.like_post", side_effect=Exception("Post not found")):
        response = client.post("/api/posts/999/like", headers=mock_token_header)
        
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}


def test_dislike_post_success(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.dislike_post", return_value=None):
        response = client.delete("/api/posts/1/like", headers=mock_token_header)
        
    assert response.status_code == 204


def test_dislike_post_invalid_id(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user):
        response = client.delete("/api/posts/abc/like", headers=mock_token_header)
        
    assert response.status_code == 422


def test_dislike_post_not_found(mock_token_header, mock_user):
    with patch("controllers.post_controller.get_current_user", return_value=mock_user), \
         patch("services.post_service.dislike_post", side_effect=Exception("Post not found")):
        response = client.delete("/api/posts/999/like", headers=mock_token_header)
        
    assert response.status_code == 404
    assert response.json() == {"detail": "Post not found"}