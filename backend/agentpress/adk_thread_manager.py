"""
Google ADK 鐗堟湰锛?.12.0
Google ADK 鐗堟湰鐨勭嚎绋嬬鐞嗗櫒
瀹炵幇涓?ThreadManager 鐩稿悓鐨勬帴鍙ｏ紝浣嗕娇鐢?Google ADK 浣滀负搴曞眰瀹炵幇
"""

import json
from typing import List, Dict, Any, Optional, Type, Union, AsyncGenerator, Literal
from services.postgresql import DBConnection
from utils.logger import logger
from agentpress.tool_registry import ToolRegistry
from agentpress.context_manager import ContextManager
from agentpress.response_processor import ResponseProcessor, ProcessorConfig
from agentpress.tool import Tool


ADK_AVAILABLE = True
from google.adk.agents.llm_agent import LlmAgent # type: ignore
from google.adk.runners import Runner # type: ignore
from google.adk.sessions import DatabaseSessionService # type: ignore
from google.adk.tools.base_tool import BaseTool # type: ignore


try:
    from langfuse.client import StatefulGenerationClient, StatefulTraceClient # type: ignore
except ImportError:
    try:
        from langfuse import StatefulGenerationClient, StatefulTraceClient # type: ignore
    except ImportError:
        from typing import Any
        StatefulGenerationClient = Any
        StatefulTraceClient = Any

from services.langfuse import langfuse
from utils.config import config

# Type alias for tool choice
ToolChoice = Literal["auto", "required", "none"]

