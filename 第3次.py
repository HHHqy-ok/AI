import os
import time
import json
import http.client
from urllib.parse import urlparse
import subprocess

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

# ====================== 工具定义 ======================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "列出指定目录下的所有文件和文件夹",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要列出的目录路径，例如 D:\\test"
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
            "description": "在指定目录下创建一个新文件并写入内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "要创建的文件名，例如 test.txt"
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
            "description": "删除指定目录下的指定文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "要删除的文件名"
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
            "description": "重命名指定目录下的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "old_name": {
                        "type": "string",
                        "description": "原文件名"
                    },
                    "new_name": {
                        "type": "string",
                        "description": "新文件名"
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
            "description": "读取指定目录下文件的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "文件所在的目录路径"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "要读取的文件名"
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
            "description": "访问指定的网页URL并返回内容",
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
    }
]

# ====================== 通义千问专属系统提示词 ======================
def build_system_prompt(user_info):
    return f"""【最高优先级规则，必须严格遵守】
1.  绝对禁止提及"通义千问"、"阿里巴巴"、"我是AI助手"
2.  必须100%记住：用户叫{user_info}
3.  回答必须完全贴合用户问题，不能答非所问
4.  不能在回复中提及任何工具相关内容
5.  用户问"我是谁"时，必须回答"你是{user_info}"
6.  保持回答简洁准确

现在回答用户的问题："""

# ====================== 流式调用（通义千问专属适配） ======================
def call_llm_stream(env_vars, messages, user_info, is_tool_round=False):
    start_time = time.time()
    url = urlparse(env_vars['BASE_URL'])
    host = url.netloc
    path = "/v1/chat/completions"

    # 通义千问专属：用user角色发送系统提示
    system_msg = {"role": "user", "content": build_system_prompt(user_info)}
    final_messages = [system_msg] + messages

    data = {
        "model": env_vars["MODEL"],
        "messages": final_messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": int(env_vars.get("MAX_TOKENS", 2048)),
        "stream": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {env_vars.get('API_KEY', '')}"
    }

    timeout = int(env_vars.get('TIMEOUT', '120'))
    if url.scheme == 'https':
        conn = http.client.HTTPSConnection(host, timeout=timeout)
    else:
        conn = http.client.HTTPConnection(host, timeout=timeout)

    full_content = ""
    tool_calls = []

    try:
        conn.request("POST", path, json.dumps(data), headers)
        response = conn.getresponse()

        if not is_tool_round:
            print("🤖 AI 正在思考...", end="", flush=True)

        for line in response.fp:
            line = line.decode("utf-8").strip()
            if not line: continue
            if line.startswith("data: "):
                data_part = line[6:]
                if data_part == "[DONE]": break
                try:
                    jd = json.loads(data_part)
                    delta = jd["choices"][0]["delta"]
                    
                    if not is_tool_round and "content" in delta and delta["content"]:
                        token = delta["content"]
                        full_content += token
                        if not tool_calls:
                            if not full_content or len(full_content) == len(token):
                                print("\r" + " " * 20 + "\r", end="", flush=True)
                                print("🤖 AI 回复：", end="", flush=True)
                            print(token, end="", flush=True)
                    
                    if "tool_calls" in delta and delta["tool_calls"]:
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

        if not is_tool_round:
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

    timeout = int(env_vars.get('TIMEOUT', '120'))
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
    total_length = 0
    for message in messages:
        if "content" in message:
            total_length += len(message["content"])
        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                if "function" in tool_call:
                    if "name" in tool_call["function"]:
                        total_length += len(tool_call["function"]["name"])
                    if "arguments" in tool_call["function"]:
                        total_length += len(tool_call["function"]["arguments"])
    return total_length

