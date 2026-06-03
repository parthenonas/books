from fastapi import APIRouter, Depends, HTTPException, status

from databases.business_todo.src.schemas.tasks import TaskListResponse, TaskCreate, TaskResponse, TaskUpdate, \
    TaskListRequest
from databases.business_todo.src.services.task_service import TaskService
from databases.business_todo.src.utils.validators import ValidationError
from databases.business_todo.src.api.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def get_tasks(
        request: TaskListRequest = Depends(),
        current_user: dict = Depends(get_current_user)
):
    """Получить список задач с фильтрацией и пагинацией"""
    try:
        cid = int(request.customer_id) if request.customer_id and request.customer_id != "me" else (
            current_user["user_id"] if request.customer_id == "me" else None
        )
        eid = int(request.executor_id) if request.executor_id and request.executor_id != "me" else (
            current_user["user_id"] if request.executor_id == "me" else None
        )

        return TaskService.get_tasks(
            status=request.status_filter,
            priority=request.priority,
            customer_id=cid,
            executor_id=eid,
            page=request.page,
            limit=request.limit
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={e.field: e.message} if e.field else e.message)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
        request: TaskCreate,
        current_user: dict = Depends(get_current_user)
):
    """Создать новую задачу (только customer)"""
    try:
        return TaskService.create_task(
            task_text=request.task_text,
            description=request.description,
            priority=request.priority,
            deadline=request.deadline,
            current_user=current_user
        )
    except ValidationError as e:
        status_code = 403 if "permission" in e.message.lower() else 400
        raise HTTPException(status_code=status_code, detail={e.field: e.message} if e.field else e.message)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Получить задачу по ID"""
    try:
        return TaskService.get_task(task_id, current_user)
    except ValidationError as e:
        status_code = 404 if "not found" in e.message.lower() else 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
        task_id: int,
        request: TaskUpdate,
        current_user: dict = Depends(get_current_user)
):
    """Обновить задачу (владелец или admin)"""
    try:
        return TaskService.update_task(
            task_id,
            request.model_dump(exclude_unset=True),
            current_user
        )
    except ValidationError as e:
        if "not found" in e.message.lower():
            status_code = 404
        elif "permission" in e.message.lower():
            status_code = 403
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail={e.field: e.message} if e.field else e.message)


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Удалить задачу (владелец или admin)"""
    try:
        return TaskService.delete_task(task_id, current_user)
    except ValidationError as e:
        status_code = 404 if "not found" in e.message.lower() else 403
        raise HTTPException(status_code=status_code, detail=e.message)


@router.post("/{task_id}/claim", response_model=TaskResponse, summary="Взять задачу в работу")
def claim_task(
        task_id: int,
        current_user: dict = Depends(get_current_user)
):
    """
    Исполнитель берёт задачу в работу

    Требования:
    - Роль: executor
    - Статус задачи: new
    - Задача не должна быть уже назначена другому исполнителю
    """
    try:
        return TaskService.claim_task(task_id, current_user)
    except ValidationError as e:
        if "not found" in e.message.lower():
            status_code = 404
        elif "permission" in e.message.lower() or "role" in e.message.lower():
            status_code = 403
        elif "already" in e.message.lower() or "assigned" in e.message.lower():
            status_code = 409  # Conflict
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=e.message)