class ADKThreadManager:
    """
    Google ADK 鐗堟湰鐨勭嚎绋嬬鐞嗗櫒
    瀹炵幇涓?ThreadManager 鐩稿悓鐨勬帴鍙ｏ紝浣嗕娇鐢?Google ADK 浣滀负搴曞眰瀹炵幇
    """

    def __init__(self, trace: Optional[StatefulTraceClient] = None, is_agent_builder: bool = False, target_agent_id: Optional[str] = None, agent_config: Optional[dict] = None): # type: ignore
        """鍒濆鍖?ADK 绾跨▼绠＄悊鍣?

        Args:
            trace: Optional trace client for logging
            is_agent_builder: Whether this is an agent builder session
            target_agent_id: ID of the agent being built (if in agent builder mode)
            agent_config: Optional agent configuration with version information
        """
        if not ADK_AVAILABLE:
            raise ImportError("Google ADK is not available. Please install google-adk package.")
        
        self.db = DBConnection()
        self.tool_registry = ToolRegistry()
        self.trace = trace
        self.is_agent_builder = is_agent_builder
        self.target_agent_id = target_agent_id
        self.agent_config = agent_config
        
        if not self.trace:
            self.trace = langfuse.trace(name="anonymous:adk_thread_manager")
        
        self.response_processor = ResponseProcessor(
            tool_registry=self.tool_registry,
            add_message_callback=self.add_message,
            trace=self.trace,
            is_agent_builder=self.is_agent_builder,
            target_agent_id=self.target_agent_id,
            agent_config=self.agent_config
        )
        self.context_manager = ContextManager()
        
        # # ADK 缁勪欢
        # self.llm_agent: Optional[LlmAgent] = None
        # self.runner: Optional[Runner] = None
        # self.session_service: Optional[DatabaseSessionService] = None

    def add_tool(self, tool_class: Type[Tool], function_names: Optional[List[str]] = None, **kwargs):
        """Add a tool to the ThreadManager."""
        self.tool_registry.register_tool(tool_class, function_names, **kwargs)

    def _convert_tool_to_adk(self, tool_class: Type, **kwargs) -> Optional[BaseTool]:
        """灏嗗伐鍏疯浆鎹负 ADK 鏍煎紡

        Args:
            tool_class: 宸ュ叿绫?
            **kwargs: 宸ュ叿鍙傛暟

        Returns:
            ADK 宸ュ叿瀹炰緥
        """
        try:
            # 杩欓噷闇€瑕佹牴鎹叿浣撶殑宸ュ叿绫诲疄鐜拌浆鎹㈤€昏緫
            # 鏆傛椂杩斿洖 None锛屽悗缁彲浠ユ牴鎹渶瑕佸疄鐜板叿浣撶殑杞崲
            logger.debug(f"Converting tool {tool_class.__name__} to ADK format")
            return None
        except Exception as e:
            logger.error(f"Failed to convert tool {tool_class.__name__}: {e}")
            return None

    async def get_llm_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a thread from events table.

        This method fetches messages from the events table and formats them
        to match the original messages table format for downstream compatibility.

        Args:
            thread_id: The ID of the thread to get messages for.

        Returns:
            List of message objects in the same format as original messages table.
        """
        logger.debug(f"Getting messages for thread {thread_id} from events table")
        client = await self.db.client

        try:
            # 鑾峰彇浜嬩欢锛屽垎鎵硅幏鍙栵紝閬垮厤鏁版嵁搴撹繃杞?
            all_events = []
            batch_size = 1000
            offset = 0
            
            while True:
                # 浠?events 琛ㄨ幏鍙栨秷鎭紝鎸夋椂闂存埑鎺掑簭
                result = await client.table('events').select(
                    'id, author, content, timestamp, session_id, user_id, app_name, invocation_id'
                ).eq('session_id', thread_id).in_(
                    'author', ['user', 'assistant']
                ).order('timestamp').range(offset, offset + batch_size - 1).execute()
                
                if not result.data or len(result.data) == 0:
                    break
                    
                all_events.extend(result.data)
                
                # 濡傛灉鑾峰彇鐨勮褰曟暟灏忎簬 batch_size锛屽垯琛ㄧず宸茬粡鍒拌揪鏈熬
                if len(result.data) < batch_size:
                    break
                    
                offset += batch_size
            
            # 浣跨敤 all_events 鑰屼笉鏄?result.data 
            result_data = all_events

            # 瑙ｆ瀽杩斿洖鐨勬暟鎹紝骞惰浆鎹负鍘熷娑堟伅鏍煎紡
            if not result_data:
                return []

            # 灏嗕簨浠惰浆鎹负鍘熷娑堟伅鏍煎紡锛岀敤浜庝笅娓稿吋瀹?
            messages = []
            for event in result_data:
                try:
                    # 纭繚event鏄瓧鍏告牸寮?
                    if hasattr(event, '__dict__'):
                        event = dict(event)
                    
                    # 瑙ｆ瀽浜嬩欢鍐呭
                    content = event.get('content', {})
                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except json.JSONDecodeError:
                            # 濡傛灉涓嶆槸JSON锛屽綋浣滅函鏂囨湰澶勭悊
                            content = {"content": content}
                    
                    # 鏋勫缓涓庡師濮?messages 琛ㄦ牸寮忓吋瀹圭殑娑堟伅瀵硅薄
                    message = {
                        "role": event.get('author', 'user'),
                        "message_id": event.get('id'),
                        "timestamp": event.get('timestamp'),
                        "app_name": event.get('app_name'),
                        "user_id": event.get('user_id'),
                        "session_id": event.get('session_id'),
                        "invocation_id": event.get('invocation_id')
                    }
                    
                    # 澶勭悊timestamp瀛楁锛岀‘淇漝atetime瀵硅薄琚浆鎹负瀛楃涓?
                    if message.get('timestamp') and hasattr(message['timestamp'], 'isoformat'):
                        message['timestamp'] = message['timestamp'].isoformat()
                    
                    # 澶勭悊鍐呭鏍煎紡 - 鍏煎鍘熷鏍煎紡鍜孉DK鏍煎紡
                    if isinstance(content, dict):
                        # 澶勭悊ADK鏍煎紡 {"role": "user", "parts": [{"text": "..."}]}
                        if 'parts' in content and isinstance(content['parts'], list):
                            # 鎻愬彇ADK parts涓殑鏂囨湰鍐呭
                            text_parts = []
                            for part in content['parts']:
                                if isinstance(part, dict) and 'text' in part:
                                    text_parts.append(part['text'])
                            message["content"] = ' '.join(text_parts).strip()
                        # 濡傛灉瀛樺湪锛氬鐞嗗師濮嬫牸寮?{"role": "user", "content": "..."}
                        elif 'content' in content:
                            message["content"] = content['content']
                        else:
                            # 濡傛灉閮芥病鏈夛紝灏嗘暣涓璞¤浆涓哄瓧绗︿覆锛堝悜鍚庡吋瀹癸級
                            message["content"] = json.dumps(content)
                    else:
                        message["content"] = str(content)
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.error(f"Failed to parse event {event.get('id')}: {e}")
                    continue

            logger.debug(f"Retrieved {len(messages)} messages from events table for thread {thread_id}")
            return messages

        except Exception as e:
            logger.error(f"Failed to get messages for thread {thread_id}: {str(e)}", exc_info=True)
            return []

    async def run_thread(
        self,
        thread_id: str,
        system_prompt: Dict[str, Any],
        stream: bool = True,
        temporary_message: Optional[Dict[str, Any]] = None,
        llm_model: str = "deepseek/deepseek-chat",
        llm_temperature: float = 0,
        llm_max_tokens: Optional[int] = None,
        processor_config: Optional[ProcessorConfig] = None,
        tool_choice: ToolChoice = "auto",
        native_max_auto_continues: int = 0,
        available_functions: Optional[Dict[str, callable]] = None,
        max_xml_tool_calls: int = 0,
        include_xml_examples: bool = False,
        enable_thinking: Optional[bool] = False,
        reasoning_effort: Optional[str] = 'low',
        enable_context_manager: bool = True,
        generation: Optional[StatefulGenerationClient] = None, # type: ignore
    ) -> Union[Dict[str, Any], AsyncGenerator]:
        """浣跨敤 ADK Runner 鎵ц绾跨▼

        Args:
            thread_id: 绾跨▼ID
            system_prompt: 绯荤粺鎻愮ず璇?
            stream: 鏄惁浣跨敤娴佸紡鍝嶅簲
            temporary_message: 涓存椂娑堟伅
            llm_model: 妯″瀷鍚嶇О
            llm_temperature: 娓╁害鍙傛暟
            llm_max_tokens: 鏈€澶oken鏁?
            tool_choice: 宸ュ叿閫夋嫨
            enable_thinking: 鏄惁鍚敤鎬濊€?
            reasoning_effort: 鎺ㄧ悊鍔姏绋嬪害
            enable_context_manager: 鏄惁鍚敤涓婁笅鏂囩鐞嗗櫒
            user_id: 鐢ㄦ埛ID
            user_message: 鐢ㄦ埛娑堟伅
            **kwargs: 鍏朵粬鍙傛暟

        Yields:
            鍝嶅簲浜嬩欢
        """
        logger.info(f"current thread_id: {thread_id}")
        logger.info(f"current llm_model: {llm_model}")

        # 纭繚 processor_config 涓嶄负 None
        config = processor_config or ProcessorConfig()

        # 濡傛灉 max_xml_tool_calls 鎸囧畾涓旀湭鍦?config 涓缃紝鍒欏簲鐢?
        if max_xml_tool_calls > 0 and not config.max_xml_tool_calls:
            config.max_xml_tool_calls = max_xml_tool_calls

        # 鍒涘缓涓€涓伐浣滃壇鏈紝浠ヤ究鍙兘淇敼
        working_system_prompt = system_prompt.copy()

        # 鎺у埗鏄惁闇€瑕佽嚜鍔ㄧ户缁紝鍥犱负宸ュ叿璋冪敤瀹屾垚鍘熷洜
        # Control whether we need to auto-continue due to tool_calls finish reason
        auto_continue = True
        auto_continue_count = 0

        # 鍏变韩鐘舵€侊紝鐢ㄤ簬杩炵画娴佸紡杈撳嚭
        continuous_state = {
            'accumulated_content': '',
            'thread_run_id': None
        }

        async def _run_once(temp_msg=None):
            try:
                # 纭繚 config 鍦ㄥ綋鍓嶄綔鐢ㄥ煙鍙敤
                nonlocal config
                # 娉ㄦ剰锛歝onfig 鐜板湪淇濊瘉瀛樺湪锛屽洜涓轰笂闈㈢殑妫€鏌?

                # 1. 浠庣嚎绋嬭幏鍙栨秷鎭紝鐢ㄤ簬 LLM 璋冪敤
                messages = await self.get_llm_messages(thread_id)

                # 2. 妫€鏌?token 璁℃暟锛屽啀缁х画
                token_count = 0
                try:
                    from litellm.utils import token_counter # type: ignore
                    # 浣跨敤淇敼鍚庣殑working_system_prompt杩涜token璁℃暟
                    token_count = token_counter(model=llm_model, messages=[working_system_prompt] + messages)
                    token_threshold = self.context_manager.token_threshold
                    logger.info(f"Thread {thread_id} token count: {token_count}/{token_threshold} ({(token_count/token_threshold)*100:.1f}%)")

                except Exception as e:
                    logger.error(f"Error counting tokens or summarizing: {str(e)}")

                # 3. 棰勫鐞嗚緭鍏ユ秷鎭紝鍑嗗LLM璋冪敤 + 娣诲姞涓存椂娑堟伅锛堝鏋滃瓨鍦級
                # 浣跨敤淇敼鍚庣殑working_system_prompt锛屽彲鑳藉寘鍚玐ML绀轰緥
                prepared_messages = [working_system_prompt]

                # 鎵惧埌鏈€鍚庝竴涓敤鎴锋秷鎭殑绱㈠紩
                last_user_index = -1
                for i, msg in enumerate(messages):
                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        last_user_index = i

                # 鎻掑叆涓存椂娑堟伅锛屽鏋滃瓨鍦紝鎻掑叆鍒版渶鍚庝竴涓敤鎴锋秷鎭箣鍓?
                if temp_msg and last_user_index >= 0:
                    prepared_messages.extend(messages[:last_user_index])
                    prepared_messages.append(temp_msg)
                    prepared_messages.extend(messages[last_user_index:])
                    logger.info("Added temporary message before the last user message")
                else:
                    # 濡傛灉娌℃湁鐢ㄦ埛娑堟伅鎴栨病鏈変复鏃舵秷鎭紝鍒欐坊鍔犳墍鏈夋秷鎭?
                    prepared_messages.extend(messages)
                    if temp_msg:
                        prepared_messages.append(temp_msg)
                        logger.info("Added temporary message to the end of prepared messages")

                # 馃敡 淇锛氱Щ闄ゅ彲鑳藉鑷撮噸澶嶈緭鍑虹殑涓存椂鍔╂墜娑堟伅閫昏緫
                # Agent搴旇鍩轰簬鏁版嵁搴撲腑宸蹭繚瀛樼殑娑堟伅鍘嗗彶鏉ヨ嚜鍔ㄧ户缁紝鑰屼笉鏄噸澶嶄复鏃跺唴瀹?
                if auto_continue_count > 0:
                    logger.info(f"Auto-continue round {auto_continue_count}: using existing message history as context")
     
                prepared_messages = self.context_manager.compress_messages(prepared_messages, llm_model)

                # 5. 鍑嗗澶фā鍨嬭皟鐢?
                try:
                    # import datatime
                    # if generation:
                    #     generation.update(
                    #         input=prepared_messages,
                    #         start_time=datetime.datetime.now(datetime.timezone.utc),
                    #         model=llm_model,
                    #         model_parameters={
                    #           "max_tokens": llm_max_tokens,
                    #           "temperature": llm_temperature,
                    #           "enable_thinking": enable_thinking,
                    #           "reasoning_effort": reasoning_effort,
                    #           "tool_choice": tool_choice,
                    #           "tools": openapi_tool_schemas,
                    #         }
                    #     )

                    from services.llm import make_adk_api_call
                    
                    tool_functions = available_functions
                    # 灏嗘瀯寤哄ソ鐨勬彁绀鸿瘝瀹為檯鍙戦€佸埌澶фā鍨嬩腑                    
                    llm_response = await make_adk_api_call(
                        prepared_messages, 
                        llm_model,
                        temperature=llm_temperature,
                        max_tokens=llm_max_tokens,
                        tools=tool_functions,  # 馃敡 浼犻€掑伐鍏峰嚱鏁板瓧鍏?
                        tool_choice=tool_choice if config.native_tool_calling else "none",
                        stream=stream,
                        enable_thinking=enable_thinking,
                        reasoning_effort=reasoning_effort
                    )
                    logger.info(f"Successfully received raw LLM API response stream/object")
                except Exception as e:
                    logger.error(f"Failed to make LLM API call: {str(e)}", exc_info=True)
                    raise

                # 6. 杩欐牱寮€濮嬪鐞咥DK杩斿洖鐨勫紓姝ョ敓鎴愬櫒
                if stream:
                    logger.info("Processing ADK streaming response")

                    from typing import AsyncGenerator, cast
                    
                    try:
                        response_generator = self.response_processor.process_adk_streaming_response(
                            adk_response=cast(AsyncGenerator, llm_response),
                            thread_id=thread_id,
                            config=config,
                            prompt_messages=prepared_messages,
                            llm_model=llm_model,
                            can_auto_continue=(native_max_auto_continues > 0),
                            auto_continue_count=auto_continue_count,
                            continuous_state=continuous_state
                        )
                        logger.info("process_adk_streaming_response called successfully")
                        return response_generator
                    except Exception as e:
                        logger.error(f"process_adk_streaming_response called failed: {e}")
                        import traceback
                        traceback.print_exc()
                        raise
                    # else:
                    #     # Fallback to non-streaming if response is not iterable
                    #     response_generator = self.response_processor.process_non_streaming_response(
                    #         llm_response=llm_response,
                    #         thread_id=thread_id,
                    #         config=config,
                    #         prompt_messages=prepared_messages,
                    #         llm_model=llm_model,
                    #     )

                    # return response_generator
                else:
                    logger.debug("Processing non-streaming response")
                    # Pass through the response generator without try/except to let errors propagate up
                    response_generator = self.response_processor.process_non_streaming_response(
                        llm_response=llm_response,
                        thread_id=thread_id,
                        config=config,
                        prompt_messages=prepared_messages,
                        llm_model=llm_model,
                    )
                    return response_generator # Return the generator

            except Exception as e:
                logger.error(f"Error in run_thread: {str(e)}", exc_info=True)
                # Return the error as a dict to be handled by the caller
                return {
                    "type": "status",
                    "status": "error",
                    "message": str(e)
                }

        # 瀹氫箟涓€涓寘瑁呭櫒鐢熸垚鍣紝澶勭悊鑷姩缁х画閫昏緫
        async def auto_continue_wrapper():
            print("鎴戝厛杩涘叆鐨刟uto_continue_wrapper")
            nonlocal auto_continue, auto_continue_count

            while auto_continue and (native_max_auto_continues == 0 or auto_continue_count < native_max_auto_continues):
                # 閲嶇疆 auto_continue 鐢ㄤ簬姝よ凯浠?
                auto_continue = False

                # 杩愯涓€娆＄嚎绋嬶紝浼犻€掑彲鑳戒慨鏀瑰悗鐨勭郴缁熸彁绀?
                # 浠呭湪绗竴娆¤凯浠ｆ椂浼犻€?temp_msg
                try:
                    print("鎴戝湪杩欓噷瑕佸紑濮嬫墽琛?_run_once")
                    response_gen = await _run_once(temporary_message if auto_continue_count == 0 else None)

                    # Handle error responses
                    if isinstance(response_gen, dict) and "status" in response_gen and response_gen["status"] == "error":
                        logger.error(f"Error in auto_continue_wrapper: {response_gen.get('message', 'Unknown error')}")
                        yield response_gen
                        return  # Exit the generator on error
                    print("鎴戝湪杩欓噷瑕佽幏鍙?response_gen 鐨勫睘鎬т簡")
                    # Process each chunk
                    try:
                        if hasattr(response_gen, '__aiter__'):
                            from typing import AsyncGenerator, cast
                            async for chunk in cast(AsyncGenerator, response_gen):
                                
                                # 馃敡 娣诲姞锛氭娴嬪伐鍏锋墽琛屽畬鎴愶紝绔嬪嵆缁堟
                                if chunk.get('type') == 'status':
                                    try:
                                        content = json.loads(chunk.get('content', '{}'))
                                        status_type = content.get('status_type')
                                        
                                        # 妫€娴嬪埌宸ュ叿瀹屾垚锛岀珛鍗崇粓姝㈡暣涓祦绋?
                                        if status_type == 'tool_completed':
                                            logger.info("馃敡 妫€娴嬪埌宸ュ叿鎵ц瀹屾垚锛岀珛鍗崇粓姝㈡祦绋?)
                                            yield chunk  # 鍏堣緭鍑哄伐鍏峰畬鎴愮姸鎬?
                                            return  # 馃敡 褰诲簳缁堟锛屼笉鍐嶅鐞嗕换浣曞悗缁唴瀹?
                                            
                                        # 鍏朵粬status澶勭悊閫昏緫
                                        if content.get('finish_reason') == 'length':
                                            logger.info(f"Detected finish_reason='length', auto-continuing ({auto_continue_count + 1}/{native_max_auto_continues})")
                                            auto_continue = True
                                            auto_continue_count += 1
                                            continue
                                    except (json.JSONDecodeError, TypeError):
                                        # If content is not valid JSON, just yield the chunk normally
                                        pass
                                
                                # Check if this is a finish reason chunk with tool_calls or xml_tool_limit_reached
                                if chunk.get('type') == 'finish':
                                    if chunk.get('finish_reason') == 'tool_calls':
                                        # Only auto-continue if enabled (max > 0)
                                        if native_max_auto_continues > 0:
                                            logger.info(f"Detected finish_reason='tool_calls', auto-continuing ({auto_continue_count + 1}/{native_max_auto_continues})")
                                            auto_continue = True
                                            auto_continue_count += 1
                                            # Don't yield the finish chunk to avoid confusing the client
                                            continue
                                    elif chunk.get('finish_reason') == 'xml_tool_limit_reached':
                                        # Don't auto-continue if XML tool limit was reached
                                        logger.info(f"Detected finish_reason='xml_tool_limit_reached', stopping auto-continue")
                                        auto_continue = False
                                        # Still yield the chunk to inform the client

                                # Otherwise just yield the chunk normally
                                yield chunk
                        else:
                            # response_gen is not iterable (likely an error dict), yield it directly
                            yield response_gen

                        # If not auto-continuing, we're done
                        if not auto_continue:
                            break
                    except Exception as e:
                        if ("AnthropicException - Overloaded" in str(e)):
                            logger.error(f"AnthropicException - Overloaded detected - Falling back to OpenRouter: {str(e)}", exc_info=True)
                            nonlocal llm_model
                            # Remove "-20250514" from the model name if present
                            model_name_cleaned = llm_model.replace("-20250514", "")
                            llm_model = f"openrouter/{model_name_cleaned}"
                            auto_continue = True
                            continue # Continue the loop
                        else:
                            # If there's any other exception, log it, yield an error status, and stop execution
                            logger.error(f"Error in auto_continue_wrapper generator: {str(e)}", exc_info=True)
                            yield {
                                "type": "status",
                                "status": "error",
                                "message": f"Error in thread processing: {str(e)}"
                            }
                        return  # Exit the generator on any error
                except Exception as outer_e:
                    # Catch exceptions from _run_once itself
                    logger.error(f"Error executing thread: {str(outer_e)}", exc_info=True)
                    yield {
                        "type": "status",
                        "status": "error",
                        "message": f"Error executing thread: {str(outer_e)}"
                    }
                    return  # Exit immediately on exception from _run_once

            # If we've reached the max auto-continues, log a warning
            if auto_continue and auto_continue_count >= native_max_auto_continues:
                logger.warning(f"Reached maximum auto-continue limit ({native_max_auto_continues}), stopping.")
                yield {
                    "type": "content",
                    "content": f"\n[Agent reached maximum auto-continue limit of {native_max_auto_continues}]"
                }        

        # 濡傛灉鑷姩缁х画琚鐢?(native_max_auto_continues=0), 鍙繍琛屼竴娆?
        if native_max_auto_continues == 0:
            print("鑷姩缁х画琚鐢?(native_max_auto_continues=0)")
            # Pass the potentially modified system prompt and temp message
            return await _run_once(temporary_message)
        
        # 鍚﹀垯杩斿洖鑷姩缁х画鍖呰鍣ㄧ敓鎴愬櫒
        return auto_continue_wrapper()
        
        # try:
        #     # if not self.runner or not self.session:
        #     #     raise RuntimeError("ADK components not initialized. Call setup() first.")
            
        #     # # 鍑嗗鐢ㄦ埛杈撳叆
        #     # if user_message:
        #     #     message_text = user_message
        #     # elif temporary_message:
        #     #     # 澶勭悊涓存椂娑堟伅
        #     #     if isinstance(temporary_message.get('content'), list):
        #     #         # 濡傛灉鏄妯℃€佹秷鎭紝鎻愬彇鏂囨湰鍐呭
        #     #         text_parts = []
        #     #         for part in temporary_message['content']:
        #     #             if isinstance(part, dict) and part.get('type') == 'text':
        #     #                 text_parts.append(part.get('text', ''))
        #     #         message_text = ' '.join(text_parts)
        #     #     else:
        #     #         message_text = str(temporary_message.get('content', 'Hello'))
        #     # else:
        #     #     message_text = "Hello"
            
        #     # logger.debug(f"Prepared user message: {message_text[:100]}...")
            
        #     message_text = "濡備綍鐞嗚В榛戞礊锛?

        #     from google.genai import types # type:ignore
        #     # 鍒涘缓鐢ㄦ埛鍐呭
        #     user_content = content = types.Content(role='user', parts=[types.Part(text=message_text)])
        #     print(f"user_content: {user_content}")
        #     # 浣跨敤 ADK Runner 鎵ц

        #     from google.adk.agents.run_config import RunConfig, StreamingMode # type: ignore
        #     run_config = RunConfig(streaming_mode=StreamingMode.SSE)

        #     from google.adk.models.lite_llm import LiteLlm # type: ignore

        #     model=LiteLlm(
        #         model="openai/gpt-4o",  
        #         api_key="your_openai_api_key_here"
        #     )

        #     from google.adk.agents import LlmAgent # type: ignore

        #     print(f"system_prompt: {system_prompt}")
        #     init_agent = LlmAgent(
        #         name="hephaestus_basic_agent",
        #         model=model,
        #         instruction=system_prompt
        #     )


        #     # 浣跨敤鏁版嵁搴撲細璇濇湇鍔?
        #     DB_CONFIG = {
        #         'host': 'localhost',
        #         'port': 5432,
        #         'database': 'adk',
        #         'user': 'postgres',
        #         'password': 'snowball2019'
        #     }

        #     print(f"DB_CONFIG: {DB_CONFIG}")
        #     DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            
        #     from google.adk.sessions import DatabaseSessionService # type: ignore
        #     session_service = DatabaseSessionService(DATABASE_URL)

        #     # 鍒涘缓浼氳瘽
        #     APP_NAME = "hephaestus"
        #     USER_ID = "f7a2a1ab-a233-49b4-abdc-c58c650cfa06"
        #     SESSION_ID = thread_id

        #     print("寮€濮嬪垱寤烘暟鎹簱session")
        #     await session_service.create_session(
        #         app_name=APP_NAME, 
        #         user_id=USER_ID,
        #         session_id=SESSION_ID
        #     )
        #     print("鏁版嵁搴搒ession鍒涘缓鎴愬姛")

        #     # 鍒涘缓runner
        #     runner = Runner(
        #         agent=init_agent,
        #         app_name="hephaestus",
        #         session_service=session_service
        #     )
        #     print("寮€濮嬫墽琛宺unner锛?)

        #     # 鎵ц浠ｇ悊杩愯鐨勬祦寮忚緭鍑?
        #     async for event in runner.run_async(
        #         user_id=USER_ID,
        #         session_id=SESSION_ID,
        #         new_message=content,
        #         run_config=run_config
        #     ):
        #         if event.content and event.content.parts and event.content.parts[0].text:
        #             current_text = event.content.parts[0].text
        #             print(current_text, end="", flush=True)  # 鐩存帴杈撳嚭澧為噺
                
                    
        # except Exception as e:
        #     print(f"ADK thread execution failed: {e}")

    async def create_thread(
        self,
        account_id: Optional[str] = None,
        project_id: Optional[str] = None,
        is_public: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """鍒涘缓鏂扮嚎绋嬶紙涓?ThreadManager 淇濇寔鎺ュ彛涓€鑷达級

        Args:
            account_id: 璐︽埛ID
            project_id: 椤圭洰ID
            is_public: 鏄惁鍏紑
            metadata: 鍏冩暟鎹?

        Returns:
            绾跨▼ID
        """
        logger.debug(f"Creating new thread (account_id: {account_id}, project_id: {project_id}, is_public: {is_public})")
        client = await self.db.client

        # 鍑嗗绾跨▼鏁版嵁
        thread_data = {
            'is_public': is_public,
            'metadata': metadata or {}
        }

        # 娣诲姞鍙€夊瓧娈?
        if account_id:
            thread_data['account_id'] = account_id
        if project_id:
            thread_data['project_id'] = project_id

        try:
            # 鎻掑叆绾跨▼骞惰幏鍙栫嚎绋婭D
            result = await client.table('threads').insert(thread_data).execute()
            
            if result.data and len(result.data) > 0 and isinstance(result.data[0], dict) and 'thread_id' in result.data[0]:
                thread_id = result.data[0]['thread_id']
                logger.info(f"Successfully created thread: {thread_id}")
                return thread_id
            else:
                logger.error(f"Thread creation failed or did not return expected data structure. Result data: {result.data}")
                raise Exception("Failed to create thread: no thread_id returned")

        except Exception as e:
            logger.error(f"Failed to create thread: {str(e)}", exc_info=True)
            raise Exception(f"Thread creation failed: {str(e)}")

    async def add_message(
        self,
        thread_id: str,
        type: str,
        content: Union[Dict[str, Any], List[Any], str],
        is_llm_message: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        agent_version_id: Optional[str] = None
    ):
        """Add a message to the thread in the database.

        Args:
            thread_id: The ID of the thread to add the message to.
            type: The type of the message (e.g., 'text', 'image_url', 'tool_call', 'tool', 'user', 'assistant').
            content: The content of the message. Can be a dictionary, list, or string.
                     It will be stored as JSONB in the database.
            is_llm_message: Flag indicating if the message originated from the LLM.
                            Defaults to False (user message).
            metadata: Optional dictionary for additional message metadata.
                      Defaults to None, stored as an empty JSONB object if None.
            agent_id: Optional ID of the agent associated with this message.
                     Stored directly in agent_id column.
            agent_version_id: Optional ID of the specific agent version used.
                             Stored directly in agent_version_id column.
        """
        logger.debug(f"Adding message of type '{type}' to thread {thread_id} (agent: {agent_id}, version: {agent_version_id})")
        client = await self.db.client

        # 鍑嗗鎻掑叆鏁版嵁 - 鏍规嵁messages琛ㄧ殑瀹為檯缁撴瀯
        data_to_insert = {
            'thread_id': thread_id,
            'project_id': '00000000-0000-0000-0000-000000000000',  # 涓存椂浣跨敤榛樿project_id
            'type': type,
            'is_llm_message': is_llm_message,
            'role': 'assistant' if type == 'assistant' else 'user' if type == 'user' else 'system',
            'content': json.dumps(content) if isinstance(content, (dict, list)) else str(content),
            'metadata': json.dumps(metadata) if metadata else '{}',
        }
        
        # 鐩存帴娣诲姞agent淇℃伅鍒板瓧娈典腑
        if agent_id:
            data_to_insert['agent_id'] = agent_id
        if agent_version_id:
            data_to_insert['agent_version_id'] = agent_version_id

        try:
            # 鎻掑叆娑堟伅
            result = await client.table('messages').insert(data_to_insert)
            logger.info(f"Successfully added message to thread {thread_id}")

            if result.data and len(result.data) > 0 and isinstance(result.data[0], dict) and 'message_id' in result.data[0]:
                return result.data[0]
            
            else:
                logger.error(f"Insert operation failed or did not return expected data structure for thread {thread_id}. Result data: {result.data}")
                return None
        except Exception as e:
            logger.error(f"Failed to add message to thread {thread_id}: {str(e)}", exc_info=True)
            raise

