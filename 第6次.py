import os
import time
import json
import http.client
from urllib.parse import urlparse
import subprocess
import re

# 读取 .env 文件
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"❌ 错误: .env 文件不存在，请放在当前脚本同一文件夹下")
        return None
    
    env_vars = {}
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    required_vars = ['BASE_URL', 'MODEL', 'API_KEY']
    missing = [var for var in required_vars if var not in env_vars]
    if missing:
        print(f"❌ 错误: .env 文件缺少以下必填配置：{', '.join(missing)}")
        return None
    
    return env_vars

# ====================== 工具函数 ======================
def list_files(directory):
    try:
        files = []
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                file_info = {
                    "name": item,
                    "size": os.path.getsize(item_path),
                    "last_modified": os.path.getmtime(item_path),
                    "is_file": True
                }
            else:
                file_info = {"name": item, "is_file": False}
            files.append(file_info)
        return json.dumps({"success": True, "files": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def rename_file(directory, old_name, new_name):
    try:
        old_path = os.path.join(directory, old_name)
        new_path = os.path.join(directory, new_name)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            return json.dumps({"success": True, "message": f"文件已重命名为 {new_name}"}, ensure_ascii=False)
        else:
            return json.dumps({"success": False, "error": "文件不存在"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def delete_file(directory, file_name):
    try:
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return json.dumps({"success": True, "message": "文件已删除"}, ensure_ascii=False)
        else:
            return json.dumps({"success": False, "error": "文件不存在"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def create_file(directory, file_name, content=""):
    try:
        file_path = os.path.join(directory, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"success": True, "message": f"文件 {file_name} 已创建成功"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def read_file(directory, file_name):
    try:
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return json.dumps({"success": True, "content": content}, ensure_ascii=False)
        else:
            return json.dumps({"success": False, "error": "文件不存在"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def curl_request(url):
    try:
        result = subprocess.run(['curl', '-s', url], capture_output=True, timeout=30)
        if result.returncode == 0:
            try:
                content = result.stdout.decode('utf-8')
            except UnicodeDecodeError:
                content = result.stdout.decode('gbk', errors='replace')
            return json.dumps({"success": True, "content": content}, ensure_ascii=False)
        else:
            try:
                error = result.stderr.decode('utf-8')
            except UnicodeDecodeError:
                error = result.stderr.decode('gbk', errors='replace')
            return json.dumps({"success": False, "error": error}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def file_search(directory, keyword):
    """搜索指定目录下包含关键词的文件"""
    try:
        matches = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if keyword in content:
                            matches.append(file_path)
                except Exception:
                    continue
        
        return json.dumps({"success": True, "files": matches, "count": len(matches)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

# ====================== Skills 相关函数 ======================
def list_available_skills():
    try:
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agents', 'skills')
        
        if not os.path.exists(skills_dir):
            return json.dumps({"success": True, "skills": []}, ensure_ascii=False)
        
        skills = []
        
        for item in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, item)
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, 'SKILL.md')
                if os.path.exists(skill_file):
                    try:
                        with open(skill_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if front_matter_match:
                            front_matter = front_matter_match.group(1)
                            
                            name_match = re.search(r'name:\s*(.+)', front_matter)
                            desc_match = re.search(r'description:\s*(.+)', front_matter)
                            
                            if name_match:
                                skill_name = name_match.group(1).strip().strip('"\'')
                                skill_desc = desc_match.group(1).strip().strip('"\'') if desc_match else ""
                                
                                skills.append({
                                    "name": skill_name,
                                    "description": skill_desc
                                })
                    except Exception as e:
                        print(f"⚠️  读取技能 {item} 失败: {str(e)}")
                        continue
        
        return json.dumps({"success": True, "skills": skills}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

def load_skill_content(skill_name):
    try:
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agents', 'skills')
        
        if not os.path.exists(skills_dir):
            return json.dumps({"success": False, "error": "skills 目录不存在"}, ensure_ascii=False)
        
        for item in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, item)
            if os.path.isdir(skill_path):
                skill_file = os.path.join(skill_path, 'SKILL.md')
                if os.path.exists(skill_file):
                    try:
                        with open(skill_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if front_matter_match:
                            front_matter = front_matter_match.group(1)
                            
                            name_match = re.search(r'name:\s*(.+)', front_matter)
                            if name_match:
                                extracted_name = name_match.group(1).strip().strip('"\'')
                                if extracted_name == skill_name:
                                    body_content = content[front_matter_match.end():]
                                    return json.dumps({"success": True, "content": body_content}, ensure_ascii=False)
                    except Exception as e:
                        continue
        
        return json.dumps({"success": False, "error": f"未找到名为 {skill_name} 的技能"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

# ====================== 工具定义 ======================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出本地电脑指定目录下的所有文件和文件夹，仅当用户明确提到本地文件、电脑文件夹、磁盘路径时使用",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出的本地目录路径，例如 D:\\\\test"
                    }
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "在本地电脑指定目录下创建一个新文件并写入内容，仅用于本地文件操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "本地文件所在的目录路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "要创建的本地文件名，例如 test.txt"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的内容，默认为空字符串",
                        "default": ""
                    }
                },
                "required": ["directory", "file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "删除本地电脑指定目录下的指定文件，仅用于本地文件操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "本地文件所在的目录路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "要删除的本地文件名"
                    }
                },
                "required": ["directory", "file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "重命名本地电脑指定目录下的文件，仅用于本地文件操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "本地文件所在的目录路径"
                    },
                    "old_name": {
                        "type": "string",
                        "description": "原本地文件名"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "新本地文件名"
                    }
                },
                "required": ["directory", "old_name", "new_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取本地电脑指定目录下文件的内容，仅用于本地文件操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "本地文件所在的目录路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "要读取的本地文件名"
                    }
                },
                "required": ["directory", "file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "curl_request",
            "description": "访问指定的网页URL并返回内容，用于网络请求",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要访问的网页URL，例如 https://www.baidu.com"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "load_skill_content",
            "description": "加载指定技能的详细内容。当用户请求需要使用某个技能时，调用此函数获取该技能的完整说明",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "要加载的技能名称，例如 notice"
                    }
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "file_search",
            "description": "在指定目录下搜索包含关键词的文件，用于查找特定内容的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要搜索的本地目录路径，例如 D:\\\\test"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "要搜索的关键词，例如 def"
                    }
                },
                "required": ["directory", "keyword"]
            }
        }
    }
]

# ====================== 链式调用上下文管理器 ======================
class ChainedCallContext:
    def __init__(self, max_iterations=10):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.call_history = []
        self.variables = {}
    
    def add_call(self, tool_name, arguments, result):
        """记录一次工具调用和结果"""
        self.call_history.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "iteration": self.current_iteration
        })
    
    def set_variable(self, name, value):
        """设置上下文变量"""
        self.variables[name] = value
    
    def get_variable(self, name, default=None):
        """获取上下文变量"""
        return self.variables.get(name, default)
    
    def increment_iteration(self):
        """增加迭代次数"""
        self.current_iteration += 1
    
    def is_max_iterations_reached(self):
        """检查是否达到最大迭代次数"""
        return self.current_iteration >= self.max_iterations
    
    def get_history_summary(self):
        """获取调用历史摘要"""
        summary = []
        for call in self.call_history:
            summary.append(f"步骤{call['iteration']+1}: 调用 {call['tool_name']}({call['arguments']}) -> {call['result'][:100]}...")
        return "\n".join(summary)

