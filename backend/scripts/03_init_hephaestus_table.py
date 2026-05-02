#!/usr/bin/env python3
"""
鎵цhephaestus.sql杩佺Щ鏂囦欢鐨勮剼鏈?
鍒涘缓鎵€鏈変笟鍔¤〃锛氱敤鎴疯璇併€侀」鐩鐞嗐€佷唬鐞嗙郴缁熴€丄DK妗嗘灦
"""

import asyncio
import sys
import os
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.postgresql import DBConnection
from utils.logger import logger


async def execute_hephaestus_migration():
    """鎵цhephaestus.sql杩佺Щ"""
    db = None
    try:
        logger.info("寮€濮嬫墽琛宖ufanmanus.sql杩佺Щ...")
        
        # 鍒濆鍖栨暟鎹簱杩炴帴
        db = DBConnection()
        await db.initialize()
        client = await db.client
        
        # 璇诲彇杩佺Щ鏂囦欢
        migration_file = project_root / "migrations" / "hephaestus.sql"
        if not migration_file.exists():
            logger.error(f"杩佺Щ鏂囦欢涓嶅瓨鍦? {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.info(f"璇诲彇杩佺Щ鏂囦欢: {migration_file}")
        
        # 鎵ц杩佺Щ
        async with client.pool.acquire() as conn:
            await conn.execute(migration_sql)
        
        logger.info("hephaestus.sql杩佺Щ瀹屾垚锛?)
        
        # 楠岃瘉琛ㄦ槸鍚﹀垱寤烘垚鍔?
        async with client.pool.acquire() as conn:
            tables = await conn.fetch(
                """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
                """
            )
        
        logger.info(f"鏁版嵁搴撲腑鍏辨湁 {len(tables)} 涓〃:")
        for table in tables:
            logger.info(f"  - {table['tablename']}")
        
        # 楠岃瘉鍏抽敭琛ㄦ槸鍚﹀瓨鍦?
        expected_tables = [
            'users', 'agents', 'projects', 'messages', 'threads',
            'sessions', 'events', 'app_states', 'user_states'
        ]
        
        existing_table_names = [table['tablename'] for table in tables]
        missing_tables = [table for table in expected_tables if table not in existing_table_names]
        
        if missing_tables:
            logger.warning(f"浠ヤ笅鍏抽敭琛ㄦ湭鎵惧埌: {missing_tables}")
        else:
            logger.info("鎵€鏈夊叧閿〃閮藉凡鍒涘缓鎴愬姛锛?)
        
        return True
        
    except Exception as e:
        logger.error(f"hephaestus.sql杩佺Щ澶辫触: {e}")
        return False
    finally:
        if db:
            await DBConnection.disconnect()


def main():
    """涓诲嚱鏁?""
    print("Hephaestus 鏁版嵁搴撹〃杩佺Щ宸ュ叿")
    print("=" * 50)
    
    success = asyncio.run(execute_hephaestus_migration())
    if success:
        print("\n鏁版嵁搴撹〃鍒涘缓鎴愬姛锛?)
        print("\n宸插垱寤虹殑16涓牳蹇冭〃锛?)
        print("鐢ㄦ埛璁よ瘉: users, oauth_providers, user_sessions, refresh_tokens, user_activities")
        print("椤圭洰绠＄悊: projects, threads, messages")
        print("浠ｇ悊绯荤粺: agents, agent_versions, agent_workflows, agent_runs")
        print("ADK妗嗘灦: app_states, sessions, events, user_states")
        print("\n馃殌 鐜板湪鍙互鍚姩鏈嶅姟浜? python -m uvicorn api:app --reload")
    else:
        print("\n鏁版嵁搴撹〃鍒涘缓澶辫触锛?)
        print("璇锋鏌ワ細")
        print("1. 鏁版嵁搴撹繛鎺ユ槸鍚︽甯?)
        print("2. .env 鏂囦欢涓殑 DATABASE_URL 鏄惁姝ｇ‘")
        print("3. migrations/hephaestus.sql 鏂囦欢鏄惁瀛樺湪")
        sys.exit(1)


if __name__ == "__main__":
    main() 