# ====================== 按要求压缩：前70%压缩，后30%保留 ======================
def compress_chat_history(env_vars, messages):
    print("\n📝 检测到聊天历史过长，开始压缩...")
    
    total_messages = len(messages)
    if total_messages < 3:
        return messages
    
    # 计算分割点：前70%压缩，后30%保留
    compress_count = int(total_messages * 0.7)
    keep_count = total_messages - compress_count
    
    # 确保至少保留1条消息
    if keep_count < 1:
        keep_count = 1
        compress_count = total_messages - keep_count
    
    messages_to_compress = messages[:compress_count]
    messages_to_keep = messages[compress_count:]
    
    # 构建压缩请求
    compress_prompt = "请对以下聊天记录进行总结，保持关键信息完整，语言简洁：\n\n"
    for msg in messages_to_compress:
        if msg["role"] == "user":
            compress_prompt += f"用户：{msg['content']}\n"
        elif msg["role"] == "assistant":
            compress_prompt += f"助手：{msg['content']}\n"
        elif msg["role"] == "tool":
            compress_prompt += f"工具：{msg['content']}\n"
    
    compress_messages = [
        {"role": "system", "content": "你是一个聊天记录压缩助手，需要将长对话压缩为简洁的摘要，保留关键信息。"},
        {"role": "user", "content": compress_prompt}
    ]
    
    # 调用LLM进行压缩
    compressed_content = call_llm_non_stream(env_vars, compress_messages)
    
    if not compressed_content:
        print("❌ 压缩失败，保留原聊天记录")
        return messages
    
    # 构建新的消息列表：压缩摘要 + 保留的最新消息
    new_messages = [
        {"role": "assistant", "content": f"【聊天历史摘要】\n{compressed_content}"}
    ] + messages_to_keep
    
    print(f"✅ 聊天历史压缩完成（前{compress_count}条压缩，后{keep_count}条保留）")
    return new_messages

# ====================== 自动提取用户身份 ======================
def extract_user_info(messages):
    for msg in reversed(messages):
        if msg["role"] == "user":
            content = msg["content"]
            if "我是" in content:
                return content.split("我是", 1)[1].strip()
            elif "我叫" in content:
                return content.split("我叫", 1)[1].strip()
    return "杰克"

# ====================== 保存聊天日志 ======================
def save_log(user_question, ai_answer, user_info):
    log_dir = r"D:\chat-log"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "log.txt")
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# 聊天历史\n")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"用户：{user_question}\n")
        f.write(f"AI：{ai_answer}\n")

# ====================== 主循环 ======================
def main():
    env_vars = load_env()
    if not env_vars: return

    print("=" * 50)
    print("✅ 通义千问专属工具助手已启动")
    print(f"模型：{env_vars['MODEL']}")
    print(f"地址：{env_vars['BASE_URL']}")
    print("=" * 50)

    messages = []
    chat_rounds = 0
    user_info = "杰克"

    while True:
        prompt = input("\n请输入问题（输入 exit 退出）：")
        if prompt.lower() == "exit": break

        messages.append({"role": "user", "content": prompt})
        chat_rounds += 1
        
        # 自动更新用户身份
        current_info = extract_user_info(messages)
        if current_info:
            user_info = current_info
        
        # 检查是否需要压缩聊天历史：超过5轮 或 上下文超过3K
        context_length = calculate_context_length(messages)
        if chat_rounds > 5 or context_length > 3000:
            messages = compress_chat_history(env_vars, messages)
            # 压缩后重置轮数，避免立即再次压缩
            chat_rounds = len(messages)

        while True:
            is_tool_round = any(msg.get("tool_calls") for msg in messages[-2:])
            content, tool_calls, total, duration, speed = call_llm_stream(env_vars, messages, user_info, is_tool_round)

            if not content and not tool_calls:
                break

            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    try:
                        params = json.loads(tc["function"]["arguments"])
                    except:
                        params = {}
                    
                    if tool_name == "list_files":
                        res = list_files(params.get("directory"))
                    elif tool_name == "rename_file":
                        res = rename_file(params.get("directory"), params.get("old_name"), params.get("new_name"))
                    elif tool_name == "delete_file":
                        res = delete_file(params.get("directory"), params.get("file_name"))
                    elif tool_name == "create_file":
                        res = create_file(params.get("directory"), params.get("file_name"), params.get("content", ""))
                    elif tool_name == "read_file":
                        res = read_file(params.get("directory"), params.get("file_name"))
                    elif tool_name == "curl_request":
                        res = curl_request(params.get("url"))
                    else:
                        res = json.dumps({"success": False, "error": "未知工具"}, ensure_ascii=False)
                    
                    messages.append({
                        "role": "assistant",
                        "tool_calls": [tc]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": res
                    })

                continue

            # 每轮都保存日志
            save_log(prompt, content, user_info)
            
            messages.append({"role": "assistant", "content": content})
            
            print("=" * 50)
            print(f"⏱ 耗时：{duration:.2f}s  |  📊 Tokens：{total}  |  ⚡ 速度：{speed:.2f} token/s")
            print("=" * 50)
            break

if __name__ == "__main__":
    main()