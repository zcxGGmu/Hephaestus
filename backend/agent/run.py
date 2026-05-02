import os
import json
import asyncio
import datetime
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass
import traceback


from agent.tools.message_tool import MessageTool
# from agent.tools.sb_deploy_tool import SandboxDeployTool
# from agent.tools.sb_expose_tool import SandboxExposeTool
# from agent.tools.sandbox_web_search_tool import SandboxWebSearchTool
from dotenv import load_dotenv # type: ignore
from utils.config import config
# from agent.agent_builder_prompt import get_agent_builder_prompt
from agentpress.thread_manager import ThreadManager
from agentpress.response_processor import ProcessorConfig
# from agent.tools.sb_shell_tool import SandboxShellTool
# from agent.tools.sb_files_tool import SandboxFilesTool
#from agent.tools.data_providers_tool import DataProvidersTool
# from agent.tools.expand_msg_tool import ExpandMessageTool
from agent.prompt import get_system_prompt
from agent.gemini_prompt import get_gemini_system_prompt
# from agent.custom_prompt import render_prompt_template
from utils.logger import logger
# from utils.auth_utils import get_account_id_from_thread
# from services.billing import check_billing_status
# from agent.tools.sb_vision_tool import SandboxVisionTool
# from agent.tools.sb_image_edit_tool import SandboxImageEditTool
# from agent.tools.sb_presentation_outline_tool import SandboxPresentationOutlineTool
# from agent.tools.sb_presentation_tool_v2 import SandboxPresentationToolV2
from services.langfuse import langfuse
try:
    from langfuse.client import StatefulTraceClient # type: ignore
except ImportError:
    # 瀵逛簬 langfuse 3.x 鐗堟湰锛屽皾璇曚笉鍚岀殑瀵煎叆璺緞
    try:
        from langfuse import StatefulTraceClient # type: ignore
    except ImportError:
        # 濡傛灉閮藉け璐ワ紝浣跨敤 Any 绫诲瀷
        from typing import Any
        StatefulTraceClient = Any

# from agent.tools.mcp_tool_wrapper import MCPToolWrapper
# from agent.tools.task_list_tool import TaskListTool
# from agentpress.tool import SchemaType
# from agent.tools.sb_sheets_tool import SandboxSheetsTool
# from agent.tools.sb_web_dev_tool import SandboxWebDevTool

load_dotenv()


@dataclass
class AgentConfig:
    thread_id: str
    project_id: str
    stream: bool
    native_max_auto_continues: int = 0
    max_iterations: int = 100
    model_name: str = "deepseek/deepseek-chat"
    enable_thinking: Optional[bool] = False
    reasoning_effort: Optional[str] = 'low'
    enable_context_manager: bool = True
    agent_config: Optional[dict] = None
    trace: Optional[StatefulTraceClient] = None # type: ignore
    is_agent_builder: Optional[bool] = False
    target_agent_id: Optional[str] = None