# ====================== 分析提示词构建函数 ======================
def build_analysis_prompt(user_request, context):
    """构建链式调用分析提示词"""
    
    history_text = ""
    if context.call_history:
        history_text = "\n【已执行步骤】\n"
        for i, call in enumerate(context.call_history):
            history_text += f"{i+1}. 工具: {call['tool_name']}\n   参数: {json.dumps(call['arguments'], ensure_ascii=False)}\n   结果: {call['result']}\n\n"
    
    variables_text = ""
    if context.variables:
        variables_text = f"\n【上下文变量】\n{json.dumps(context.variables, ensure_ascii=False)}\n"
    
    return f"""你是一个智能工具调用助手，需要根据用户请求和已执行的步骤历史，决定下一步操作。

【用户请求】
{user_request}

{history_text}
{variables_text}

【决策规则】
1. 分析用户请求和已执行的步骤，判断是否需要继续调用工具
2. 如果任务已完成，直接总结结果
3. 如果需要继续执行，选择合适的工具进行调用
4. 可以使用上下文变量存储和传递中间结果
5. 前一个工具的输出可以作为后一个工具的输入参数

【输出格式要求】
请严格按照以下JSON格式输出：

1. 任务完成时：
{{"done": true, "answer": "最终回答内容"}}

2. 需要继续调用工具时：
{{"done": false, "tool_call": {{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}}}

【可用工具】
{json.dumps(TOOLS, ensure_ascii=False, indent=2)}

请直接输出JSON格式的决策结果，不要输出其他任何内容。"""

