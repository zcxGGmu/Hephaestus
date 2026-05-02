async def _log_adk_user_message_event(client, user_id: str, message_content: str, session_id: str, message_id: str, app_name: str = "hephaestus"):
    """璁板綍鐢ㄦ埛娑堟伅浜嬩欢鍒癆DK events琛?""
    try:
        import uuid
        import pickle
        from datetime import datetime
        event_id = str(uuid.uuid4())
        invocation_id = str(uuid.uuid4())
        
        # 鎸夌収ADK鏍煎紡鏋勫缓娑堟伅鍐呭 - 搴旇绗﹀悎 types.Content 缁撴瀯
        content = {
            "role": "user", 
            "parts": [{"text": message_content}],  # ADK鏈熸湜鐨勬牸寮?
            "message_id": message_id
        }
        
        # actions 闇€瑕佹墜鍔ㄥ簭鍒楀寲涓哄瓧鑺傦紙杩欐槸ADK鐨勬牸寮忚姹傦級
        actions_dict = {
            "skip_summarization": None,
            "state_delta": {},
            "artifact_delta": {},
            "transfer_to_agent": None,
            "escalate": None,
            "requested_auth_configs": {}
        }
        
        # 鎵嬪姩搴忓垪鍖?actions 瀛楀吀涓哄瓧鑺傦紙杩欐槸ADK鐨勬牸寮忚姹傦級
        actions_bytes = pickle.dumps(actions_dict)
        
        # 鎻掑叆鍒癆DK events琛?
        async with client.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (
                    id, app_name, user_id, session_id, invocation_id, 
                    author, timestamp, content, actions
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                event_id, app_name, user_id, session_id, invocation_id,
                "user", datetime.now(), json.dumps(content), actions_bytes  
            )
        
        logger.info(f"User message event recorded successfully: {event_id}")
        return event_id
        
    except Exception as e:
        logger.error(f"Record user message event failed: {e}")
        raise
