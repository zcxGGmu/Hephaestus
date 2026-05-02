#!/usr/bin/env python3
"""
娴嬭瘯鏂扮殑 ADK 澶勭悊鍣ㄦ灦鏋?
"""

import asyncio
import sys
import os

# 娣诲姞椤圭洰鏍圭洰褰曞埌 Python 璺緞
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm import make_adk_api_call

async def test_adk_processor():
    """娴嬭瘯鏂扮殑 ADK 澶勭悊鍣ㄦ灦鏋?""
    print("馃И 寮€濮嬫祴璇曟柊鐨?ADK 澶勭悊鍣ㄦ灦鏋?..")
    
    # 鍑嗗娴嬭瘯娑堟伅
    test_messages = [
        {
            'role': 'user',
            'content': '浣犲ソ锛岃绠€鍗曚粙缁嶄竴涓嬩綘鑷繁',
            'app_name': 'hephaestus',
            'user_id': 'test_user_123',
            'session_id': 'test_session_456'
        }
    ]
    
    try:
        print("馃摗 璋冪敤 make_adk_api_call...")
        
        # 璋冪敤 ADK API
        response = await make_adk_api_call(
            messages=test_messages,
            model_name="openai/gpt-4o",
            stream=True,
            system_prompt="浣犳槸涓€涓弸濂界殑AI鍔╂墜锛岃鐢ㄤ腑鏂囧洖绛斻€?
        )
        
        print("鉁?鎴愬姛鑾峰彇 ADK 鍝嶅簲娴?)
        print("馃摑 寮€濮嬪鐞?ADK 浜嬩欢:")
        
        # 澶勭悊 ADK 浜嬩欢娴?
        event_count = 0
        async for event in response:
            event_count += 1
            print(f"馃攳 [ADK EVENT DEBUG] 鏀跺埌绗?{event_count} 涓?ADK 浜嬩欢: {type(event)}")
            print(f"馃攳 [ADK EVENT DEBUG] 浜嬩欢鍐呭: {event}")
            
            # 妫€鏌ヤ簨浠舵槸鍚︽湁鍐呭
            if hasattr(event, 'content') and event.content:
                print(f"馃攳 [ADK EVENT DEBUG] 浜嬩欢鏈夊唴瀹? {event.content}")
                if hasattr(event.content, 'parts') and event.content.parts:
                    for i, part in enumerate(event.content.parts):
                        if hasattr(part, 'text') and part.text:
                            print(f"馃攳 [ADK EVENT DEBUG] 绗?{i} 涓儴鍒嗙殑鏂囨湰: {part.text}")
        
        print(f"鉁?ADK 浜嬩欢澶勭悊瀹屾垚锛屽叡鏀跺埌 {event_count} 涓簨浠?)
        
    except Exception as e:
        print(f"鉂?ADK 澶勭悊鍣ㄦ祴璇曞け璐? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_adk_processor()) 
