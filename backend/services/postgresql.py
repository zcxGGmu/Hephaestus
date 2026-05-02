"""
AgentPress PostgreSQL Database Connection Manager
"""

from typing import Optional, List, Dict, Any, Union
import asyncpg # type: ignore
from utils.logger import logger
from utils.config import config
import threading
import os
import json

class DBConnection:
    """绾跨▼瀹夊叏鐨勫崟渚嬫暟鎹簱杩炴帴绠＄悊鍣紝浣跨敤PostgreSQL"""
    
    _instance: Optional['DBConnection'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # 鍙岄噸妫€鏌ラ攣瀹氭ā寮忥紝纭繚绾跨▼瀹夊叏
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._pool = None
        return cls._instance

    def __init__(self):
        """鍒濆鍖栨柟娉曪紝涓嶅湪杩欓噷杩涜瀹為檯鍒濆鍖?""
        pass

    async def initialize(self):
        """鍒濆鍖栨暟鎹簱杩炴帴姹?""
        if self._initialized:
            return
                
        try:
            # 浠庣幆澧冨彉閲忔垨閰嶇疆鏂囦欢鑾峰彇鏁版嵁搴揢RL
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                if hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
                    database_url = config.DATABASE_URL
                else:
                    # 寮€鍙戠幆澧冪殑榛樿杩炴帴瀛楃涓?
                    database_url = "postgresql://postgres:password@localhost:5432/hephaestus"
            
            if not database_url:
                logger.error("Missing PostgreSQL DATABASE_URL environment variable")
                raise RuntimeError("PostgreSQL DATABASE_URL environment variable must be set.")

            logger.debug("Initializing PostgreSQL connection pool")
            
            # 鍒涘缓PostgreSQL杩炴帴姹?
            self._pool = await asyncpg.create_pool(
                database_url,
                min_size=1, # 鏈€灏忚繛鎺ユ暟
                max_size=10, # 鏈€澶ц繛鎺ユ暟
                command_timeout=60 # 鍛戒护瓒呮椂鏃堕棿
            )
            
            self._initialized = True
            logger.debug(f"PostgreSQL connection pool initialized")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection pool initialization error: {e}")
            raise RuntimeError(f"PostgreSQL connection pool initialization failed: {str(e)}")

    @property
    async def client(self):
        """浠庤繛鎺ユ睜鑾峰彇鏁版嵁搴撳鎴风"""
        if not self._initialized:
            await self.initialize()
        return PostgreSQLClient(self._pool)

    @classmethod
    async def disconnect(cls):
        """鏂紑鏁版嵁搴撹繛鎺?""
        if cls._instance and cls._instance._pool:
            await cls._instance._pool.close()
            cls._instance._pool = None
            cls._instance._initialized = False
            logger.info("PostgreSQL鏁版嵁搴撹繛鎺ユ睜宸插叧闂?)

class PostgreSQLClient:
    """PostgreSQL瀹㈡埛绔寘瑁呭櫒锛屾彁渚涙搷浣滄暟鎹簱鐨勬帴鍙?""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    def table(self, table_name: str):
        """鍒涘缓琛ㄦ煡璇㈡瀯寤哄櫒"""
        return PostgreSQLTable(self.pool, table_name)
    
    def schema(self, schema_name: str):
        """鍒涘缓妯″紡鏌ヨ鏋勫缓鍣紙鐢ㄤ簬Supabase schema鍏煎锛?""
        return PostgreSQLSchema(self.pool, schema_name)

class PostgreSQLSchema:
    """妯″紡鏌ヨ鏋勫缓鍣紝鐢ㄤ簬鏀寔schema鍔熻兘"""
    
    def __init__(self, pool: asyncpg.Pool, schema_name: str):
        self.pool = pool
        self.schema_name = schema_name
    
    def table(self, table_name: str):
        """鍦ㄦ寚瀹氭ā寮忎腑鍒涘缓琛ㄦ煡璇㈡瀯寤哄櫒"""
        full_table_name = f"{self.schema_name}.{table_name}"
        return PostgreSQLTable(self.pool, full_table_name)

class PostgreSQLTable:
    """PostgreSQL琛ㄦ煡璇㈡瀯寤哄櫒锛屾彁渚涙搷浣滄暟鎹簱鐨勬帴鍙?""
    
    def __init__(self, pool: asyncpg.Pool, table_name: str):
        self.pool = pool
        self.table_name = table_name
        self._select_fields = "*"
        self._where_conditions = []
        self._order_by = []
        self._limit_value = None
        self._offset_value = None
        self._count_flag = False
        self._params = []
        self._single_result = False
        self._maybe_single = False
    
    def select(self, fields: str = "*", count: str = None):
        """閫夋嫨鐗瑰畾瀛楁"""
        self._select_fields = fields
        if count == "exact":
            self._count_flag = True
        return self
    
    def eq(self, column: str, value: Any):
        """娣诲姞鐩哥瓑鏉′欢"""
        self._where_conditions.append(f"{column} = ${len(self._params) + 1}")
        self._params.append(value)
        return self
    
    def neq(self, column: str, value: Any):
        """娣诲姞涓嶇瓑鏉′欢锛堟敮鎸?neq()鏂规硶锛?""
        if value is None:
            self._where_conditions.append(f"{column} IS NOT NULL")
        else:
            self._where_conditions.append(f"{column} != ${len(self._params) + 1}")
            self._params.append(value)
        return self
    
    def lt(self, column: str, value: Any):
        """娣诲姞灏忎簬鏉′欢"""
        self._where_conditions.append(f"{column} < ${len(self._params) + 1}")
        self._params.append(value)
        return self
    
    def gt(self, column: str, value: Any):
        """娣诲姞澶т簬鏉′欢"""
        self._where_conditions.append(f"{column} > ${len(self._params) + 1}")
        self._params.append(value)
        return self
    
    def gte(self, column: str, value: Any):
        """娣诲姞澶т簬绛変簬鏉′欢"""
        self._where_conditions.append(f"{column} >= ${len(self._params) + 1}")
        self._params.append(value)
        return self
    
    def lte(self, column: str, value: Any):
        """娣诲姞灏忎簬绛変簬鏉′欢"""
        self._where_conditions.append(f"{column} <= ${len(self._params) + 1}")
        self._params.append(value)
        return self
    
    def like(self, column: str, pattern: str):
        """娣诲姞LIKE鏉′欢"""
        self._where_conditions.append(f"{column} LIKE ${len(self._params) + 1}")
        self._params.append(pattern)
        return self
    
    def ilike(self, column: str, pattern: str):
        """娣诲姞澶у皬鍐欎笉鏁忔劅鐨凩IKE鏉′欢"""
        self._where_conditions.append(f"{column} ILIKE ${len(self._params) + 1}")
        self._params.append(pattern)
        return self
    
    def contains(self, column: str, value: Any):
        """娣诲姞鍖呭惈鏉′欢锛堢敤浜庢暟缁勬垨JSON瀛楁锛?""
        if isinstance(value, list):
            # 瀵逛簬鏁扮粍瀛楁锛屼娇鐢?@> 鎿嶄綔绗?
            self._where_conditions.append(f"{column} @> ${len(self._params) + 1}")
            self._params.append(json.dumps(value))
        else:
            # 瀵逛簬鏂囨湰鎼滅储锛屼娇鐢?LIKE
            self._where_conditions.append(f"{column} LIKE ${len(self._params) + 1}")
            self._params.append(f"%{value}%")
        return self
    
    def in_(self, column: str, values: List[Any]):
        """娣诲姞IN鏉′欢"""
        if not values:
            # 濡傛灉鍒楄〃涓虹┖锛屾坊鍔犱竴涓案杩滀负鍋囩殑鏉′欢
            self._where_conditions.append("1 = 0")
            return self
        
        placeholders = []
        for value in values:
            self._params.append(value)
            placeholders.append(f"${len(self._params)}")
        
        self._where_conditions.append(f"{column} IN ({', '.join(placeholders)})")
        return self
    
    def is_(self, column: str, value: Any):
        """娣诲姞IS鏉′欢锛堢敤浜嶯ULL妫€鏌ワ級"""
        if value is None:
            self._where_conditions.append(f"{column} IS NULL")
        else:
            self._where_conditions.append(f"{column} IS ${len(self._params) + 1}")
            self._params.append(value)
        return self
    
    @property
    def not_(self):
        """杩斿洖NOT鏌ヨ鏋勫缓鍣?""
        return PostgreSQLNotBuilder(self)
    
    def filter(self, field_expression: str, operator: str, value: Any):
        """娣诲姞杩囨护鏉′欢锛堟敮鎸丼upabase鐨刦ilter璇硶锛?""
        if operator == 'eq':
            return self.eq(field_expression, value)
        elif operator == 'neq':
            return self.neq(field_expression, value)
        elif operator == 'lt':
            return self.lt(field_expression, value)
        elif operator == 'gt':
            return self.gt(field_expression, value)
        # 瀵逛簬澶嶆潅鐨凧SON瀛楁鏌ヨ锛屽 'sandbox->>id'
        elif '->>' in field_expression:
            self._where_conditions.append(f"{field_expression} = ${len(self._params) + 1}")
            self._params.append(value)
        else:
            logger.warning(f"涓嶆敮鎸佺殑杩囨护鎿嶄綔绗? {operator}")
        return self
    
    def or_(self, condition: str):
        """娣诲姞OR鏉′欢锛堢畝鍖栧疄鐜帮級"""
        # 澶勭悊鍩烘湰鐨刬like鎼滅储
        if "ilike" in condition:
            # 瑙ｆ瀽鏉′欢濡?"name.ilike.%search%,description.ilike.%search%"
            parts = condition.split(",")
            or_conditions = []
            for part in parts:
                if ".ilike." in part:
                    field, _, pattern = part.split(".", 2)
                    or_conditions.append(f"{field} ILIKE ${len(self._params) + 1}")
                    self._params.append(pattern)
            
            if or_conditions:
                self._where_conditions.append(f"({' OR '.join(or_conditions)})")
        return self
    
    def order(self, column: str, desc: bool = False):
        """娣诲姞鎺掑簭瀛愬彞"""
        direction = "DESC" if desc else "ASC"
        self._order_by.append(f"{column} {direction}")
        return self
    
    def range(self, start: int, end: int):
        """娣诲姞鍒嗛〉锛圠IMIT鍜孫FFSET锛?""
        self._limit_value = end - start + 1
        self._offset_value = start
        return self
    
    def limit(self, count: int):
        """娣诲姞LIMIT瀛愬彞"""
        self._limit_value = count
        return self
    
    def single(self):
        """鏍囪鏌ヨ搴旇繑鍥炲崟涓粨鏋?""
        self._single_result = True
        self._limit_value = 1
        return self
    
    def maybe_single(self):
        """鏍囪鏌ヨ鍙兘杩斿洖鍗曚釜缁撴灉鎴杗ull"""
        self._maybe_single = True
        self._limit_value = 1
        return self
    
    async def execute(self):
        """鎵ц鏌ヨ"""
        # 鏋勫缓SELECT鏌ヨ
        query_parts = [f"SELECT {self._select_fields}"]
        
        # 濡傛灉闇€瑕佽鏁帮紝鏋勫缓璁℃暟鏌ヨ
        count_query = None
        if self._count_flag:
            count_query = f"SELECT COUNT(*) FROM {self.table_name}"
            if self._where_conditions:
                count_query += f" WHERE {' AND '.join(self._where_conditions)}"
        
        query_parts.append(f"FROM {self.table_name}")
        
        # 娣诲姞WHERE瀛愬彞
        if self._where_conditions:
            query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
        
        # 娣诲姞ORDER BY
        if self._order_by:
            query_parts.append(f"ORDER BY {', '.join(self._order_by)}")
        
        # 娣诲姞LIMIT鍜孫FFSET
        if self._limit_value:
            query_parts.append(f"LIMIT {self._limit_value}")
        if self._offset_value:
            query_parts.append(f"OFFSET {self._offset_value}")
        
        query = " ".join(query_parts)
        
        try:
            async with self.pool.acquire() as conn:
                # 鎵ц涓绘煡璇?
                rows = await conn.fetch(query, *self._params)
                data = [dict(row) for row in rows]
                
                # 濡傛灉闇€瑕佽鏁帮紝鎵ц璁℃暟鏌ヨ
                count = None
                if self._count_flag:
                    count_result = await conn.fetchval(count_query, *self._params)
                    count = int(count_result) if count_result else 0
                
                # 澶勭悊single鍜宮aybe_single鎯呭喌
                if self._single_result:
                    if not data:
                        raise ValueError("鏌ヨ鏈繑鍥炰换浣曠粨鏋?)
                    return QueryResult(data[0], count)
                elif self._maybe_single:
                    if not data:
                        return QueryResult(None, count)
                    return QueryResult(data[0], count)
                
                # 杩斿洖Supabase椋庢牸鐨勭粨鏋?
                return QueryResult(data, count)
                
        except Exception as e:
            logger.error(f"鏌ヨ鎵ц澶辫触: {e}, SQL: {query}, 鍙傛暟: {self._params}")
            raise RuntimeError(f"鏁版嵁搴撴煡璇㈠け璐? {str(e)}")
    
    async def insert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]):
        """鎻掑叆鏁版嵁鍒拌〃涓?""
        try:
            # 澶勭悊鍗曟潯璁板綍鍜屽鏉¤褰?
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                return QueryResult([])
            
            # 鑾峰彇鎵€鏈夊瓧娈靛悕
            columns = list(data[0].keys())
            
            # 鏋勫缓鎻掑叆鏌ヨ
            values_placeholders = []
            all_values = []
            
            for i, record in enumerate(data):
                record_placeholders = []
                for j, column in enumerate(columns):
                    placeholder_index = i * len(columns) + j + 1
                    record_placeholders.append(f"${placeholder_index}")
                    all_values.append(record[column])
                values_placeholders.append(f"({', '.join(record_placeholders)})")
            
            query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES {', '.join(values_placeholders)}
            RETURNING *
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *all_values)
                result_data = [dict(row) for row in rows]
                return QueryResult(result_data)
                
        except Exception as e:
            logger.error(f"鎻掑叆鎿嶄綔澶辫触: {e}")
            raise RuntimeError(f"鏁版嵁搴撴彃鍏ュけ璐? {str(e)}")
    
    async def update(self, data: Dict[str, Any]):
        """鏇存柊琛ㄤ腑鐨勬暟鎹?""
        try:
            # 鏋勫缓SET瀛愬彞
            set_clauses = []
            values = []
            for key, value in data.items():
                set_clauses.append(f"{key} = ${len(values) + len(self._params) + 1}")
                values.append(value)
            
            query_parts = [f"UPDATE {self.table_name}"]
            query_parts.append(f"SET {', '.join(set_clauses)}")
            
            if self._where_conditions:
                query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
            
            query_parts.append("RETURNING *")
            query = " ".join(query_parts)
            
            # 璋冭瘯淇℃伅
            logger.debug(f"UPDATE query: {query}")
            logger.debug(f"Parameters: {self._params + values}")
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *(self._params + values))
                result_data = [dict(row) for row in rows]
                
                # 澶勭悊鍗曚釜缁撴灉鐨勬儏鍐?
                if self._single_result or self._maybe_single:
                    if not result_data and self._single_result:
                        raise ValueError("鏇存柊鎿嶄綔鏈奖鍝嶄换浣曡褰?)
                    return QueryResult(result_data[0] if result_data else None)
                
                return QueryResult(result_data)
                
        except Exception as e:
            logger.error(f"鏇存柊鎿嶄綔澶辫触: {e}")
            logger.error(f"Query: {query if 'query' in locals() else 'N/A'}")
            logger.error(f"Parameters: {self._params + values if 'values' in locals() else 'N/A'}")
            raise RuntimeError(f"鏁版嵁搴撴洿鏂板け璐? {str(e)}")
    
    async def delete(self):
        """浠庤〃涓垹闄ゆ暟鎹?""
        try:
            query_parts = [f"DELETE FROM {self.table_name}"]
            
            if self._where_conditions:
                query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
            
            query_parts.append("RETURNING *")
            query = " ".join(query_parts)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *self._params)
                result_data = [dict(row) for row in rows]
                return QueryResult(result_data)
                
        except Exception as e:
            logger.error(f"鍒犻櫎鎿嶄綔澶辫触: {e}")
            raise RuntimeError(f"鏁版嵁搴撳垹闄ゅけ璐? {str(e)}")

class PostgreSQLNotBuilder:
    """NOT鏌ヨ鏋勫缓鍣紝鐢ㄤ簬鏀寔.not_.is_()绛夎娉?""
    
    def __init__(self, table_builder: PostgreSQLTable):
        self.table_builder = table_builder
    
    def is_(self, column: str, value: Any):
        """娣诲姞IS NOT鏉′欢"""
        if value is None:
            self.table_builder._where_conditions.append(f"{column} IS NOT NULL")
        else:
            self.table_builder._where_conditions.append(f"{column} IS NOT ${len(self.table_builder._params) + 1}")
            self.table_builder._params.append(value)
        return self.table_builder

class QueryResult:
    """鏌ヨ缁撴灉鍖呰鍣紝鍖归厤Supabase鎺ュ彛"""
    
    def __init__(self, data: Union[List[Dict[str, Any]], Dict[str, Any], None], count: Optional[int] = None):
        self.data = data
        self.count = count

