import os
import oracledb
import asyncio
import re
from functools import lru_cache
from typing import Any, List, Optional
from course_selection_api.config import get_settings
setting = get_settings()

# 全局連接池
_pool = None


def get_connection_pool():
    """獲取或創建連接池（單例模式）"""
    global _pool
    if _pool is None:
        dsn = get_database_dsn()
        try:
            _pool = oracledb.create_pool(
                user=setting.db_user,
                password=setting.db_password,
                dsn=dsn,
                min=5,                          # 最小連接數（增加以應對並發）
                max=20,                         # 最大連接數（增加以支持批量操作）
                increment=2,                    # 連接增量（加快擴展速度）
                getmode=oracledb.POOL_GETMODE_WAIT,
                wait_timeout=60000,             # 等待超時 60 秒（增加超時時間）
                timeout=600,                    # 連接空閒超時 10 分鐘
                ping_interval=60                # 每 60 秒 ping 一次保持連接
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Database connection pool created successfully (min=2, max=10)")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create connection pool: {e}")
            raise
    return _pool


class Database:
    """Database utility class for executing queries (Oracle)"""
    
    @staticmethod
    def _convert_lob_to_string(value: Any) -> Any:
        """Convert Oracle LOB objects to strings for JSON serialization"""
        if isinstance(value, oracledb.LOB):
            return value.read()
        return value
    
    @staticmethod
    def _convert_row_to_dict(row: tuple, columns: List[str]) -> dict:
        """Convert a database row to a dictionary, handling LOB objects"""
        return {col: Database._convert_lob_to_string(val) for col, val in zip(columns, row)}
    
    @staticmethod
    def _convert_postgres_to_oracle(query: str) -> str:
        """Convert PostgreSQL parameter syntax ($1, $2) to Oracle syntax (:1, :2)"""
        # 替換 $1, $2, ... 為 :1, :2, ...
        def replace_param(match):
            num = match.group(1)
            return f":{num}"
        return re.sub(r'\$(\d+)', replace_param, query)
    
    @staticmethod
    def _convert_returning_clause(query: str) -> tuple[str, bool]:
        """Convert PostgreSQL RETURNING clause to Oracle format"""
        # Oracle 不支持 RETURNING 在 INSERT/UPDATE 中直接返回，需要分兩步
        # 這裡先標記，實際處理在 DAO 層
        has_returning = 'RETURNING' in query.upper()
        if has_returning:
            # 移除 RETURNING 子句，稍後在 DAO 層手動查詢
            query = re.sub(r'\s+RETURNING\s+.*', '', query, flags=re.IGNORECASE)
        return query, has_returning
    
    @staticmethod
    async def fetch(conn: oracledb.Connection, query: str, *args) -> List[Any]:
        """Execute a query and return all results"""
        cursor = conn.cursor()
        try:
            oracle_query = Database._convert_postgres_to_oracle(query)
            # 執行查詢（使用線程池執行同步操作）
            await asyncio.to_thread(cursor.execute, oracle_query, args if args else None)
            rows = await asyncio.to_thread(cursor.fetchall)
            # 轉換為字典列表，將欄位名稱轉為小寫（Oracle 返回大寫）
            columns = [desc[0].lower() for desc in cursor.description] if cursor.description else []
            return [Database._convert_row_to_dict(row, columns) for row in rows]
        finally:
            cursor.close()
    
    @staticmethod
    async def fetchrow(conn: oracledb.Connection, query: str, *args) -> Optional[Any]:
        """Execute a query and return one result"""
        cursor = conn.cursor()
        try:
            oracle_query = Database._convert_postgres_to_oracle(query)
            # 執行查詢
            await asyncio.to_thread(cursor.execute, oracle_query, args if args else None)
            row = await asyncio.to_thread(cursor.fetchone)
            if row:
                # 將欄位名稱轉為小寫（Oracle 返回大寫）
                columns = [desc[0].lower() for desc in cursor.description] if cursor.description else []
                return Database._convert_row_to_dict(row, columns)
            return None
        finally:
            cursor.close()
    
    @staticmethod
    async def execute(conn: oracledb.Connection, query: str, *args) -> str:
        """Execute a query and return execution status"""
        cursor = conn.cursor()
        try:
            oracle_query, _ = Database._convert_returning_clause(query)
            oracle_query = Database._convert_postgres_to_oracle(oracle_query)
            # 執行查詢
            await asyncio.to_thread(cursor.execute, oracle_query, args if args else None)
            await asyncio.to_thread(conn.commit)
            return "OK"
        finally:
            cursor.close()

    @staticmethod
    async def fetchval(conn: oracledb.Connection, query: str, *args) -> Any:
        """Execute a query and return a single value"""
        cursor = conn.cursor()
        try:
            oracle_query = Database._convert_postgres_to_oracle(query)
            # 執行查詢
            await asyncio.to_thread(cursor.execute, oracle_query, args if args else None)
            row = await asyncio.to_thread(cursor.fetchone)
            value = row[0] if row else None
            return Database._convert_lob_to_string(value) if value is not None else None
        finally:
            cursor.close()
    
    @staticmethod
    async def get_nextval(conn: oracledb.Connection, sequence_name: str) -> int:
        """Get next value from a sequence"""
        cursor = conn.cursor()
        try:
            query = f"SELECT {sequence_name}.NEXTVAL FROM DUAL"
            await asyncio.to_thread(cursor.execute, query)
            row = await asyncio.to_thread(cursor.fetchone)
            return row[0] if row else None
        finally:
            cursor.close()


@lru_cache()
def get_database_dsn() -> str:
    """Get database DSN from environment variables"""
    host = setting.db_host
    port = setting.db_port
    service_name = setting.db_name
    
    return f"{host}:{port}/{service_name}"


async def get_db_connection():
    """FastAPI dependency to get database connection from pool"""
    pool = get_connection_pool()
    conn = None
    try:
        # 從連接池獲取連接（使用線程池執行同步操作）
        conn = await asyncio.to_thread(pool.acquire)
        yield conn
    except Exception as e:
        # 記錄連接錯誤
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database connection error: {e}")
        logger.error(f"DSN: {get_database_dsn()}, User: {setting.db_user}")
        raise
    finally:
        # 釋放連接回連接池（不是關閉連接）
        if conn:
            try:
                await asyncio.to_thread(pool.release, conn)
            except Exception as e:
                # 記錄釋放錯誤但不拋出異常
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error releasing database connection: {e}")
