"""
簡單的 Token 認證模組
使用 user_id + 'nchu' + 年月日 進行 MD5 加密
"""
import hashlib
from datetime import datetime
from course_selection_api.lib.base_exception import UnauthorizedException


class SimpleTokenAuth:
    """簡單的 Token 認證類，用於 create/update 操作"""
    
    # MD5 salt
    SALT = "nchu"
    
    @staticmethod
    def generate_token(user_id: str) -> str:
        """
        生成 token
        使用 MD5(user_id + 'nchu' + 年月日) 生成 token
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            MD5 hash 字符串
        """
        # 取得當前日期（格式：YYYYMMDD）
        current_date = datetime.now().strftime('%Y%m%d')
        # 使用 user_id + nchu + 年月日 進行 MD5 加密
        content = f"{user_id}{SimpleTokenAuth.SALT}{current_date}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def verify_token(token: str, user_id: str) -> bool:
        """
        驗證 token 是否有效
        
        Args:
            token: MD5 token 字符串
            user_id: 要驗證的用戶 ID
            
        Returns:
            是否驗證成功
            
        Raises:
            UnauthorizedException: Token 無效或驗證失敗
        """
        try:
            # 生成預期的 token
            expected_token = SimpleTokenAuth.generate_token(user_id)
            
            # 比對 token
            if token != expected_token:
                raise UnauthorizedException(message="Token 驗證失敗")
            
            return True
            
        except UnauthorizedException:
            raise
        except Exception as e:
            raise UnauthorizedException(message=f"Token 驗證失敗: {str(e)}")


def verify_simple_token(user_id: str, token: str) -> bool:
    """
    便捷函數：驗證 simple token
    
    Args:
        user_id: 用戶 ID
        token: MD5 token 字符串
        
    Returns:
        是否驗證成功
    """
    return SimpleTokenAuth.verify_token(token, user_id)

