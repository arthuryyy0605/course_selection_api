from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer

from course_selection_api.lib.auth_library.permission import depend_auth, Auth
from course_selection_api.lib.response import ExceptionResponse, SingleResponse, to_json_response
from course_selection_api.schema.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    MeResponse,
    UserListResponse, UpdateUserStatusRequest, UpdateUserStatusResponse
)
from course_selection_api.data_access_object.db import get_db_connection
from course_selection_api.business_model.auth_business import AuthBusiness

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, conn=Depends(get_db_connection)):
    """Register a new consumer account"""
    result = await AuthBusiness.register_user(conn, request)
    return to_json_response(SingleResponse(result=result))


@router.post("/login", response_model=SingleResponse[LoginResponse])
async def login(request: LoginRequest, conn=Depends(get_db_connection)):
    """Login a user and return JWT token"""
    result = await AuthBusiness.login_user(conn, request)
    return to_json_response(SingleResponse(result=result))


@router.get("/me", responses={404: {'model': ExceptionResponse}}, response_model=SingleResponse[MeResponse])
async def get_current_user_info(
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Get information about the currently logged-in user"""
    result = await AuthBusiness.get_current_user_info(conn, auth)
    return to_json_response(SingleResponse(result=result))


# Admin-only endpoints for user management
@router.get("/admin/users", response_model=SingleResponse[UserListResponse])
async def get_all_users(
        limit: int = 100,
        offset: int = 0,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Get all users (admin only)"""
    result = await AuthBusiness.get_all_users(conn, auth, limit, offset)
    return to_json_response(SingleResponse(result=result))


@router.put("/admin/users/{user_id}/status", response_model=SingleResponse[UpdateUserStatusResponse])
async def update_user_status(
        user_id: str,
        request: UpdateUserStatusRequest,
        auth: Auth = depend_auth(),
        conn=Depends(get_db_connection)
):
    """Enable or disable a user account (admin only)"""
    result = await AuthBusiness.update_user_enabled_status(conn, auth, user_id, request.enabled)
    return to_json_response(SingleResponse(result=result))