class ToolManager:
    def __init__(self, thread_manager: ThreadManager, project_id: str, thread_id: str):
        self.thread_manager = thread_manager
        self.project_id = project_id
        self.thread_id = thread_id
    
    def register_all_tools(self):
        # 娴嬭瘯鐜版湁宸ュ叿娉ㄥ唽娴佺▼
        logger.info("鎴戠幇鍦ㄥ紑濮嬪姞杞藉伐鍏凤紒锛侊紒锛?)
        from agent.tools.simple_test_tool import SimpleTestTool
        self.thread_manager.add_tool(SimpleTestTool)

        from agent.tools.task_list_tool import TaskListTool
        self.thread_manager.add_tool(TaskListTool, project_id=self.project_id, thread_manager=self.thread_manager, thread_id=self.thread_id)
        logger.info("Successfully registered task list tool: TaskListTool (with enhanced registry)")
        
        # from agent.tools.sandbox_web_search_tool import SandboxWebSearchTool
        # self.thread_manager.add_tool(SandboxWebSearchTool, project_id=self.project_id, thread_manager=self.thread_manager)

        # self.thread_manager.add_tool(SandboxShellTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxFilesTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxDeployTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxExposeTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxWebSearchTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxVisionTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxImageEditTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxPresentationOutlineTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxPresentationToolV2, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxSheetsTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(SandboxWebDevTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # if config.RAPID_API_KEY:
        #     self.thread_manager.add_tool(DataProvidersTool)
        

        
        # # Add Browser Tool
        # from agent.tools.browser_tool import BrowserTool
        # self.thread_manager.add_tool(BrowserTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
    
    def register_agent_builder_tools(self, agent_id: str):
        pass
        # from agent.tools.agent_builder_tools.agent_config_tool import AgentConfigTool
        # from agent.tools.agent_builder_tools.mcp_search_tool import MCPSearchTool
        # from agent.tools.agent_builder_tools.credential_profile_tool import CredentialProfileTool
        # from agent.tools.agent_builder_tools.workflow_tool import WorkflowTool
        # from agent.tools.agent_builder_tools.trigger_tool import TriggerTool
        # from services.postgresql import DBConnection
        
        # db = DBConnection()
        # self.thread_manager.add_tool(AgentConfigTool, thread_manager=self.thread_manager, db_connection=db, agent_id=agent_id)
        # self.thread_manager.add_tool(MCPSearchTool, thread_manager=self.thread_manager, db_connection=db, agent_id=agent_id)
        # self.thread_manager.add_tool(CredentialProfileTool, thread_manager=self.thread_manager, db_connection=db, agent_id=agent_id)
        # self.thread_manager.add_tool(WorkflowTool, thread_manager=self.thread_manager, db_connection=db, agent_id=agent_id)
        # self.thread_manager.add_tool(TriggerTool, thread_manager=self.thread_manager, db_connection=db, agent_id=agent_id)
    
    def register_custom_tools(self, enabled_tools: Dict[str, Any]):
        pass
        # self.thread_manager.add_tool(ExpandMessageTool, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # self.thread_manager.add_tool(MessageTool)
        # self.thread_manager.add_tool(TaskListTool, project_id=self.project_id, thread_manager=self.thread_manager, thread_id=self.thread_id)

        # def safe_tool_check(tool_name: str) -> bool:
        #     try:
        #         if not isinstance(enabled_tools, dict):
        #             return False
        #         tool_config = enabled_tools.get(tool_name, {})
        #         if not isinstance(tool_config, dict):
        #             return bool(tool_config) if isinstance(tool_config, bool) else False
        #         return tool_config.get('enabled', False)
        #     except Exception:
        #         return False
        
        # if safe_tool_check('sb_shell_tool'):
        #     self.thread_manager.add_tool(SandboxShellTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_files_tool'):
        #     self.thread_manager.add_tool(SandboxFilesTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_deploy_tool'):
        #     self.thread_manager.add_tool(SandboxDeployTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_expose_tool'):
        #     self.thread_manager.add_tool(SandboxExposeTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('web_search_tool'):
        #     self.thread_manager.add_tool(SandboxWebSearchTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_vision_tool'):
        #     self.thread_manager.add_tool(SandboxVisionTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_presentation_tool'):
        #     self.thread_manager.add_tool(SandboxPresentationOutlineTool, project_id=self.project_id, thread_manager=self.thread_manager)
        #     self.thread_manager.add_tool(SandboxPresentationToolV2, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_image_edit_tool'):
        #     self.thread_manager.add_tool(SandboxImageEditTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_sheets_tool'):
        #     self.thread_manager.add_tool(SandboxSheetsTool, project_id=self.project_id, thread_manager=self.thread_manager)
        # if safe_tool_check('sb_web_dev_tool'):
        #     self.thread_manager.add_tool(SandboxWebDevTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)
        # if config.RAPID_API_KEY and safe_tool_check('data_providers_tool'):
        #     self.thread_manager.add_tool(DataProvidersTool)

        
        # if safe_tool_check('browser_tool'):
        #     from agent.tools.browser_tool import BrowserTool
        #     self.thread_manager.add_tool(BrowserTool, project_id=self.project_id, thread_id=self.thread_id, thread_manager=self.thread_manager)


# class MCPManager:
#     def __init__(self, thread_manager: ThreadManager, account_id: str):
#         self.thread_manager = thread_manager
#         self.account_id = account_id
    
#     async def register_mcp_tools(self, agent_config: dict) -> Optional[MCPToolWrapper]:
#         all_mcps = []
        
#         if agent_config.get('configured_mcps'):
#             all_mcps.extend(agent_config['configured_mcps'])
        
#         if agent_config.get('custom_mcps'):
#             for custom_mcp in agent_config['custom_mcps']:
#                 custom_type = custom_mcp.get('customType', custom_mcp.get('type', 'sse'))
                
#                 if custom_type == 'pipedream':
#                     if 'config' not in custom_mcp:
#                         custom_mcp['config'] = {}
                    
#                     if not custom_mcp['config'].get('external_user_id'):
#                         profile_id = custom_mcp['config'].get('profile_id')
#                         if profile_id:
#                             try:
#                                 from pipedream import profile_service
#                                 from uuid import UUID
                                
#                                 profile = await profile_service.get_profile(UUID(self.account_id), UUID(profile_id))
#                                 if profile:
#                                     custom_mcp['config']['external_user_id'] = profile.external_user_id
#                             except Exception as e:
#                                 logger.error(f"Error retrieving external_user_id from profile {profile_id}: {e}")
                    
#                     if 'headers' in custom_mcp['config'] and 'x-pd-app-slug' in custom_mcp['config']['headers']:
#                         custom_mcp['config']['app_slug'] = custom_mcp['config']['headers']['x-pd-app-slug']
                
#                 elif custom_type == 'composio':
#                     qualified_name = custom_mcp.get('qualifiedName')
#                     if not qualified_name:
#                         qualified_name = f"composio.{custom_mcp['name'].replace(' ', '_').lower()}"
                    
#                     mcp_config = {
#                         'name': custom_mcp['name'],
#                         'qualifiedName': qualified_name,
#                         'config': custom_mcp.get('config', {}),
#                         'enabledTools': custom_mcp.get('enabledTools', []),
#                         'instructions': custom_mcp.get('instructions', ''),
#                         'isCustom': True,
#                         'customType': 'composio'
#                     }
#                     all_mcps.append(mcp_config)
#                     continue
                
#                 mcp_config = {
#                     'name': custom_mcp['name'],
#                     'qualifiedName': f"custom_{custom_type}_{custom_mcp['name'].replace(' ', '_').lower()}",
#                     'config': custom_mcp['config'],
#                     'enabledTools': custom_mcp.get('enabledTools', []),
#                     'instructions': custom_mcp.get('instructions', ''),
#                     'isCustom': True,
#                     'customType': custom_type
#                 }
#                 all_mcps.append(mcp_config)
        
#         if not all_mcps:
#             return None
        
#         mcp_wrapper_instance = MCPToolWrapper(mcp_configs=all_mcps)
#         try:
#             await mcp_wrapper_instance.initialize_and_register_tools()
            
#             updated_schemas = mcp_wrapper_instance.get_schemas()
#             for method_name, schema_list in updated_schemas.items():
#                 for schema in schema_list:
#                     self.thread_manager.tool_registry.tools[method_name] = {
#                         "instance": mcp_wrapper_instance,
#                         "schema": schema
#                     }
            
#             logger.info(f"鈿?Registered {len(updated_schemas)} MCP tools (Redis cache enabled)")
#             return mcp_wrapper_instance
#         except Exception as e:
#             logger.error(f"Failed to initialize MCP tools: {e}")
#             return None


class PromptManager:
    @staticmethod
    # async def build_system_prompt(model_name: str, agent_config: Optional[dict], 
    #                               is_agent_builder: bool, thread_id: str, 
    #                               mcp_wrapper_instance: Optional[MCPToolWrapper]) -> dict:
    async def build_system_prompt(model_name: str, agent_config: Optional[dict], 
                                  is_agent_builder: bool, thread_id: str, ) -> dict:    
        if "gemini-2.5-flash" in model_name.lower() and "gemini-2.5-pro" not in model_name.lower():
            default_system_content = get_gemini_system_prompt()
        else:
            default_system_content = get_system_prompt()
        
        # if "anthropic" not in model_name.lower():
        #     sample_response_path = os.path.join(os.path.dirname(__file__), 'sample_responses/1.txt')
        #     with open(sample_response_path, 'r') as file:
        #         sample_response = file.read()
        #     default_system_content = default_system_content + "\n\n <sample_assistant_response>" + sample_response + "</sample_assistant_response>"
        
        # if is_agent_builder:
        #     system_content = get_agent_builder_prompt()
        # elif agent_config and agent_config.get('system_prompt'):
        #     system_content = render_prompt_template(agent_config['system_prompt'].strip())
        # else:
        #    system_content = default_system_content
        system_content = default_system_content
        # if agent_config and (agent_config.get('configured_mcps') or agent_config.get('custom_mcps')) and mcp_wrapper_instance and mcp_wrapper_instance._initialized:
        #     mcp_info = "\n\n--- MCP Tools Available ---\n"
        #     mcp_info += "You have access to external MCP (Model Context Protocol) server tools.\n"
        #     mcp_info += "MCP tools can be called directly using their native function names in the standard function calling format:\n"
        #     mcp_info += '<function_calls>\n'
        #     mcp_info += '<invoke name="{tool_name}">\n'
        #     mcp_info += '<parameter name="param1">value1</parameter>\n'
        #     mcp_info += '<parameter name="param2">value2</parameter>\n'
        #     mcp_info += '</invoke>\n'
        #     mcp_info += '</function_calls>\n\n'
            
        #     mcp_info += "Available MCP tools:\n"
        #     try:
        #         registered_schemas = mcp_wrapper_instance.get_schemas()
        #         for method_name, schema_list in registered_schemas.items():
        #             for schema in schema_list:
        #                 if schema.schema_type == SchemaType.OPENAPI:
        #                     func_info = schema.schema.get('function', {})
        #                     description = func_info.get('description', 'No description available')
        #                     mcp_info += f"- **{method_name}**: {description}\n"
                            
        #                     params = func_info.get('parameters', {})
        #                     props = params.get('properties', {})
        #                     if props:
        #                         mcp_info += f"  Parameters: {', '.join(props.keys())}\n"
                                
        #     except Exception as e:
        #         logger.error(f"Error listing MCP tools: {e}")
        #         mcp_info += "- Error loading MCP tool list\n"
            
        #     mcp_info += "\n馃毃 CRITICAL MCP TOOL RESULT INSTRUCTIONS 馃毃\n"
        #     mcp_info += "When you use ANY MCP (Model Context Protocol) tools:\n"
        #     mcp_info += "1. ALWAYS read and use the EXACT results returned by the MCP tool\n"
        #     mcp_info += "2. For search tools: ONLY cite URLs, sources, and information from the actual search results\n"
        #     mcp_info += "3. For any tool: Base your response entirely on the tool's output - do NOT add external information\n"
        #     mcp_info += "4. DO NOT fabricate, invent, hallucinate, or make up any sources, URLs, or data\n"
        #     mcp_info += "5. If you need more information, call the MCP tool again with different parameters\n"
        #     mcp_info += "6. When writing reports/summaries: Reference ONLY the data from MCP tool results\n"
        #     mcp_info += "7. If the MCP tool doesn't return enough information, explicitly state this limitation\n"
        #     mcp_info += "8. Always double-check that every fact, URL, and reference comes from the MCP tool output\n"
        #     mcp_info += "\nIMPORTANT: MCP tool results are your PRIMARY and ONLY source of truth for external data!\n"
        #     mcp_info += "NEVER supplement MCP results with your training data or make assumptions beyond what the tools provide.\n"
            
        #     system_content += mcp_info

        now = datetime.datetime.now(datetime.timezone.utc)
        datetime_info = f"\n\n=== CURRENT DATE/TIME INFORMATION ===\n"
        datetime_info += f"Today's date: {now.strftime('%A, %B %d, %Y')}\n"
        datetime_info += f"Current UTC time: {now.strftime('%H:%M:%S UTC')}\n"
        datetime_info += f"Current year: {now.strftime('%Y')}\n"
        datetime_info += f"Current month: {now.strftime('%B')}\n"
        datetime_info += f"Current day: {now.strftime('%A')}\n"
        datetime_info += "Use this information for any time-sensitive tasks, research, or when current date/time context is needed.\n"
        
        system_content += datetime_info

        return {"role": "system", "content": system_content}

class MessageManager:
    """
    娑堟伅绠＄悊鍣ㄧ被
    
    璐熻矗鏋勫缓涓存椂娑堟伅锛屽寘鎷祻瑙堝櫒鐘舵€佸拰鍥惧儚涓婁笅鏂囦俊鎭€?
    杩欎簺涓存椂娑堟伅浼氬湪AI澶勭悊鐢ㄦ埛璇锋眰鏃朵綔涓轰笂涓嬫枃淇℃伅鎻愪緵缁欐ā鍨嬨€?
    """
    
    def __init__(self, client, thread_id: str, model_name: str, trace: Optional[StatefulTraceClient]): # type: ignore
        """
        鍒濆鍖栨秷鎭鐞嗗櫒
        
        Args:
            client: 鏁版嵁搴撳鎴风锛岀敤浜庢煡璇㈡秷鎭〃
            thread_id: 绾跨▼ID锛岀敤浜庢爣璇嗙壒瀹氱殑瀵硅瘽绾跨▼
            model_name: 妯″瀷鍚嶇О锛岀敤浜庡垽鏂槸鍚︽敮鎸佸浘鍍忓鐞?
            trace: 杩借釜瀹㈡埛绔紝鐢ㄤ簬鏃ュ織璁板綍
        """
        self.client = client
        self.thread_id = thread_id
        self.model_name = model_name
        self.trace = trace
    
    async def build_temporary_message(self) -> Optional[dict]:
        """
        鏋勫缓涓存椂娑堟伅
        
        杩欎釜鏂规硶浼氾細
        1. 鑾峰彇鏈€鏂扮殑娴忚鍣ㄧ姸鎬佷俊鎭紙鍖呮嫭鎴浘锛?
        2. 鑾峰彇鏈€鏂扮殑鍥惧儚涓婁笅鏂囦俊鎭?
        3. 灏嗚繖浜涗俊鎭粍鍚堟垚涓€涓复鏃舵秷鎭紝渚汚I妯″瀷浣跨敤
        
        Returns:
            Optional[dict]: 鍖呭惈娴忚鍣ㄧ姸鎬佸拰鍥惧儚淇℃伅鐨勪复鏃舵秷鎭紝濡傛灉娌℃湁鐩稿叧淇℃伅鍒欒繑鍥濶one
        """
        temp_message_content_list = []  # 瀛樺偍涓存椂娑堟伅鐨勫唴瀹瑰垪琛?

        # 鑾峰彇鏈€鏂扮殑娴忚鍣ㄧ姸鎬佹秷鎭?
        latest_browser_state_msg = await self.client.table('messages').select('*').eq('thread_id', self.thread_id).eq('type', 'browser_state').order('created_at', desc=True).limit(1).execute()
        
        if latest_browser_state_msg.data and len(latest_browser_state_msg.data) > 0:
            try:
                # 瑙ｆ瀽娴忚鍣ㄧ姸鎬佸唴瀹?
                browser_content = latest_browser_state_msg.data[0]["content"]
                if isinstance(browser_content, str):
                    browser_content = json.loads(browser_content)
                
                # 鎻愬彇鎴浘淇℃伅
                screenshot_base64 = browser_content.get("screenshot_base64")  # Base64缂栫爜鐨勬埅鍥?
                screenshot_url = browser_content.get("image_url")  # 鎴浘鐨刄RL鍦板潃
                
                # 澶嶅埗娴忚鍣ㄧ姸鎬佹枃鏈紝绉婚櫎鎴浘鐩稿叧瀛楁
                browser_state_text = browser_content.copy()
                browser_state_text.pop('screenshot_base64', None)
                browser_state_text.pop('image_url', None)

                # 濡傛灉鏈夋祻瑙堝櫒鐘舵€佹枃鏈俊鎭紝娣诲姞鍒颁复鏃舵秷鎭腑
                if browser_state_text:
                    temp_message_content_list.append({
                        "type": "text",
                        "text": f"The following is the current state of the browser:\n{json.dumps(browser_state_text, indent=2)}"
                    })
                
                # 妫€鏌ユā鍨嬫槸鍚︽敮鎸佸浘鍍忓鐞嗭紙Gemini銆丄nthropic銆丱penAI锛?
                if 'gemini' in self.model_name.lower() or 'anthropic' in self.model_name.lower() or 'openai' in self.model_name.lower():
                    # 浼樺厛浣跨敤URL锛屽鏋滄病鏈夊垯浣跨敤Base64
                    if screenshot_url:
                        temp_message_content_list.append({
                            "type": "image_url",
                            "image_url": {
                                "url": screenshot_url,
                                "format": "image/jpeg"
                            }
                        })
                    elif screenshot_base64:
                        temp_message_content_list.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{screenshot_base64}",
                            }
                        })

            except Exception as e:
                logger.error(f"Error parsing browser state: {e}")

        # 鑾峰彇鏈€鏂扮殑鍥惧儚涓婁笅鏂囨秷鎭?
        latest_image_context_msg = await self.client.table('messages').select('*').eq('thread_id', self.thread_id).eq('type', 'image_context').order('created_at', desc=True).limit(1).execute()
        
        if latest_image_context_msg.data and len(latest_image_context_msg.data) > 0:
            try:
                # 瑙ｆ瀽鍥惧儚涓婁笅鏂囧唴瀹?
                image_context_content = latest_image_context_msg.data[0]["content"] if isinstance(latest_image_context_msg.data[0]["content"], dict) else json.loads(latest_image_context_msg.data[0]["content"])
                
                # 鎻愬彇鍥惧儚淇℃伅
                base64_image = image_context_content.get("base64")  # Base64缂栫爜鐨勫浘鍍?
                mime_type = image_context_content.get("mime_type")  # 鍥惧儚鐨凪IME绫诲瀷
                file_path = image_context_content.get("file_path", "unknown file")  # 鍥惧儚鏂囦欢璺緞

                # 濡傛灉鏈夊浘鍍忔暟鎹紝娣诲姞鍒颁复鏃舵秷鎭腑
                if base64_image and mime_type:
                    # 娣诲姞鍥惧儚鎻忚堪鏂囨湰
                    temp_message_content_list.append({
                        "type": "text",
                        "text": f"Here is the image you requested to see: '{file_path}'"
                    })
                    # 娣诲姞鍥惧儚URL
                    temp_message_content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                        }
                    })

                # 澶勭悊瀹屽浘鍍忎笂涓嬫枃鍚庯紝鍒犻櫎璇ユ秷鎭紙閬垮厤閲嶅浣跨敤锛?
                await self.client.table('messages').delete().eq('message_id', latest_image_context_msg.data[0]["message_id"]).execute()
                
            except Exception as e:
                logger.error(f"Error parsing image context: {e}")

        # 濡傛灉鏈変复鏃舵秷鎭唴瀹癸紝杩斿洖鏍煎紡鍖栫殑娑堟伅
        if temp_message_content_list:
            return {"role": "user", "content": temp_message_content_list}
        return None

