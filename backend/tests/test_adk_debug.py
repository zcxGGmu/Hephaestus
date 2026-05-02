
from google.genai import types # type: ignore
from google.adk.agents.run_config import RunConfig, StreamingMode # type: ignore
from google.adk.models.lite_llm import LiteLlm # type: ignore
from google.adk.agents import LlmAgent # type: ignore
from google.adk.sessions import DatabaseSessionService # type: ignore
from services.model_only_session_service import ModelOnlyDBSessionService
from google.adk import Runner # type: ignore
from google.adk.agents.callback_context import CallbackContext # type: ignore
from google.adk.models import LlmRequest, LlmResponse # type: ignore
from typing import Optional
import asyncio


# 鏁版嵁搴撹繛鎺ラ厤缃?
DB_CONFIG = {
    'host': 'localhost',  # 杩欓噷鏇挎崲鎴愬疄闄呯殑 PostgreSQL 鏈嶅姟鍣ㄥ湴鍧€
    'port': 5432,   # 杩欓噷鏇挎崲鎴愬疄闄呯殑 PostgreSQL 鏈嶅姟鍣ㄧ鍙?
    'database': 'adk',  # 杩欓噷鏇挎崲鎴愬疄闄呯殑 PostgreSQL 鏁版嵁搴撳悕绉?
    'user': 'postgres',  # 杩欓噷鏇挎崲鎴愬疄闄呯殑 PostgreSQL 鐢ㄦ埛鍚?
    'password': 'snowball2019'  # 杩欓噷鏇挎崲鎴愬疄闄呯殑 PostgreSQL 瀵嗙爜
}

# 鐢熸垚鏁版嵁搴撹繛鎺ュ瓧绗︿覆
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

streaming_mode = StreamingMode.SSE
run_config = RunConfig(streaming_mode=streaming_mode)

# 鍒涘缓LiteLlm妯″瀷
model = LiteLlm(
    model="openai/gpt-4o",
    api_key="your_openai_api_key_here"
)

# 瀹氫箟鍥炶皟鍑芥暟鏉ユ彁鍙?invocation_id
def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """ADK鍥炶皟锛氬湪LLM璋冪敤鍓嶈幏鍙杋nvocation_id"""
    try:
        print(f"馃敆 before_model_callback 琚Е鍙戯紒锛侊紒")
        print(f"馃敆 CallbackContext 灞炴€? {dir(callback_context)}")
        
        if hasattr(callback_context, 'invocation_id') and callback_context.invocation_id:
            print(f"鉁?鎴愬姛鎻愬彇 invocation_id: {callback_context.invocation_id}")
        else:
            print(f"鈿狅笍 涓婁笅鏂囦腑娌℃湁鎵惧埌 invocation_id")
            
        # 鎵撳嵃鏇村涓婁笅鏂囦俊鎭?
        if hasattr(callback_context, 'session_id'):
            print(f"馃敆 Session ID: {callback_context.session_id}")
        if hasattr(callback_context, 'user_id'):
            print(f"馃敆 User ID: {callback_context.user_id}")
            
    except Exception as e:
        print(f"鈿狅笍 鍥炶皟鍑芥暟鎵ц鍑洪敊: {e}")
    
    # 鉁?鍏抽敭锛氬繀椤昏繑鍥?None 璁〢DK缁х画姝ｅ父鎵ц
    return None

# 鍒涘缓 Agent 瀵硅薄锛屾坊鍔犲洖璋?
agent = LlmAgent(
    name="hephaestus",
    model=model,
    instruction="浣犳槸鎴戠殑AI鍔╂墜锛岃鏍规嵁鐢ㄦ埛鐨勯棶棰樼粰鍑哄洖绛斻€?,
    before_model_callback=before_model_callback  # 馃敆 娣诲姞鍥炶皟
)

query = "浣犲ソ锛岃浣犱粙缁嶄竴涓嬩綘鑷繁銆?

# 灏嗙敤鎴风殑闂杞崲涓?ADK 鏍煎紡
content = types.Content(role='user', parts=[types.Part(text=query)])

