#!/usr/bin/env python3
"""
澶氬簲鐢ㄦ灦鏋勪娇鐢ㄧず渚?
灞曠ず濡備綍鏀寔鐢ㄦ埛鍒涘缓澶氫釜agent搴旂敤
"""

import asyncio
from auth.service import AuthService
from utils.logger import logger


async def example_multi_app_usage():
    """澶氬簲鐢ㄦ灦鏋勪娇鐢ㄧず渚?""
    
    auth_service = AuthService()
    
    # 妯℃嫙鐢ㄦ埛ID
    user_id = "user_123"
    
    print("=== 澶氬簲鐢ㄦ灦鏋勭ず渚?===\n")
    
    # 1. 鐢ㄦ埛娉ㄥ唽/鐧诲綍锛堜娇鐢ㄩ粯璁ゅ簲鐢級
    print("1. 鐢ㄦ埛娉ㄥ唽/鐧诲綍")
    print(f"   榛樿搴旂敤: {auth_service.default_app_name}")
    print("   - 鐢ㄦ埛璁よ瘉鐩稿叧鐨勪細璇濆拰浜嬩欢閮藉瓨鍌ㄥ湪榛樿搴旂敤涓?)
    print("   - app_name: hephaestus")
    print("   - 鍖呭惈: 鐧诲綍浜嬩欢銆佹敞鍐屼簨浠躲€佺敤鎴风姸鎬佺瓑\n")
    
    # 2. 鐢ㄦ埛鍒涘缓绗竴涓猘gent
    print("2. 鐢ㄦ埛鍒涘缓绗竴涓猘gent")
    agent1_id = "agent_chatbot_001"
    agent1_config = {
        "name": "鏅鸿兘瀹㈡湇",
        "type": "chatbot",
        "model": "gpt-4",
        "description": "涓撲笟鐨勫鎴锋湇鍔″姪鎵?
    }
    
    session1_id = await auth_service.create_agent_session(
        user_id, agent1_id, agent1_config
    )
    print(f"   Agent ID: {agent1_id}")
    print(f"   Session ID: {session1_id}")
    print(f"   App Name: agent_{agent1_id}")
    print("   - 姣忎釜agent閮芥湁鐙珛鐨刟pp_name")
    print("   - 浼氳瘽鍜屼簨浠跺畬鍏ㄩ殧绂籠n")
    
    # 3. 鐢ㄦ埛鍒涘缓绗簩涓猘gent
    print("3. 鐢ㄦ埛鍒涘缓绗簩涓猘gent")
    agent2_id = "agent_analyzer_002"
    agent2_config = {
        "name": "鏁版嵁鍒嗘瀽甯?,
        "type": "analyzer",
        "model": "claude-3",
        "description": "涓撲笟鐨勬暟鎹垎鏋愬姪鎵?
    }
    
    session2_id = await auth_service.create_agent_session(
        user_id, agent2_id, agent2_config
    )
    print(f"   Agent ID: {agent2_id}")
    print(f"   Session ID: {session2_id}")
    print(f"   App Name: agent_{agent2_id}")
    print("   - 涓嶅悓鐨刟gent鏈変笉鍚岀殑app_name")
    print("   - 鏁版嵁瀹屽叏闅旂锛屼簰涓嶅奖鍝峔n")
    
    # 4. 鑾峰彇鐢ㄦ埛鐨勬墍鏈塧gents
    print("4. 鑾峰彇鐢ㄦ埛鐨勬墍鏈塧gents")
    agents = await auth_service.get_user_agents(user_id)
    print(f"   鐢ㄦ埛 {user_id} 鍒涘缓鐨刟gents:")
    for agent in agents:
        print(f"   - {agent['agent_id']}: {agent['config']['name']}")
        print(f"     浼氳瘽ID: {agent['session_id']}")
        print(f"     鍒涘缓鏃堕棿: {agent['created_at']}")
    
    print("\n=== 鏋舵瀯浼樺娍 ===")
    print("鉁?姣忎釜agent鐙珛鐨勫簲鐢ㄧ┖闂?)
    print("鉁?浼氳瘽鍜屼簨浠跺畬鍏ㄩ殧绂?)
    print("鉁?鏀寔鐢ㄦ埛鍒涘缓鏃犻檺涓猘gent")
    print("鉁?绗﹀悎ADK妗嗘灦鐨勮璁＄悊蹇?)
    print("鉁?渚夸簬鍚庣画鎵╁睍鍜岀鐞?)


if __name__ == "__main__":
    asyncio.run(example_multi_app_usage()) 