# ====================== 系统提示词（链式调用版） ======================
def build_chained_system_prompt():
    return """你是一个具备链式工具调用能力的智能助手。

【链式调用规则】
1. 你可以进行多步骤的工具调用，前一个工具的输出可以作为后一个工具的输入
2. 每次调用工具后，会获得中间结果，你需要根据中间结果决定下一步操作
3. 你可以使用上下文变量存储中间结果供后续步骤使用
4. 请仔细分析当前状态，判断是继续调用工具还是直接总结回答

【工具调用顺序依赖】
- file_search -> read_file: 先搜索包含关键词的文件，再读取内容
- list_files -> read_file: 先列出文件再读取
- read_file -> create_file: 先读取内容再写入新文件
- curl_request -> create_file: 先获取网页内容再保存到文件

【上下文变量使用方式】
- 使用 set_variable(key, value) 存储变量
- 使用 get_variable(key) 获取变量
- 变量可以在不同工具调用之间传递

【工具选择指南】
- 当用户说"查找"、"搜索"、"包含"、"关键词"时，使用 file_search 工具
- 当用户说"列出"、"目录"、"文件夹"时，使用 list_files 工具
- 当用户说"读取"、"打开"、"查看内容"时，使用 read_file 工具
- 当用户说"创建"、"写入"、"保存"、"生成"时，使用 create_file 工具
- 当用户说"访问"、"网页"、"URL"时，使用 curl_request 工具

【链式调用示例】
示例1：查找包含关键词的文件并总结
1. 调用 file_search 在指定目录搜索包含关键词的文件
2. 根据搜索结果，调用 read_file 读取相关文件内容
3. 总结文件内容给用户

示例2：查找文件并读取
1. 调用 list_files 获取目录下的文件列表
2. 根据结果决定读取哪些文件
3. 调用 read_file 读取文件内容
4. 总结内容给用户

示例3：网页内容保存
1. 调用 curl_request 获取网页内容
2. 调用 create_file 将内容保存到本地文件

请根据用户请求，智能规划工具调用链，直到完成任务。"""

# ====================== 非流式调用（用于链式调用决策） ======================
def call_llm_decision(env_vars, prompt):
    """调用LLM进行决策"""
    url = urlparse(env_vars['BASE_URL'])
    host = url.netloc
    path = "/v1/chat/completions"

    messages = [
        {"role": "system", "content": build_chained_system_prompt()},
        {"role": "user", "content": prompt}
    ]

    data = {
        "model": env_vars["MODEL"],
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2048,
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {env_vars.get('API_KEY', '')}"
    }

    timeout = int(env_vars.get('TIMEOUT', '180'))
    if url.scheme == 'https':
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, timeout=timeout)

    try:
        conn.request("POST", path, json.dumps(data), headers)
        response = conn.getresponse()
        response_data = json.loads(response.read().decode('utf-8'))
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"]
        return ""
    except Exception as e:
        print(f"❌ LLM调用失败：{str(e)}")
        return ""
    finally:
        conn.close()

# ====================== 执行工具调用 ======================
def execute_tool_call(tool_call):
    """执行工具调用，支持两种格式：
    1. 标准OpenAI格式: {"id": "...", "type": "function", "function": {"name": "...", "arguments": "..."}}
    2. 自定义格式: {"name": "...", "arguments": {...}}
    """
    try:
        # 尝试标准OpenAI格式
        if "function" in tool_call:
            function_name = tool_call["function"]["name"]
            args_str = tool_call["function"]["arguments"]
            # 尝试解析参数
            try:
                function_args = json.loads(args_str)
            except (json.JSONDecodeError, TypeError):
                function_args = args_str if isinstance(args_str, dict) else {}
        # 尝试自定义格式
        elif "name" in tool_call:
            function_name = tool_call["name"]
            function_args = tool_call.get("arguments", {})
            # 如果参数是字符串，尝试解析
            if isinstance(function_args, str):
                try:
                    function_args = json.loads(function_args)
                except json.JSONDecodeError:
                    function_args = {}
        else:
            return json.dumps({"success": False, "error": "无效的工具调用格式"}, ensure_ascii=False)
        
        function_map = {
            "list_files": list_files,
            "create_file": create_file,
            "delete_file": delete_file,
            "rename_file": rename_file,
            "read_file": read_file,
            "curl_request": curl_request,
            "load_skill_content": load_skill_content,
            "file_search": file_search
        }
        
        if function_name in function_map:
            return function_map[function_name](**function_args)
        else:
            return json.dumps({"success": False, "error": f"未知工具: {function_name}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": f"工具调用执行失败: {str(e)}"}, ensure_ascii=False)