class AgentRunner:

    def __init__(self, config: AgentConfig):
        self.config = config
    
    async def setup(self):
        try:
            if not self.config.trace:
                self.config.trace = langfuse.trace(name="run_agent", session_id=self.config.thread_id, metadata={"project_id": self.config.project_id})
                logger.info(f"Langfuse trace created successfully")
            else:
                logger.info(f"Using existing trace")
     
            # 浣跨敤 Google ADK 妗嗘灦鎵挎帴鏈嶅姟
            self.thread_manager = ADKThreadManager(
                        trace=self.config.trace, 
                        is_agent_builder=self.config.is_agent_builder or False, 
                        target_agent_id=self.config.target_agent_id, 
                        agent_config=self.config.agent_config
                    )
            logger.info(f"ADKThreadManager created successfully")

            # 鍒濆鍖栨暟鎹簱瀹㈡埛绔?
            self.client = await self.thread_manager.db.client
            logger.info(f"Database client initialized successfully")

            # 鑾峰彇璐︽埛ID
            from utils.auth_utils import AuthUtils
            self.account_id = await AuthUtils.get_account_id_from_thread(self.client, self.config.thread_id)
            if not self.account_id: 
                raise ValueError("Could not determine account ID for thread")

            # 鑾峰彇椤圭洰淇℃伅
            project = await self.client.table('projects').select('*').eq('project_id', self.config.project_id).execute()
            if not project.data or len(project.data) == 0:
                raise ValueError(f"Project {self.config.project_id} not found")

            project_data = project.data[0]
            sandbox_info = project_data.get('sandbox', {})

            # 澶勭悊 sandbox_info 鍙兘鏄瓧绗︿覆鐨勬儏鍐?
            if isinstance(sandbox_info, str):
                try:
                    import json
                    sandbox_info = json.loads(sandbox_info)
                except (json.JSONDecodeError, TypeError):
                    sandbox_info = {}

            if not sandbox_info.get('id'):
                # 娌欑鏄噿鍔犺浇鐨勶紝褰撻渶瑕佹椂鍒涘缓鍜屾寔涔呭寲娌欑鍏冩暟鎹?
                # 濡傛灉娌欑涓嶅瓨鍦紝宸ュ叿浼氳皟鐢?`_ensure_sandbox()` 鏉ュ垱寤哄拰鎸佷箙鍖栨矙绠卞厓鏁版嵁
                logger.info(f"No sandbox found for project {self.config.project_id}; will create lazily when needed")
            
        except Exception as setup_error:
            logger.error(f"Error details: {traceback.format_exc()}")
            raise setup_error
        
    async def setup_tools(self):
        tool_manager = ToolManager(self.thread_manager, self.config.project_id, self.config.thread_id)
        if self.config.agent_config and self.config.agent_config.get('is_hephaestus_default', False):
            tool_manager.register_all_tools()
            logger.info("register all tools success锛?)

    
    def get_max_tokens(self) -> Optional[int]:
        if "sonnet" in self.config.model_name.lower():
            return 8192
        elif "gpt-4" in self.config.model_name.lower():
            return 4096
        elif "gemini-2.5-pro" in self.config.model_name.lower():
            return 64000
        elif "kimi-k2" in self.config.model_name.lower():
            return 8192
        return None
    
    
    async def run(self) -> AsyncGenerator[Dict[str, Any], None]:
        await self.setup()
        await self.setup_tools()

        # mcp_wrapper_instance = await self.setup_mcp_tools()
        
        # system_message = await PromptManager.build_system_prompt(
        #     self.config.model_name, self.config.agent_config, 
        #     self.config.is_agent_builder, self.config.thread_id, 
        #     mcp_wrapper_instance
        # )

        system_message = await PromptManager.build_system_prompt(
            self.config.model_name, self.config.agent_config, 
            self.config.is_agent_builder, self.config.thread_id, 
        )
        logger.info(f"system_message created successfully")

        # 鍒濆鍖栬凯浠ｆ鏁?
        iteration_count = 0

        # 鍒濆鍖栫户缁墽琛屾爣蹇?
        continue_execution = True

        # 鑾峰彇鏈€鏂版秷鎭?- 浠巈vents琛ㄨ幏鍙?
        latest_user_message = await self.client.table('events').select('*').eq('session_id', self.config.thread_id).order('timestamp', desc=True).limit(10).execute()
        logger.info(f"Event table query result: {len(latest_user_message.data) if latest_user_message.data else 0}")

        # 鎻愬彇鐢ㄦ埛璇锋眰鍐呭
        user_request = None
        if latest_user_message.data and len(latest_user_message.data) > 0:
            logger.info(f"Latest 10 messages author list: {[msg.get('author') for msg in latest_user_message.data]}")
            
            # 鎵惧埌鏈€鏂扮殑鐢ㄦ埛娑堟伅
            for i, event in enumerate(latest_user_message.data):
                if event.get('author') == 'user':
                    content = event.get('content', {})
                    timestamp = event.get('timestamp')
                    logger.info(f"Found user message[{i}]: content={content}, timestamp={timestamp}")
                    
                    import json
                    # 瑙ｆ瀽content瀛楁
                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except json.JSONDecodeError:
                            content = {"content": content}
                    
                    # 鎻愬彇鐢ㄦ埛璇锋眰
                    if isinstance(content, dict):
                        user_request = content.get('content', '')
                        logger.info(f"Extracted user request: {user_request}")
                    break
            
            if self.config.trace and user_request:
                self.config.trace.update(input=user_request)

        message_manager = MessageManager(self.client, self.config.thread_id, self.config.model_name, self.config.trace)

        # 杩涘叆寰幆鎵ц
        while continue_execution and iteration_count < self.config.max_iterations:
            iteration_count += 1          
            logger.info(f"Looping锛歝ontinue_execution={continue_execution}, iteration_count={iteration_count}, max_iterations={self.config.max_iterations}")
        
            temporary_message = await message_manager.build_temporary_message()
            logger.info(f"temporary_message created successfully: {temporary_message}")
            # max_tokens = self.get_max_tokens()
            
            generation = self.config.trace.generation(name="thread_manager.run_thread") if self.config.trace else None
            try:          
                # 鑾峰彇鍙敤鍑芥暟
                available_functions = self.thread_manager.tool_registry.get_available_functions()
                logger.info(f"Get available functions: {list(available_functions.keys())}")
                
                response = await self.thread_manager.run_thread( 
                        thread_id=self.config.thread_id,
                        system_prompt=system_message,
                        stream=self.config.stream,
                        llm_model=self.config.model_name,
                        llm_temperature=0,
                        # llm_max_tokens=max_tokens,
                        llm_max_tokens=1024,
                        tool_choice="auto",
                        available_functions = available_functions,
                        max_xml_tool_calls=0, # 杩欓噷涓嶈缃檺鍒?
                        temporary_message=temporary_message,
                        processor_config=ProcessorConfig(
                            xml_tool_calling=True,
                            native_tool_calling=False,
                            execute_tools=True,
                            execute_on_stream=True,
                            tool_execution_strategy="parallel",
                            xml_adding_strategy="user_message"
                        ),
                        native_max_auto_continues=self.config.native_max_auto_continues,
                        include_xml_examples=True,
                        enable_thinking=self.config.enable_thinking,
                        reasoning_effort=self.config.reasoning_effort,
                        enable_context_manager=self.config.enable_context_manager,
                        generation=generation
                    )
   
                if isinstance(response, dict) and "status" in response and response["status"] == "error":
                    yield response
                    break

                last_tool_call = None
                agent_should_terminate = False
                error_detected = False
                full_response = ""

                try:
                    if hasattr(response, '__aiter__') and not isinstance(response, dict):
                        all_chunk = []
                        index = 0
                        tool_call_assistant_map: Dict[str, str] = {}
                        async for chunk in response:
                            # 鎷嗗垎鍖呭惈澶氫釜 tool_calls 鐨勬渶缁?assistant 娑堟伅锛屽苟寤虹珛 tool_call_id 鈫?assistant_message_id 鐨勬槧灏?
                            try:
                                if isinstance(chunk, dict) and chunk.get('type') == 'assistant':
                                    metadata_obj = chunk.get('metadata', {})
                                    if isinstance(metadata_obj, str):
                                        try:
                                            metadata_obj = json.loads(metadata_obj)
                                        except Exception:
                                            metadata_obj = {}
                                    stream_status = metadata_obj.get('stream_status')
                                    if stream_status == 'complete':
                                        content_obj = chunk.get('content', '{}')
                                        if isinstance(content_obj, str):
                                            try:
                                                content_obj = json.loads(content_obj)
                                            except Exception:
                                                content_obj = {}
                                        tool_calls = content_obj.get('tool_calls') or []
                                        if isinstance(tool_calls, list) and len(tool_calls) > 0:
                                            from uuid import uuid4
                                            assistant_text = content_obj.get('content', '')
                                            from datetime import datetime, timezone, timedelta
                                            base_ts_str = chunk.get('created_at')
                                            try:
                                                base_dt = datetime.fromisoformat(base_ts_str) if isinstance(base_ts_str, str) else datetime.now(timezone.utc)
                                            except Exception:
                                                base_dt = datetime.now(timezone.utc)
                                            for i, tc in enumerate(tool_calls):
                                                # 馃敡 鐢熸垚纭畾鎬UID锛屼笌鍚庣鎷嗗垎閫昏緫淇濇寔涓€鑷?
                                                tool_call_id = tc.get('id') if isinstance(tc, dict) else f"unknown_{i}"
                                                import hashlib
                                                seed_data = f"assistant_split_{tool_call_id}_{self.config.thread_id}_{i}_v1"
                                                hash_object = hashlib.md5(seed_data.encode())
                                                hex_dig = hash_object.hexdigest()
                                                new_assistant_id = f"{hex_dig[:8]}-{hex_dig[8:12]}-{hex_dig[12:16]}-{hex_dig[16:20]}-{hex_dig[20:]}"
                                                
                                                new_content = {
                                                    "role": "assistant",
                                                    "content": assistant_text if i == 0 else "",
                                                    "tool_calls": [tc]
                                                }
                                                new_chunk = dict(chunk)
                                                new_chunk['message_id'] = new_assistant_id
                                                new_chunk['content'] = json.dumps(new_content)
                                                # 璁剧疆涓ユ牸閫掑鐨?created_at锛岄伩鍏嶅墠绔?key 鎶栧姩
                                                try:
                                                    new_dt = base_dt + timedelta(milliseconds=i)
                                                    new_chunk['created_at'] = new_dt.isoformat()
                                                except Exception:
                                                    pass
                                                # 涓烘瘡椤垫彁渚涚ǔ瀹氶『搴忓彿
                                                try:
                                                    metadata_copy = dict(metadata_obj) if isinstance(metadata_obj, dict) else {}
                                                    metadata_copy['tool_index'] = i
                                                    new_chunk['metadata'] = json.dumps(metadata_copy)
                                                except Exception:
                                                    pass
                                                # 璁板綍鏄犲皠锛屼緵鍚庣画 tool 缁撴灉閲嶅啓assistant_message_id
                                                try:
                                                    tool_call_id = tc.get('id') if isinstance(tc, dict) else None
                                                    if tool_call_id:
                                                        tool_call_assistant_map[tool_call_id] = new_assistant_id
                                                except Exception:
                                                    pass
                                                all_chunk.append({"index": index, "chunk": new_chunk})
                                                index += 1
                                                yield new_chunk
                                            # 涓嶅啀涓嬪彂鍘熷鐨勫悎骞禷ssistant锛岀洿鎺ヨ繘鍏ヤ笅涓€鏉hunk
                                            continue
                            except Exception:
                                pass

                            # 閲嶅啓姣忎釜宸ュ叿缁撴灉鐨?assistant_message_id锛屾寚鍚戝搴旀媶鍒嗗悗鐨?assistant 娑堟伅
                            try:
                                if isinstance(chunk, dict) and chunk.get('type') == 'tool':
                                    metadata_obj = chunk.get('metadata', {})
                                    if isinstance(metadata_obj, str):
                                        try:
                                            metadata_obj = json.loads(metadata_obj)
                                        except Exception:
                                            metadata_obj = {}
                                    tool_call_id = metadata_obj.get('tool_call_id') or metadata_obj.get('tool_call')
                                    mapped_assistant_id = tool_call_assistant_map.get(str(tool_call_id)) if tool_call_id else None
                                    if mapped_assistant_id:
                                        metadata_obj['assistant_message_id'] = mapped_assistant_id
                                        chunk['metadata'] = json.dumps(metadata_obj)
                            except Exception:
                                pass
                            if isinstance(chunk, dict) and chunk.get('type') == 'status' and chunk.get('status') == 'error':
                                error_detected = True
                                all_chunk.append({"index": index, "chunk": chunk})
                                index += 1
                                yield chunk
                                continue

                            if chunk.get('type') == 'status':
                                try:
                                    metadata = chunk.get('metadata', {})
                                    if isinstance(metadata, str):
                                        metadata = json.loads(metadata)
                                    content_obj = chunk.get('content', {})
                                    if isinstance(content_obj, str):
                                        try:
                                            content_obj = json.loads(content_obj)
                                        except Exception:
                                            content_obj = {}

                                    if metadata.get('agent_should_terminate'):
                                        agent_should_terminate = True
                                        if content_obj.get('function_name'):
                                            last_tool_call = content_obj['function_name']
                                        elif content_obj.get('xml_tag_name'):
                                            last_tool_call = content_obj['xml_tag_name']

                                    # 灏嗗寘鍚?tool_call_id 鐨勭姸鎬佹秷鎭篃琛ュ厖 assistant_message_id锛屼究浜庡墠绔寜椤垫洿鏂拌繘搴?
                                    tool_call_id_in_status = metadata.get('tool_call_id') or content_obj.get('tool_call_id')
                                    if tool_call_id_in_status:
                                        mapped_assistant_id = tool_call_assistant_map.get(str(tool_call_id_in_status))
                                        if mapped_assistant_id:
                                            metadata['assistant_message_id'] = mapped_assistant_id
                                            chunk['metadata'] = json.dumps(metadata)
                                except Exception:
                                    pass
                            
                            if chunk.get('type') == 'assistant' and 'content' in chunk:
                                try:
                                    content = chunk.get('content', '{}')
                                    if isinstance(content, str):
                                        assistant_content_json = json.loads(content)
                                    else:
                                        assistant_content_json = content

                                    assistant_text = assistant_content_json.get('content', '')
                                    full_response += assistant_text
                                    
                                    if isinstance(assistant_text, str):
                                        if '</ask>' in assistant_text or '</complete>' in assistant_text or '</web-browser-takeover>' in assistant_text:
                                            if '</ask>' in assistant_text:
                                                            xml_tool = 'ask'
                                            elif '</complete>' in assistant_text:
                                                            xml_tool = 'complete'
                                            elif '</web-browser-takeover>' in assistant_text:
                                                            xml_tool = 'web-browser-takeover'

                                            last_tool_call = xml_tool
                                    
                                except json.JSONDecodeError:
                                    pass
                                except Exception:
                                    pass

                            all_chunk.append({"index": index, "chunk": chunk})
                            index += 1
                            yield chunk
                    else:
                        error_detected = True

                    if error_detected:
                        if generation:
                            generation.end(output=full_response, status_message="error_detected", level="ERROR")
                        break
                        
                    if agent_should_terminate or last_tool_call in ['ask', 'complete', 'web-browser-takeover']:
                        if generation:
                            generation.end(output=full_response, status_message="agent_stopped")
                        continue_execution = False
                    else:
                        # 鉁?姝ｅ父瀹屾垚涓€杞璇濆悗锛屼篃瑕佺粓姝㈠惊鐜紙闄ら潪闇€瑕佺户缁墽琛屼换鍔★級
                        continue_execution = False

                except Exception as e:
                    error_msg = f"Error during response streaming: {str(e)}"
                    if generation:
                        generation.end(output=full_response, status_message=error_msg, level="ERROR")
                    yield {
                        "type": "status",
                        "status": "error", 
                        "message": error_msg
                    }
                    break
                     
            except Exception as e:
                error_msg = f"Error running thread: {str(e)}"
                yield {
                    "type": "status",
                    "status": "error", 
                    "message": error_msg
                }
                break
            
            if generation:
                generation.end(output=full_response)

        asyncio.create_task(asyncio.to_thread(lambda: langfuse.flush()))
        #         if isinstance(response, dict) and "status" in response and response["status"] == "error":
        #             yield response
        #             break

        #         last_tool_call = None
        #         agent_should_terminate = False
        #         error_detected = False
        #         full_response = ""
        #         final_response_text = None  # 鉁?鐢ㄤ簬瀛樺偍is_final_response鐨勫唴瀹?
        #         adk_call_completed = False  # 鉁?鏍囪鍗曟ADK璋冪敤鏄惁瀹屾垚

        #         try:
        #             all_chunk = []
        #             if hasattr(response, '__aiter__') and not isinstance(response, dict):
        #                 async for chunk in response:
        #                     print(f"current chunk: {chunk}")
        #                     # 鉁?鍩轰簬瀹為檯浜嬩欢鏍煎紡鐨勫鐞嗛€昏緫
        #                     if isinstance(chunk, dict):
        #                         chunk_type = chunk.get('type')
        #                         chunk_content = chunk.get('content', '{}')
        #                         chunk_metadata = chunk.get('metadata', '{}')
                                
        #                         # 瑙ｆ瀽JSON瀛楃涓?
        #                         try:
        #                             if isinstance(chunk_content, str):
        #                                 content_data = json.loads(chunk_content)
        #                             else:
        #                                 content_data = chunk_content
                                        
        #                             if isinstance(chunk_metadata, str):
        #                                 metadata_data = json.loads(chunk_metadata)
        #                             else:
        #                                 metadata_data = chunk_metadata
        #                         except json.JSONDecodeError:
        #                             content_data = {}
        #                             metadata_data = {}
                                
        #                         # 鉁?妫€鏌ssistant娑堟伅鐨勫畬鎴愮姸鎬?
        #                         if chunk_type == 'assistant' and metadata_data.get('stream_status') == 'complete':
        #                             if content_data.get('content'):
        #                                 final_response_text = content_data['content']
        #                                 logger.info(f"馃幆 妫€娴嬪埌瀹屾暣assistant鍥炲: {final_response_text[:100]}...")
                                
        #                         # 鉁?妫€鏌inish鐘舵€侊紙绫讳技is_final_response锛?
        #                         elif chunk_type == 'status' and content_data.get('status_type') == 'finish':
        #                             if content_data.get('finish_reason') == 'final':
        #                                 logger.info(f"馃弫 妫€娴嬪埌final finish鐘舵€?)
        #                                 # 杩欒〃绀哄綋鍓嶅洖鍚堢殑鏈€缁堝搷搴?
                                
        #                         # 鉁?妫€鏌hread_run_end锛堣皟鐢ㄥ畬鍏ㄧ粨鏉燂級
        #                         elif chunk_type == 'status' and content_data.get('status_type') == 'thread_run_end':
        #                             logger.info(f"馃幆 妫€娴嬪埌thread_run_end锛孉DK璋冪敤瀹屽叏缁撴潫")
        #                             adk_call_completed = True
                                
        #                         # 鉁?妫€鏌ラ敊璇姸鎬?
        #                         elif chunk_type == 'status' and chunk.get('status') == 'error':
        #                             error_detected = True
        #                             yield chunk
        #                             continue
                        
        #                         # 鉁?妫€鏌ュ伐鍏疯皟鐢ㄥ拰缁堟鏉′欢 (濡傛灉杩樻湁鍏朵粬閫昏緫闇€瑕?
        #                         if chunk_type == 'assistant':
        #                             # 馃敡 浠嶢DK鏍煎紡涓纭彁鍙栨枃鏈?
        #                             assistant_text = ""
        #                             if content_data.get('content'):
        #                                 # 鏃ф牸寮忥細{"content": "text"}
        #                                 assistant_text = str(content_data['content'])
        #                             elif content_data.get('parts'):
        #                                 # ADK鏍煎紡锛歿"role": "model", "parts": [{"text": "..."}]}
        #                                 for part in content_data['parts']:
        #                                     if isinstance(part, dict) and 'text' in part:
        #                                         # 馃敡 淇锛氬畨鍏ㄥ鐞唒art['text']锛岄槻姝ist绫诲瀷瀵艰嚧鎷兼帴閿欒
        #                                         part_text = part['text']
        #                                         if isinstance(part_text, list):
        #                                             part_text = ''.join(str(item) for item in part_text)
        #                                         elif not isinstance(part_text, str):
        #                                             part_text = str(part_text)
        #                                         assistant_text += part_text
                                    
        #                             if assistant_text:
        #                                 # 馃敡 淇锛氱‘淇漟ull_response鎷兼帴鐨勭被鍨嬪畨鍏?
        #                                 if not isinstance(full_response, str):
        #                                     full_response = str(full_response)
        #                                 if not isinstance(assistant_text, str):
        #                                     assistant_text = str(assistant_text)
        #                                 full_response += assistant_text
                                    
        #                             # 妫€鏌ML宸ュ叿璋冪敤
        #                             if isinstance(assistant_text, str):
        #                                 if '</ask>' in assistant_text:
        #                                     last_tool_call = 'ask'
        #                                     agent_should_terminate = True
        #                                 elif '</complete>' in assistant_text:
        #                                     last_tool_call = 'complete' 
        #                                     agent_should_terminate = True
        #                                 elif '</web-browser-takeover>' in assistant_text:
        #                                     last_tool_call = 'web-browser-takeover'
        #                                     agent_should_terminate = True

        #                     yield chunk
                        
        #                 # 鉁?褰揳sync for寰幆缁撴潫鏃讹紝璇存槑浜嬩欢娴佽€楀敖
        #                 if not adk_call_completed:
        #                     adk_call_completed = True
        #                     logger.info(f"馃弫 ADK浜嬩欢娴佽€楀敖锛屽崟娆¤皟鐢ㄥ畬鎴?)

                      
        #             else:
        #                 error_detected = True
        #             logger.info(f"123all_chunk: {all_chunk}")    
        #         except Exception as stream_error:
        #             error_msg = f"Error during response streaming: {str(stream_error)}"
        #             logger.error(error_msg)
        #             if generation:
        #                 generation.end(output=full_response, status_message=error_msg, level="ERROR")
        #             yield {
        #                 "type": "status",
        #                 "status": "error",
        #                 "message": error_msg
        #             }
        #             break
                    
        #     except Exception as run_error:
        #         error_msg = f"Error running thread: {str(run_error)}"
        #         logger.error(error_msg)
        #         yield {
        #             "type": "status",
        #             "status": "error",
        #             "message": error_msg
        #         }
        #         break
            
        #     # 鉁?澶栧眰寰幆缁堟鍒ゆ柇锛堝熀浜庡疄闄呬簨浠讹級
        #     if error_detected:
        #         logger.info(f"馃毃 妫€娴嬪埌閿欒锛岀粓姝㈡墽琛?)
        #         if generation:
        #             generation.end(output=full_response, status_message="error_detected", level="ERROR")
        #         break
                
        #     # 鉁?鍩轰簬瀹為檯ADK浜嬩欢鐨勭粓姝㈠垽鏂?
        #     if agent_should_terminate or last_tool_call in ['ask', 'complete', 'web-browser-takeover']:
        #         logger.info(f"馃洃 Agent鏄庣‘缁堟: agent_should_terminate={agent_should_terminate}, last_tool_call={last_tool_call}")
        #         if generation:
        #             generation.end(output=full_response, status_message="agent_stopped")
        #         continue_execution = False
        #         logger.info(f"馃洃 璁剧疆continue_execution=False锛屽簲璇ラ€€鍑哄惊鐜?)
                
        #     elif adk_call_completed:
        #         # 鉁?ADK璋冪敤瀹屾垚鍚庯紝缁х画涓嬩竴娆¤凯浠ｈAgent鎵ц鏇村浠诲姟
        #         logger.info(f"鉁?ADK璋冪敤瀹屾垚锛岀户缁墽琛屾洿澶氫换鍔?(iteration {iteration_count}/{self.config.max_iterations})")
        #         if final_response_text:
        #             logger.info(f"馃摑 鏈疆鍝嶅簲棰勮: {final_response_text[:200]}...")
        #         # continue_execution淇濇寔True锛岃Agent缁х画鎵ц浠诲姟
                
        #     else:
        #         # 鉁?鍏朵粬鎯呭喌
        #         logger.info(f"鉂?鏈槑纭殑ADK鐘舵€?(completed={adk_call_completed}, final_text={bool(final_response_text)})锛岀户缁皾璇?)
            
        #     if generation:
        #         generation.end(output=full_response)

        # # 馃攳 寰幆缁撴潫鏃ュ織
        # logger.info(f"馃弫 Agent鎵ц寰幆缁撴潫: continue_execution={continue_execution}, iteration_count={iteration_count}")
        # logger.info(f"馃弫 鏈€缁堢姸鎬? max_iterations={self.config.max_iterations}")
        # #                     # 鉁?瀹樻柟鎺ㄨ崘锛氱敤is_final_response()鑾峰彇鏈€缁堝彲灞曠ず鏂囨湰
        # #                     if hasattr(chunk, 'is_final_response') and chunk.is_final_response():
        # #                         if hasattr(chunk, 'content') and chunk.content and hasattr(chunk.content, 'parts') and chunk.content.parts:
        # #                             final_response_text = chunk.content.parts[0].text
        # #                             logger.info(f"馃幆 妫€娴嬪埌final_response: {final_response_text[:100]}...")
                            
        # #                     if isinstance(chunk, dict) and chunk.get('type') == 'status' and chunk.get('status') == 'error':
        # #                         error_detected = True
        # #                         yield chunk
        # #                         continue
                            
        # #                     if chunk.get('type') == 'status':
        # #                         try:
        # #                             metadata = chunk.get('metadata', {})
        # #                             if isinstance(metadata, str):
        # #                                 metadata = json.loads(metadata)
                                    
        # #                             if metadata.get('agent_should_terminate'):
        # #                                 agent_should_terminate = True
                                        
        # #                                 content = chunk.get('content', {})
        # #                                 if isinstance(content, str):
        # #                                     content = json.loads(content)
                                        
        # #                                 if content.get('function_name'):
        # #                                     last_tool_call = content['function_name']
        # #                                 elif content.get('xml_tag_name'):
        # #                                     last_tool_call = content['xml_tag_name']
                                            
        # #                         except Exception:
        # #                             pass
                            
        # #                     if chunk.get('type') == 'assistant' and 'content' in chunk:
        # #                         try:
        # #                             content = chunk.get('content', '{}')
        # #                             if isinstance(content, str):
        # #                                 assistant_content_json = json.loads(content)
        # #                             else:
        # #                                 assistant_content_json = content

        # #                             assistant_text = assistant_content_json.get('content', '')
        # #                             full_response += assistant_text
        # #                             if isinstance(assistant_text, str):
        # #                                 if '</ask>' in assistant_text or '</complete>' in assistant_text or '</web-browser-takeover>' in assistant_text:
        # #                                    if '</ask>' in assistant_text:
        # #                                        xml_tool = 'ask'
        # #                                    elif '</complete>' in assistant_text:
        # #                                        xml_tool = 'complete'
        # #                                    elif '</web-browser-takeover>' in assistant_text:
        # #                                        xml_tool = 'web-browser-takeover'

        # #                                    last_tool_call = xml_tool
                                
        # #                         except json.JSONDecodeError:
        # #                             pass
        # #                         except Exception:
        # #                             pass

        # #                     yield chunk
                        
        # #                 # 鉁?褰揳sync for寰幆缁撴潫鏃讹紝璇存槑杩欐ADK璋冪敤鐨勪簨浠舵祦宸茶€楀敖
        # #                 adk_call_completed = True
        # #                 logger.info(f"馃弫 ADK浜嬩欢娴佽€楀敖锛屽崟娆¤皟鐢ㄥ畬鎴?)
                        
        # #             else:
        # #                 error_detected = True

        # #             if error_detected:
        # #                 logger.info(f"馃毃 妫€娴嬪埌閿欒锛岀粓姝㈡墽琛?)
        # #                 if generation:
        # #                     generation.end(output=full_response, status_message="error_detected", level="ERROR")
        # #                 break
                        
        # #             # 鉁?鍩轰簬瀹樻柟寤鸿鐨勫灞傚惊鐜粓姝㈠垽鏂?
        # #             if agent_should_terminate or last_tool_call in ['ask', 'complete', 'web-browser-takeover']:
        # #                 logger.info(f"馃洃 Agent鏄庣‘缁堟: agent_should_terminate={agent_should_terminate}, last_tool_call={last_tool_call}")
        # #                 if generation:
        # #                     generation.end(output=full_response, status_message="agent_stopped")
        # #                 continue_execution = False
        # #                 logger.info(f"馃洃 璁剧疆continue_execution=False锛屽簲璇ラ€€鍑哄惊鐜?)
        # #             elif adk_call_completed and final_response_text:
        # #                 # 鉁?ADK璋冪敤瀹屾垚涓旀湁鏈€缁堝搷搴旀枃鏈紝閫氬父琛ㄧず涓€杞畬鏁村璇濈粨鏉?
        # #                 logger.info(f"鉁?ADK璋冪敤瀹屾垚涓旀湁鏈€缁堝搷搴旓紝榛樿缁堟澶栧眰寰幆")
        # #                 logger.info(f"馃摑 鏈€缁堝搷搴旈瑙? {final_response_text[:200]}...")
        # #                 continue_execution = False
        # #             elif adk_call_completed and not final_response_text:
        # #                 # 鉁?ADK璋冪敤瀹屾垚浣嗘病鏈夋渶缁堝搷搴旀枃鏈紝鍙兘闇€瑕佺户缁?
        # #                 logger.info(f"鈿狅笍 ADK璋冪敤瀹屾垚浣嗘棤鏈€缁堝搷搴旀枃鏈紝缁х画涓嬩竴娆¤凯浠?)
        # #                 # continue_execution淇濇寔True锛岀户缁笅涓€娆¤凯浠?
        # #             else:
        # #                 # 鉁?鍏朵粬鎯呭喌锛屽彲鑳芥槸ADK鍐呴儴閿欒鎴栧紓甯哥姸鎬?
        # #                 logger.info(f"鉂?鏈槑纭殑ADK鐘舵€?(completed={adk_call_completed}, final_text={bool(final_response_text)})锛岀户缁皾璇?)

        # #         except Exception as e:
        # #             error_msg = f"Error during response streaming: {str(e)}"
        # #             if generation:
        # #                 generation.end(output=full_response, status_message=error_msg, level="ERROR")
        # #             yield {
        # #                 "type": "status",
        # #                 "status": "error",
        # #                 "message": error_msg
        # #             }
        # #             break
                    
        # #     except Exception as e:
        # #         error_msg = f"Error running thread: {str(e)}"
        # #         yield {
        # #             "type": "status",
        # #             "status": "error",
        # #             "message": error_msg
        # #         }
        # #         break
            
        # #     if generation:
        # #         generation.end(output=full_response)

        # # # 馃攳 寰幆缁撴潫鏃ュ織
        # # logger.info(f"馃弫 Agent鎵ц寰幆缁撴潫: continue_execution={continue_execution}, iteration_count={iteration_count}")
        # # logger.info(f"馃弫 鏈€缁堢姸鎬? max_iterations={self.config.max_iterations}")

        # asyncio.create_task(asyncio.to_thread(lambda: langfuse.flush()))


    # async def run(self) -> AsyncGenerator[Dict[str, Any], None]:
        # """杩愯Agent锛屾敮鎸丄DK鍜孴hreadManager涓ょ妯″紡"""
        # print(f"馃殌 ===== AgentRunner.run()寮€濮嬫墽琛?=====")
        # try:
        #     # 妫€鏌ヤ娇鐢ㄥ摢绉嶆ā寮?
        #     if self.adk_runner and self.adk_session:
        #         print(f"  馃攧 浣跨敤ADK妯″紡鎵ц...")
        #         async for event in self._run_with_adk():
        #             yield event
        #     elif self.thread_manager:
        #         print(f"  馃攧 浣跨敤ThreadManager妯″紡鎵ц...")
        #         async for event in self._run_with_thread_manager():
        #             yield event
        #     else:
        #         raise RuntimeError("Neither ADK Runner nor ThreadManager initialized. Call setup() first.")
            
        #     print(f"  鉁?AgentRunner.run()鎵ц瀹屾垚")
            
        # except Exception as run_error:
        #     print(f"  鉂?AgentRunner.run()鎵ц澶辫触: {run_error}")
        #     print(f"  馃搵 閿欒璇︽儏: {traceback.format_exc()}")
        #     # 杩斿洖閿欒浜嬩欢
        #     yield {
        #         "type": "error",
        #         "content": f"Agent execution failed: {str(run_error)}",
        #         "metadata": {"error": str(run_error)}
        #     }
    
    async def _run_with_adk(self) -> AsyncGenerator[Dict[str, Any], None]:
        """浣跨敤ADK Runner鎵ц"""
        try:
            print(f"  馃摑 鍑嗗鐢ㄦ埛杈撳叆...")
            # 鍑嗗鐢ㄦ埛杈撳叆鍐呭
            user_content = types.Content(
                role='user',
                parts=[types.Part.from_text(text=self.config.user_message or "Hello")]
            )
            print(f"  鉁?鐢ㄦ埛杈撳叆鍑嗗瀹屾垚")
            
            print(f"  馃攧 寮€濮婣DK Runner鎵ц...")
            # 浣跨敤ADK Runner鎵ц
            async for event in self.adk_runner.run_async(
                user_id=self.adk_session.user_id,
                content=user_content,
                session_id=self.adk_session.id
            ):
                print(f"  馃摠 鏀跺埌ADK浜嬩欢: {event.type}")
                
                # 灏咥DK浜嬩欢杞崲涓轰綘鐨勬牸寮?
                converted_event = self._convert_adk_event_to_format(event)
                if converted_event:
                    yield converted_event
                
                # 妫€鏌ユ槸鍚﹀畬鎴?
                if event.type == "assistant_response_end":
                    print(f"  鉁?ADK鎵ц瀹屾垚")
                    break
                    
        except Exception as adk_error:
            print(f"  鉂?ADK鎵ц澶辫触: {adk_error}")
            yield {
                "type": "error",
                "content": f"ADK execution failed: {str(adk_error)}",
                "metadata": {"error": str(adk_error)}
            }
    
    async def _run_with_thread_manager(self) -> AsyncGenerator[Dict[str, Any], None]:
        """浣跨敤ThreadManager鎵ц锛堝洖閫€妯″紡锛?""
        try:
            print(f"  馃摑 鍑嗗ThreadManager鎵ц...")
            
            # 鏋勫缓涓存椂娑堟伅
            temporary_message = None
            if self.client:
                try:
                    message_manager = MessageManager(
                        self.client, 
                        self.config.thread_id, 
                        self.config.model_name, 
                        self.config.trace
                    )
                    temporary_message = await message_manager.build_temporary_message()
                    if temporary_message:
                        print(f"  鉁?涓存椂娑堟伅鏋勫缓鎴愬姛")
                    else:
                        print(f"  鈩癸笍 娌℃湁涓存椂娑堟伅")
                except Exception as msg_error:
                    print(f"  鈿狅笍 鏋勫缓涓存椂娑堟伅澶辫触: {msg_error}")
                    temporary_message = None
            
            # 鏋勫缓绯荤粺鎻愮ず
            system_prompt = PromptManager.build_system_prompt(
                model_name=self.config.model_name,
                agent_config=self.config.agent_config,
                is_agent_builder=self.config.is_agent_builder or False,
                thread_id=self.config.thread_id
            )
            
            # 浣跨敤鍘熸湁鐨凾hreadManager閫昏緫
            response = await self.thread_manager.run_thread(
                thread_id=self.config.thread_id,
                system_prompt=system_prompt,
                stream=self.config.stream,
                temporary_message=temporary_message,
                llm_model=self.config.model_name,
                enable_thinking=self.config.enable_thinking,
                reasoning_effort=self.config.reasoning_effort,
                enable_context_manager=self.config.enable_context_manager
            )
            
            # 澶勭悊鍝嶅簲
            if response:
                yield {
                    "type": "assistant",
                    "content": {"role": "assistant", "content": str(response)},
                    "metadata": {"thread_run_id": self.config.agent_run_id}
                }
            
            print(f"  鉁?ThreadManager鎵ц瀹屾垚")
            
        except Exception as tm_error:
            print(f"  鉂?ThreadManager鎵ц澶辫触: {tm_error}")
            yield {
                "type": "error",
                "content": f"ThreadManager execution failed: {str(tm_error)}",
                "metadata": {"error": str(tm_error)}
            }
    
    def _convert_adk_event_to_format(self, adk_event) -> Optional[Dict[str, Any]]:
        """灏咥DK浜嬩欢杞崲涓轰綘鐨勬牸寮?""
        try:
            if adk_event.type == "assistant_response_start":
                return {
                    "type": "status",
                    "content": {"status_type": "assistant_response_start"},
                    "metadata": {"thread_run_id": self.config.agent_run_id}
                }
            
            elif adk_event.type == "assistant_response":
                # 澶勭悊鍔╂墜鍝嶅簲
                content = adk_event.content
                if content and hasattr(content, 'parts'):
                    text_content = ""
                    for part in content.parts:
                        if hasattr(part, 'text'):
                            # 馃敡 纭繚绫诲瀷瀹夊叏锛岄槻姝㈠瓧绗︿覆鎷兼帴閿欒
                            part_text = part.text
                            if isinstance(part_text, list):
                                part_text = ''.join(str(item) for item in part_text)
                            elif not isinstance(part_text, str):
                                part_text = str(part_text)
                            text_content += part_text
                    
                    return {
                        "type": "assistant",
                        "content": {"role": "assistant", "content": text_content},
                        "metadata": {"stream_status": "chunk", "thread_run_id": self.config.agent_run_id}
                    }
            
            elif adk_event.type == "tool_started":
                # 澶勭悊宸ュ叿璋冪敤
                return {
                    "type": "status",
                    "content": {
                        "role": "assistant",
                        "status_type": "tool_started",
                        "tool_name": adk_event.tool_name,
                        "tool_args": adk_event.tool_args
                    },
                    "metadata": {"thread_run_id": self.config.agent_run_id}
                }
            
            elif adk_event.type == "tool_result":
                # 澶勭悊宸ュ叿缁撴灉
                return {
                    "type": "tool",
                    "content": {
                        "role": "tool",
                        "tool_name": adk_event.tool_name,
                        "result": adk_event.result
                    },
                    "metadata": {"thread_run_id": self.config.agent_run_id}
                }
            
            elif adk_event.type == "assistant_response_end":
                # 澶勭悊鍝嶅簲缁撴潫
                return {
                    "type": "status",
                    "content": {"status_type": "assistant_response_end"},
                    "metadata": {"thread_run_id": self.config.agent_run_id}
                }
            
            return None
            
        except Exception as convert_error:
            print(f"  鈿狅笍 浜嬩欢杞崲澶辫触: {convert_error}")
            return None

from agentpress.adk_thread_manager import ADKThreadManager
from typing import  Union


async def run_agent(
    thread_id: str,
    project_id: str,
    stream: bool,
    # thread_manager: Optional[Union[ThreadManager, ADKThreadManager]] = None,  
    native_max_auto_continues: int = 0,
    max_iterations: int = 100,
    model_name: str = "deepseek/deepseek-chat",
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low',
    enable_context_manager: bool = True,
    agent_config: Optional[dict] = None,    
    trace: Optional[StatefulTraceClient] = None, # type: ignore
    is_agent_builder: Optional[bool] = False,
    target_agent_id: Optional[str] = None,
):
    logger.info(f"Using thread_id: {thread_id}")
    logger.info(f"Using project_id: {project_id}")
    logger.info(f"Using stream: {stream}")
    logger.info(f"Using model_name: {model_name}")
    if agent_config:
        logger.info(f"Using agent_config: {agent_config.get('name', 'Unknown')}")
    else:
        logger.info(f"Using agent_config: None")

    effective_model = model_name
    if model_name == "deepseek/deepseek-chat" and agent_config and agent_config.get('model'):
        effective_model = agent_config['model']
        logger.info(f"Using model from agent config: {effective_model}")
    elif model_name != "deepseek/deepseek-chat":
        logger.info(f"Using user-selected model: {effective_model}")
    else:
        logger.info(f"Using default model: {effective_model}")
    
    logger.info(f"Creating AgentConfig")

    config = AgentConfig(
        thread_id=thread_id,
        project_id=project_id,
        stream=stream,
        native_max_auto_continues=native_max_auto_continues, # 鎺у埗 AI Agent 鑷姩缁х画瀵硅瘽鐨勬渶澶ф鏁?
        max_iterations=max_iterations, # Agent 鏈€澶ц凯浠ｆ鏁?
        model_name=effective_model,
        enable_thinking=enable_thinking,  # 鏄惁鍚敤鎬濊€?
        reasoning_effort=reasoning_effort,  # 鎬濊€冨姏搴?
        enable_context_manager=enable_context_manager,
        agent_config=agent_config,  # Agent 閰嶇疆
        trace=trace,
        is_agent_builder=is_agent_builder,  # 鏄惁鏄?Agent 鏋勫缓鍣?
        target_agent_id=target_agent_id,  # 鐩爣 Agent ID
    )

    # 鍒涘缓 Runner 
    runner = AgentRunner(config)
    logger.info(f"AgentRunner created successfully: {runner}")
    
    try:
        logger.info(f"Starting to run runner.run()")
        async for chunk in runner.run():
            yield chunk
    except Exception as run_error:
        logger.error(f"runner.run() failed: {run_error}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise run_error
