"""
User Authentication Service
"""

import json
from datetime import datetime
from typing import Optional
from fastapi import HTTPException # type: ignore
from services.postgresql import DBConnection
from utils.auth_utils import AuthUtils
from utils.logger import logger
from .models import (
    LoginRequest, RegisterRequest, RefreshRequest,
    AuthResponse, RefreshResponse, UserResponse, User
)

class AuthService:
    """User Authentication Service"""
    
    def __init__(self):
        self.db = DBConnection()
        self.auth = AuthUtils()
        self.default_app_name = "hephaestus"  # 榛樿搴旂敤鍚嶇О
    
    async def _get_client(self):
        """鑾峰彇鏁版嵁搴撳鎴风"""
        await self.db.initialize()
        return await self.db.client
    
    def _user_to_model(self, user_data: dict) -> User:
        """杞崲鏁版嵁搴撶敤鎴锋暟鎹负妯″瀷"""
        return User(
            id=str(user_data['id']),  # 纭繚UUID杞崲涓哄瓧绗︿覆
            email=user_data['email'],
            name=user_data['name'],
            created_at=user_data['created_at']
        )
    
    async def register(self, request: RegisterRequest) -> AuthResponse:
        """User Registration"""
        logger.info(f"Starting registration for: {request.email}")
        
        client = await self._get_client()
        
        # 妫€鏌ョ敤鎴锋槸鍚﹀凡瀛樺湪
        async with client.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1", 
                request.email
            )
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # 鍒涘缓鏂扮敤鎴?
        hashed_password = self.auth.hash_password(request.password)
        
        async with client.pool.acquire() as conn:
            user_record = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, name, provider, status, created_at) 
                VALUES ($1, $2, $3, $4, $5, $6) 
                RETURNING *
                """,
                request.email, hashed_password, request.name, 'local', 'active', datetime.now()
            )
        
        user = dict(user_record)
        
        # 鐢熸垚璁块棶浠ょ墝鍜屽埛鏂颁护鐗?
        access_token = self.auth.create_access_token(str(user['id']))
        refresh_token = self.auth.create_refresh_token()
        
        # 瀛樺偍鍒锋柊浠ょ墝
        await self._store_refresh_token(str(user['id']), refresh_token)
        
        # 鏇存柊鐢ㄦ埛鐘舵€?
        await self._update_user_state(client, str(user['id']), {
            'last_login': datetime.now().isoformat(),
            'login_count': 1,
            'email_verified': False
        })
        
        # 浣跨敤榛樿搴旂敤鍚嶇О
        app_name = self.default_app_name
        
        # 鍒涘缓娉ㄥ唽浼氳瘽锛堟敞鍐屾椂鍏堝垱寤轰細璇濓紝鍐嶈褰曚簨浠讹紝鐢ㄦ潵閫傞厤ADK妗嗘灦涓棤娉曚娇鐢╯ession_id瀛楁鐨勬儏鍐碉級
        await self._create_adk_session(client, str(user['id']), {
            'registration_time': datetime.now().isoformat(),
            'registration_method': 'email_password',
            'status': 'active'
        }, app_name)
        
        # 娉ㄥ唽鏃跺垱寤篎uFanManus Agent
        from agent.hephaestus.repository import HephaestusAgentRepository
        repository = HephaestusAgentRepository()
        await repository.create_hephaestus_agent(str(user['id']))
        
        logger.info(f"User registered: {request.email}")
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=24 * 3600,  # 24灏忔椂
            user=self._user_to_model(user)
        )
    
    async def login(self, request: LoginRequest) -> AuthResponse:
        """User login"""
        client = await self._get_client()
        
        # 鏌ユ壘鐢ㄦ埛锛堝寘鍚獳DK鐘舵€佸瓧娈碉級
        async with client.pool.acquire() as conn:
            user = await conn.fetchrow(
                """
                SELECT id, email, name, password_hash, provider, status, 
                       email_verified, created_at, last_login_at
                FROM users 
                WHERE email = $1 AND provider = 'local'
                """,
                request.email
            )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # 妫€鏌ョ敤鎴风姸鎬?
        if user['status'] != 'active':
            raise HTTPException(status_code=401, detail="Account is not active")
        
        # 楠岃瘉瀵嗙爜
        if not self.auth.verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # 鐧诲綍鍓嶅厛娓呴櫎璇ョ敤鎴风殑鎵€鏈夋棫refresh tokens
        async with client.pool.acquire() as conn:
            old_tokens_result = await conn.execute(
                "DELETE FROM refresh_tokens WHERE user_id = $1",
                str(user['id'])
            )
        old_tokens_count = int(old_tokens_result.split()[-1]) if old_tokens_result else 0
        logger.info(f"Login: Cleared {old_tokens_count} old refresh tokens for user {user['id']}")
        
        # 鐢熸垚鏂扮殑tokens
        access_token = self.auth.create_access_token(str(user['id']))
        refresh_token = self.auth.create_refresh_token()
        
        # 瀛樺偍鏂扮殑鍒锋柊token
        await self._store_refresh_token(str(user['id']), refresh_token)
        
        # 鏇存柊鏈€鍚庣櫥褰曟椂闂达紙ADK鍏煎锛?
        async with client.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_login_at = $1 WHERE id = $2",
                datetime.now(), user['id']
            )
        
        # 浣跨敤榛樿搴旂敤鍚嶇О
        app_name = self.default_app_name
        
        # 鍒涘缓鎴栨洿鏂癆DK鐢ㄦ埛鐘舵€?
        await self._update_user_state(client, str(user['id']), {
            'last_login': datetime.now().isoformat(),
            'login_method': 'email_password',
            'status': 'active'
        }, app_name)
        
        # 鍒涘缓ADK浼氳瘽
        session_id = await self._create_adk_session(client, str(user['id']), {
            'access_token': access_token,
            'login_time': datetime.now().isoformat(),
            'login_method': 'email_password'
        }, app_name)
        
        logger.info(f"User logged in: {request.email}")
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=24 * 3600,  # 24灏忔椂
            user=self._user_to_model(user)
        )
    
    async def refresh_token(self, request: RefreshRequest) -> RefreshResponse:
        """鍒锋柊token"""
        client = await self._get_client()
        
        # 楠岃瘉鍒锋柊token
        token_hash = self.auth.hash_refresh_token(request.refresh_token)
        async with client.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT user_id FROM refresh_tokens 
                WHERE token_hash = $1 AND expires_at > $2
                """,
                token_hash, datetime.now()
            )
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user_id = result['user_id']
        
        # 鍒犻櫎鏃х殑鍒锋柊token
        async with client.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM refresh_tokens WHERE token_hash = $1",
                token_hash
            )
        
        # 鐢熸垚鏂扮殑tokens
        access_token = self.auth.create_access_token(user_id)
        new_refresh_token = self.auth.create_refresh_token()
        
        # 瀛樺偍鏂扮殑鍒锋柊token
        await self._store_refresh_token(user_id, new_refresh_token)
        
        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=24 * 3600  # 24灏忔椂
        )
    
    async def get_user(self, user_id: str) -> UserResponse:
        """Get user info"""
        client = await self._get_client()
        
        async with client.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(user=self._user_to_model(user))
    
    async def logout(self, user_id: str, refresh_token: Optional[str] = None):
        """Logout user"""
        client = await self._get_client()
        
        # 1. 鍒犻櫎refresh tokens (寤鸿鍒犻櫎鎵€鏈夛紝閬垮厤token涓嶄竴鑷撮棶棰?
        async with client.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM refresh_tokens WHERE user_id = $1",
                user_id
            )
        
        # 鎻愬彇鍒犻櫎鐨勮鏁?
        deleted_count = int(result.split()[-1]) if result else 0
        logger.info(f"Deleted {deleted_count} refresh tokens for user {user_id}")
        
        # 2. 鏇存柊鐢ㄦ埛鐘舵€佷负 'offline'
        await self._update_user_state(client, user_id, {
            'status': 'offline',
            'logout_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }, self.default_app_name)
        
        # 3. 鍏抽棴鐢ㄦ埛鐨勬墍鏈夋椿璺傾DK sessions
        await self._close_user_sessions(client, user_id, self.default_app_name)
        
        # 4. 璁板綍logout浜嬩欢鍒癆DK
        await self._log_logout_event(client, user_id, self.default_app_name)
        
        logger.info(f"User logged out completely: {user_id}")
    
    async def _store_refresh_token(self, user_id: str, refresh_token: str):
        """瀛樺偍鍒锋柊token"""
        client = await self._get_client()
        
        token_hash = self.auth.hash_refresh_token(refresh_token)
        expires_at = self.auth.get_refresh_token_expire_time()
        
        async with client.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, token_hash, expires_at, datetime.now()
            )
    
    async def _update_user_state(self, client, user_id: str, state_data: dict, app_name: str = "hephaestus"):
        """Update user state"""
        try:
            # 妫€鏌ユ槸鍚﹀凡瀛樺湪鐢ㄦ埛鐘舵€?
            async with client.pool.acquire() as conn:
                existing = await conn.fetchrow(
                    "SELECT * FROM user_states WHERE app_name = $1 AND user_id = $2",
                    app_name, user_id
                )
            
            if existing:
                # 鏇存柊鐜版湁鐘舵€?
                try:
                    # 瑙ｆ瀽鐜版湁鐨凧SON鐘舵€?
                    current_state = json.loads(existing['state']) if existing['state'] else {}
                except (json.JSONDecodeError, TypeError):
                    # 濡傛灉瑙ｆ瀽澶辫触锛屼娇鐢ㄧ┖瀛楀吀
                    current_state = {}
                
                # 鏇存柊鐘舵€?
                current_state.update(state_data)
                
                async with client.pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE user_states 
                        SET state = $1, update_time = $2 
                        WHERE app_name = $3 AND user_id = $4
                        """,
                        json.dumps(current_state), datetime.now(), app_name, user_id
                    )
            else:
                # 鍒涘缓鏂扮殑鐢ㄦ埛鐘舵€?
                async with client.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO user_states (app_name, user_id, state, update_time)
                        VALUES ($1, $2, $3, $4)
                        """,
                        app_name, user_id, json.dumps(state_data), datetime.now()
                    )
            
            logger.info(f"Updated user state for {user_id} in {app_name}")
            
        except Exception as e:
            logger.warning(f"Failed to update user state: {e}")
    
    async def _create_adk_session(self, client, user_id: str, session_data: dict, app_name: str = "hephaestus"):
        """Create ADK session"""
        try:
            # 鐢熸垚浼氳瘽ID
            import uuid
            session_id = str(uuid.uuid4())
            
            # 鎸夌収ADK妗嗘灦鐨勮〃缁撴瀯鎻掑叆浼氳瘽
            async with client.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO sessions (app_name, user_id, id, state, create_time, update_time)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    app_name, user_id, session_id, json.dumps(session_data), datetime.now(), datetime.now()
                )
            
            logger.info(f"Created ADK session {session_id} for user {user_id} in app {app_name}")
            return session_id
            
        except Exception as e:
            logger.warning(f"Failed to create ADK session: {e}")
            return None
    
    async def _log_adk_event(self, client, user_id: str, event_type: str, event_data: dict, 
                           session_id: str = None, app_name: str = "hephaestus"):
        """璁板綍Google ADK浜嬩欢"""
        try:
            import uuid
            event_id = str(uuid.uuid4())
            invocation_id = str(uuid.uuid4())
            
            if session_id:
                # 鎸夌収ADK妗嗘灦鐨勮〃缁撴瀯鎻掑叆浜嬩欢
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
                        "auth_service", datetime.now(), json.dumps(event_data), b''  # actions涓虹┖瀛楄妭
                    )
                
                logger.info(f"Logged ADK event {event_type} for user {user_id} with session {session_id}")
            else:
                logger.warning(f"Failed to create session for event {event_type}, skipping event log")
            
        except Exception as e:
            logger.warning(f"Failed to log ADK event: {e}") 

    async def _get_app_name_for_user(self, user_id: str, context: str = "default") -> str:
        """鑾峰彇鐢ㄦ埛鐨勫簲鐢ㄥ悕绉?
        
        Args:
            user_id: 鐢ㄦ埛ID
            context: 涓婁笅鏂囷紝鍙互鏄?'default', 'agent_creation', 'specific_agent' 绛?
            
        Returns:
            app_name: 搴旂敤鍚嶇О
        """
        # 杩欓噷鍙互鏍规嵁鐢ㄦ埛ID鍜屼笂涓嬫枃鍔ㄦ€佺‘瀹歛pp_name
        # 渚嬪锛氫粠鏁版嵁搴撴煡璇㈢敤鎴峰垱寤虹殑搴旂敤锛屾垨鑰呮牴鎹姹備笂涓嬫枃纭畾
        
        if context == "default":
            return self.default_app_name
        elif context == "agent_creation":
            # 鐢ㄦ埛鍒涘缓鏂癮gent鏃讹紝鍙互浣跨敤鐗瑰畾鐨刟pp_name
            return f"agent_creator_{user_id}"
        else:
            # 鍏朵粬鎯呭喌杩斿洖榛樿搴旂敤
            return self.default_app_name
    
    async def create_agent_session(self, user_id: str, agent_id: str, agent_config: dict) -> str:
        """涓虹敤鎴峰垱寤虹壒瀹歛gent鐨勪細璇?
        
        Args:
            user_id: 鐢ㄦ埛ID
            agent_id: Agent ID
            agent_config: Agent閰嶇疆
            
        Returns:
            session_id: 浼氳瘽ID
        """
        client = await self._get_client()
        
        # 涓虹壒瀹歛gent鍒涘缓app_name
        app_name = f"agent_{agent_id}"
        
        # 鍒涘缓agent浼氳瘽
        session_id = await self._create_adk_session(client, user_id, {
            'agent_id': agent_id,
            'agent_config': agent_config,
            'created_at': datetime.now().isoformat(),
            'session_type': 'agent_session'
        }, app_name)
        
        # 璁板綍agent鍒涘缓浜嬩欢
        if session_id:
            await self._log_adk_event(client, user_id, 'agent_session_created', {
                'agent_id': agent_id,
                'agent_config': agent_config,
                'created_at': datetime.now().isoformat()
            }, session_id, app_name)
        
        return session_id
    
    async def get_user_agents(self, user_id: str) -> list:
        """鑾峰彇鐢ㄦ埛鍒涘缓鐨勬墍鏈塧gents
        
        Args:
            user_id: 鐢ㄦ埛ID
            
        Returns:
            agents: Agent鍒楄〃
        """
        client = await self._get_client()
        
        # 鏌ヨ鐢ㄦ埛鐨勬墍鏈塧gent浼氳瘽
        async with client.pool.acquire() as conn:
            sessions = await conn.fetch(
                """
                SELECT DISTINCT app_name, id as session_id, state
                FROM sessions 
                WHERE user_id = $1 AND app_name LIKE 'agent_%'
                ORDER BY create_time DESC
                """,
                user_id
            )
        
        agents = []
        for session in sessions:
            try:
                state = json.loads(session['state']) if session['state'] else {}
                agent_id = state.get('agent_id')
                if agent_id:
                    agents.append({
                        'agent_id': agent_id,
                        'session_id': session['session_id'],
                        'config': state.get('agent_config', {}),
                        'created_at': state.get('created_at')
                    })
            except Exception as e:
                logger.warning(f"Failed to parse agent session state: {e}")
        
        return agents

    async def _close_user_sessions(self, client, user_id: str, app_name: str = "hephaestus"):
        """Close all active ADK sessions for a user"""
        try:
            # 鏇存柊鎵€鏈夎鐢ㄦ埛鐨剆essions鐘舵€佷负closed
            async with client.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE sessions 
                    SET state = jsonb_set(COALESCE(state, '{}'), '{status}', '"closed"'),
                        update_time = $1
                    WHERE app_name = $2 AND user_id = $3 
                    AND (state->>'status' IS NULL OR state->>'status' != 'closed')
                    """,
                    datetime.now(), app_name, user_id
                )
                
            closed_count = int(result.split()[-1]) if result else 0
            logger.info(f"Closed {closed_count} ADK sessions for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to close user sessions: {e}")
    
    async def _log_logout_event(self, client, user_id: str, app_name: str = "hephaestus"):
        """Log logout event to ADK"""
        try:
            # 灏濊瘯鎵惧埌鏈€杩戠殑娲昏穬session鏉ヨ褰昹ogout浜嬩欢
            async with client.pool.acquire() as conn:
                recent_session = await conn.fetchrow(
                    """
                    SELECT id FROM sessions 
                    WHERE app_name = $1 AND user_id = $2 
                    ORDER BY update_time DESC 
                    LIMIT 1
                    """,
                    app_name, user_id
                )
            
            session_id = recent_session['id'] if recent_session else None
            
            logout_data = {
                'event_type': 'user_logout',
                'logout_time': datetime.now().isoformat(),
                'reason': 'user_initiated'
            }
            
            await self._log_adk_event(client, user_id, "logout", logout_data, 
                                    session_id, app_name)
                                    
        except Exception as e:
            logger.warning(f"Failed to log logout event: {e}")