# ====================== 链式调用执行函数 ======================
def execute_chained_tool_call(env_vars, user_request, max_iterations=10):
    """执行链式工具调用的完整流程"""
    print(f"🔗 开始链式工具调用，最大迭代次数: {max_iterations}")
    print(f"📝 用户请求: {user_request}")
    
    # 初始化上下文
    context = ChainedCallContext(max_iterations=max_iterations)
    
    # 循环执行
    while not context.is_max_iterations_reached():
        context.increment_iteration()
        print(f"\n--- 迭代 {context.current_iteration} ---")
        
        # 构建分析提示词
        prompt = build_analysis_prompt(user_request, context)
        
        # 调用LLM决定下一步操作
        print("🤔 正在分析决策...")
        response = call_llm_decision(env_vars, prompt)
        
        # 解析LLM响应
        try:
            # 尝试提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                decision = json.loads(response[json_start:json_end])
            else:
                decision = json.loads(response)
        except Exception as e:
            print(f"❌ 解析决策失败: {str(e)}")
            print(f"原始响应: {response}")
            return f"解析LLM响应失败: {str(e)}"
        
        print(f"📌 决策结果: {json.dumps(decision, ensure_ascii=False)}")
        
        # 检查是否完成
        if decision.get("done", False):
            answer = decision.get("answer", "")
            print(f"\n✅ 任务完成！\n最终回答: {answer}")
            return answer
        
        # 继续调用工具
        tool_call = decision.get("tool_call")
        if tool_call:
            tool_name = tool_call["name"]
            arguments = tool_call["arguments"]
            
            print(f"⚡ 执行工具调用: {tool_name}({json.dumps(arguments, ensure_ascii=False)})")
            result = execute_tool_call(tool_call)
            
            # 记录到上下文
            context.add_call(tool_name, arguments, result)
            
            # 尝试提取结果中的数据作为上下文变量
            try:
                result_data = json.loads(result)
                if result_data.get("success"):
                    # 根据工具类型提取有用信息
                    if tool_name == "list_files" and "files" in result_data:
                        context.set_variable("file_list", result_data["files"])
                    elif tool_name == "read_file" and "content" in result_data:
                        context.set_variable("last_read_content", result_data["content"])
                    elif tool_name == "curl_request" and "content" in result_data:
                        context.set_variable("last_curl_content", result_data["content"])
            except:
                pass
            
            print(f"📊 工具执行结果: {result[:200]}...")
        else:
            print("❌ 无效的工具调用指令")
            return "无效的工具调用指令"
    
    # 达到最大迭代次数
    print(f"\n⏰ 达到最大迭代次数 {max_iterations}，任务终止")
    return f"达到最大迭代次数 {max_iterations}，任务未完成"

# ====================== 系统提示词（LMStudio兼容版） ======================
def build_system_prompt(user_info, skills_json=None):
    skills_info = ""
    if skills_json:
        skills_info = f"\n\n【可用技能列表】\n{skills_json}\n\n【技能使用规则】\n- 当用户的请求与某个技能的描述匹配时，必须先调用 load_skill_content 函数加载该技能的完整内容\n- 加载技能内容后，严格按照技能的规则和要求执行任务\n- 不要猜测技能的规则，必须通过 load_skill_content 获取准确信息"
    
    return f"""【最高优先级规则】
1. 绝对禁止提及"通义千问"、"阿里巴巴"、"我是AI助手"
2. 用户叫{user_info}
3. 回答必须完全贴合用户问题，不能答非所问
4. 不能在回复中提及任何工具相关内容、接口、代码、日志底层信息
5. 用户问"我是谁"时，必须回答"你是{user_info}"
6. 用户问"你是谁"时，回答要友好自然
{skills_info}

【🔴 工具调用规则】
- 只有当用户明确提到"本地文件"、"电脑文件夹"、"D盘"、"C盘"时，才能使用本地文件工具
- 工具返回结果后，你**必须**直接把result字段的内容整理成通顺的中文回复用户
- 若工具返回失败，直接把result字段的错误信息告诉用户

【⚠️ 重要：LMStudio兼容说明】
- 当你看到工具返回的结果时，**必须立即生成回答**，不要再次调用工具
- 不要忽略工具返回的内容，必须基于工具结果进行回复
"""

