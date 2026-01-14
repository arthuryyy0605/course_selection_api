import asyncio
from fastapi import APIRouter, status
from course_selection_api.lib.auth_library.simple_token import SimpleTokenAuth
from course_selection_api.lib.response import SingleResponse, to_json_response
from course_selection_api.lib.base_exception import UnauthorizedException
from course_selection_api.lib.logger import get_prefix_logger_adapter
from course_selection_api.schema.auth import TokenVerifyRequest, TokenVerifyResponse

router = APIRouter(prefix="/token", tags=["token"])
logger = get_prefix_logger_adapter(__name__)


@router.post("/verify", response_model=SingleResponse[TokenVerifyResponse], summary="驗證 Token")
async def verify_token(request: TokenVerifyRequest):
    """
    驗證 token 是否正確
    
    用於前端確認用戶登入狀態
    """
    # 輸入驗證
    if not request.user_id or not request.token:
        logger.warning(f"Token verification failed: missing user_id or token")
        return to_json_response(SingleResponse(result=TokenVerifyResponse(valid=False)))
    
    try:
        # 使用 asyncio.to_thread 將同步函數轉為異步執行，避免阻塞
        # 設置超時為 5 秒，確保不會無限等待
        result = await asyncio.wait_for(
            asyncio.to_thread(SimpleTokenAuth.verify_token, request.token, request.user_id),
            timeout=5.0
        )
        logger.info(f"Token verification successful for user_id: {request.user_id}")
        return to_json_response(SingleResponse(result=TokenVerifyResponse(valid=True)))
    except asyncio.TimeoutError:
        logger.error(f"Token verification timeout for user_id: {request.user_id}")
        return to_json_response(SingleResponse(result=TokenVerifyResponse(valid=False)))
    except UnauthorizedException as e:
        logger.warning(f"Token verification failed for user_id: {request.user_id}, reason: {e.message}")
        return to_json_response(SingleResponse(result=TokenVerifyResponse(valid=False)))
    except Exception as e:
        logger.error(f"Unexpected error during token verification for user_id: {request.user_id}, error: {str(e)}", exc_info=True)
        return to_json_response(SingleResponse(result=TokenVerifyResponse(valid=False)))