async def run_async():
    # 缁熶竴浣跨敤鏁版嵁搴撲腑宸插瓨鍦ㄧ殑 session_id
    USER_ID = "5b6cb69c-cb47-4178-82b5-d579e83e8ec7"
    SESSION_ID = "f40753f1-f75f-474c-b357-dfd59b78d560"  # 浣跨敤鏁版嵁搴撲腑瀹為檯瀛樺湪鐨?
    
    # 鍒涘缓 SessionService 瀵硅薄
    session_service = ModelOnlyDBSessionService(DATABASE_URL)
    
    try:
        # 鍦ㄥ紓姝ュ嚱鏁颁腑鍒涘缓浼氳瘽
        await session_service.get_session(
            app_name="hephaestus", 
            user_id=USER_ID, 
            session_id=SESSION_ID
        )
        print("鉁?鎴愬姛鍔犺浇鏁版嵁搴撲細璇?)
        
    except Exception as e:
        print(f"鉂?鏁版嵁搴撲細璇濇暟鎹崯鍧? {e}")
        print("馃攧 灏濊瘯鍒犻櫎骞堕噸鏂板垱寤轰細璇?..")
        
        try:
            # 鍏堝皾璇曞垹闄ゆ崯鍧忕殑浼氳瘽鏁版嵁
            import asyncpg
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                # 鍒犻櫎鎹熷潖鐨勪簨浠舵暟鎹?
                await conn.execute(
                    "DELETE FROM events WHERE session_id = $1", SESSION_ID
                )
                print("馃棏锔?娓呯悊浜嗘崯鍧忕殑浜嬩欢鏁版嵁")
                
                # 鍒犻櫎鎹熷潖鐨勪細璇濇暟鎹?
                await conn.execute(
                    "DELETE FROM sessions WHERE id = $1", SESSION_ID
                )
                print("馃棏锔?娓呯悊浜嗘崯鍧忕殑浼氳瘽鏁版嵁")
                
            finally:
                await conn.close()
            
            # 閲嶆柊鍒涘缓骞插噣鐨勪細璇?
            await session_service.create_session(
                app_name="hephaestus", 
                user_id=USER_ID, 
                session_id=SESSION_ID
            )
            print("鉁?閲嶆柊鍒涘缓鏁版嵁搴撲細璇濇垚鍔?)
            
        except Exception as e2:
            print(f"鉂?鏁版嵁搴撳畬鍏ㄦ棤娉曚娇鐢? {e2}")
            print("馃攧 鍥為€€鍒板唴瀛樹細璇濇湇鍔?..")
            
            # 浣跨敤鍐呭瓨浼氳瘽鏈嶅姟浣滀负澶囬€夋柟妗?
            from google.adk.sessions import InMemorySessionService # type: ignore
            session_service = InMemorySessionService()
            await session_service.create_session(
                app_name="hephaestus", 
                user_id=USER_ID, 
                session_id=SESSION_ID
            )
            print("鉁?鍐呭瓨浼氳瘽鏈嶅姟鍒涘缓鎴愬姛")
    
    # 鍒涘缓 Runner
    runner = Runner(
        agent=agent,
        app_name="hephaestus",
        session_service=session_service
    )
    
    print(f"馃殌 寮€濮嬭繍琛?ADK - User ID: {USER_ID}, Session ID: {SESSION_ID}")
    
    # 寮傛杩愯 - 鐜板湪浣跨敤缁熶竴鐨?SESSION_ID
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,  # 馃幆 淇锛氫娇鐢ㄥ悓涓€涓?SESSION_ID
        new_message=content,
    ):
        # 鎵撳嵃浜嬩欢鐨?invocation_id锛堝鏋滄湁鐨勮瘽锛?
        if hasattr(event, 'invocation_id') and event.invocation_id:
            print(f"馃搵 浜嬩欢 invocation_id: {event.invocation_id}")
            
        # 瑙ｆ瀽 ADK 浜嬩欢锛屽彧鏄剧ず鍏抽敭淇℃伅
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"馃 AI鍥炲: {part.text}")
            
            if hasattr(event, 'usage_metadata') and event.usage_metadata:
                print(f"馃搳 Token浣跨敤: 杈撳叆={event.usage_metadata.prompt_token_count}, 杈撳嚭={event.usage_metadata.candidates_token_count}, 鎬昏={event.usage_metadata.total_token_count}")
        else:
            # 濡傛灉涓嶆槸鍐呭浜嬩欢锛屾樉绀轰簨浠剁被鍨?
            print(f"馃摠 浜嬩欢绫诲瀷: {type(event).__name__}")
            if hasattr(event, 'error_message') and event.error_message:
                print(f"鉂?閿欒: {event.error_message}")
        
        print("---")

# 杩愯寮傛鍑芥暟
if __name__ == "__main__":
    asyncio.run(run_async())