# ====================== 流式调用（修复LMStudio兼容问题） ======================
def call_llm_stream(env_vars, messages, user_info, is_tool_result=False):
    start_time = time.time()
    url = urlparse(env_vars['BASE_URL'])
    host = url.netloc
    path = "/v1/chat/completions"

    skills_result = list_available_skills()
    skills_data = json.loads(skills_result)
    skills_json = None
    if skills_data.get("success"):
        skills_list = skills_data.get("skills", [])
        if skills_list:
            skills_json = json.dumps({"skills": skills_list}, ensure_ascii=False, indent=2)

    system_msg = {"role": "system", "content": build_system_prompt(user_info, skills_json)}
    final_messages = [system_msg] + messages

    data = {
        "model": env_vars["MODEL"],
        "messages": final_messages,
        "tools": TOOLS if not is_tool_result else None,
        "tool_choice": "auto" if not is_tool_result else "none",
        "temperature": 0.1,
        "max_tokens": int(env_vars.get("MAX_TOKENS", 2048)),
        "stream": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {env_vars.get('API_KEY', '')}"
    }

    timeout = int(env_vars.get('TIMEOUT', '180'))
    if url.scheme == 'https':
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, timeout=timeout)

    full_content = ""
    tool_calls = []

    try:
        conn.request("POST", path, json.dumps(data), headers)
        response = conn.getresponse()

        if not is_tool_result:
            print("AI 正在思考...", end="", flush=True)
        else:
            print("AI 正在整理回答...", end="", flush=True)

        for line in response.fp:
            line = line.decode("utf-8").strip()
            if not line: continue
            if line.startswith("data: "):
                data_part = line[6:]
                if data_part == "[DONE]": break
                try:
                    jd = json.loads(data_part)
                    delta = jd["choices"][0]["delta"]
                    
                    if "content" in delta and delta["content"]:
                        token = delta["content"]
                        full_content += token
                        if not tool_calls:
                            if not full_content or len(full_content) == len(token):
                                print("\r" + " " * 20 + "\r", end="", flush=True)
                                print("AI 回复：", end="", flush=True)
                            print(token, end="", flush=True)
                    
                    if not is_tool_result and "tool_calls" in delta and delta["tool_calls"]:
                        for tc in delta["tool_calls"]:
                            index = tc["index"]
                            if index >= len(tool_calls):
                                tool_calls.append({
                                    "id": tc.get("id", ""),
                                    "type": "function",
                                    "function": {
                                        "name": "",
                                        "arguments": ""
                                    }
                                })
                            if "function" in tc:
                                if "name" in tc["function"]:
                                    tool_calls[index]["function"]["name"] += tc["function"]["name"]
                                if "arguments" in tc["function"]:
                                    tool_calls[index]["function"]["arguments"] += tc["function"]["arguments"]
                except:
                    continue

        print("\n")
    except Exception as e:
        print(f"\n❌ 连接失败：{str(e)}")
        return None, None, 0, 0, 0
    finally:
        conn.close()

    duration = time.time() - start_time
    total_tokens = len(full_content) // 3
    speed = total_tokens / duration if duration > 0 else 0

    return full_content, tool_calls, total_tokens, duration, speed

# ====================== 非流式调用（专门用于压缩聊天记录） ======================
def call_llm_non_stream(env_vars, messages):
    start_time = time.time()
    url = urlparse(env_vars['BASE_URL'])
    host = url.netloc
    path = "/v1/chat/completions"

    data = {
        "model": env_vars["MODEL"],
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {env_vars.get('API_KEY', '')}"
    }

    timeout = int(env_vars.get('TIMEOUT', '180'))
    if url.scheme == 'https':
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, timeout=timeout)

    full_content = ""
    try:
        conn.request("POST", path, json.dumps(data), headers)
        response = conn.getresponse()
        response_data = json.loads(response.read().decode('utf-8'))
        if "choices" in response_data and len(response_data["choices"]) > 0:
            full_content = response_data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ 压缩失败：{str(e)}")
        return ""
    finally:
        conn.close()

    return full_content

