from fastapi import APIRouter

from databases.business_todo.src.api.v1 import auth, tasks, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(users.router)