# ====================== 计算聊天上下文长度 ======================
def calculate_context_length(messages):
    total_chars = 0
    for msg in messages:
        total_chars += len(msg.get("content", ""))
    return total_chars

# ====================== 压缩聊天记录 ======================
def compress_chat_history(env_vars, messages):
    if len(messages) < 6:
        return messages
    
    context_length = calculate_context_length(messages)
    if context_length < 3000:
        return messages
    
    print("\n📊 聊天记录较长，正在智能压缩...")
    
    split_point = int(len(messages) * 0.7)
    messages_to_compress = messages[:split_point]
    messages_to_keep = messages[split_point:]
    
    compression_prompt = [{"role": "system", "content": "请将以下对话历史压缩成一段简洁的摘要，保留关键信息和上下文。"}] + messages_to_compress
    
    summary = call_llm_non_stream(env_vars, compression_prompt)
    
    if summary:
        compressed_messages = [{"role": "system", "content": f"【历史对话摘要】{summary}"}] + messages_to_keep
        print(f"✅ 压缩完成：{len(messages)} 条消息 → {len(compressed_messages)} 条消息")
        return compressed_messages
    else:
        print("⚠️  压缩失败，保留原始记录")
        return messages

# ====================== 测试函数 ======================
def test_chained_calls():
    print("=== 链式工具调用测试 ===")
    
    env_vars = load_env()
    if not env_vars:
        print("❌ 无法加载环境变量")
        return
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 测试1：文件搜索链式调用
    print("\n--- 测试1：文件搜索链式调用 ---")
    test1_request = f"请查找 {current_dir} 目录下所有包含'def'关键词的文件，并总结这些文件的主要内容"
    result1 = execute_chained_tool_call(env_vars, test1_request)
    print(f"测试1结果: {result1}")
    
    # 测试2：多文件操作（需要创建测试文件）
    print("\n--- 测试2：多文件操作 ---")
    # 创建测试目录和文件
    test_dir = os.path.join(current_dir, "test_data")
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "1.txt"), 'w') as f:
        f.write("10")
    with open(os.path.join(test_dir, "2.txt"), 'w') as f:
        f.write("20")
    
    test2_request = f"读取{os.path.join(test_dir, '1.txt')} 和 {os.path.join(test_dir, '2.txt')} 两个文件，文件内容的都是正整数，把两个数相加的和写入 result.txt 文件。"
    result2 = execute_chained_tool_call(env_vars, test2_request)
    print(f"测试2结果: {result2}")
    
    # 测试3：网页处理链式调用
    print("\n--- 测试3：网页处理链式调用 ---")
    test3_request = f"访问 `https://www.nsu.edu.cn/HTML/news/2024/06/article3974.html` 并总结页面内容，保存到 {test_dir}/summary.txt"
    result3 = execute_chained_tool_call(env_vars, test3_request)
    print(f"测试3结果: {result3}")

# ====================== 主循环 ======================
def main():
    print("=== 本地大模型工具助手（支持链式工具调用） ===")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'test' 运行链式调用测试\n")
    
    env_vars = load_env()
    if not env_vars:
        return
    
    user_info = input("请输入你的名字：").strip()
    if not user_info:
        user_info = "用户"
    
    messages = []
    
    while True:
        try:
            user_input = input("\n你：").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break
            
            if user_input.lower() == 'test':
                test_chained_calls()
                continue
            
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            messages = compress_chat_history(env_vars, messages)
            
            full_content, tool_calls, total_tokens, duration, speed = call_llm_stream(env_vars, messages, user_info)
            
            if tool_calls:
                tool_results = []
                for tool_call in tool_calls:
                    result = execute_tool_call(tool_call)
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "content": result
                    })
                
                messages.append({"role": "assistant", "content": full_content if full_content else ""})
                messages.extend(tool_results)
                
                full_content, _, total_tokens, duration, speed = call_llm_stream(env_vars, messages, user_info, is_tool_result=True)
            
            if full_content:
                messages.append({"role": "assistant", "content": full_content})
                
                print(f"\n📊 统计信息：{total_tokens} tokens | {duration:.2f}秒 | {speed:.1f} tokens/秒")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误：{str(e)}")
            continue

if __name__ == "__main__":
    main()
