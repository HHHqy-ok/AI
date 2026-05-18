import os
import time
import json
import http.client
from urllib.parse import urlparse
import subprocess

# 读取 .env 文件（和脚本同级目录）
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
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.dumps({"success": True, "content": result.stdout}, ensure_ascii=False)
        else:
            return json.dumps({"success": False, "error": result.stderr}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

# ====================== 工具定义（OpenAI标准格式） ======================
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

# ====================== 流式调用（自动HTTP/HTTPS切换版） ======================
def call_llm_stream(env_vars, messages):
    start_time = time.time()
    url = urlparse(env_vars['BASE_URL'])
    host = url.netloc
    path = "/v1/chat/completions"

    data = {
        "model": env_vars["MODEL"],
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": float(env_vars.get("TEMPERATURE", 0.7)),
        "max_tokens": int(env_vars.get("MAX_TOKENS", 2048)),
        "stream": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {env_vars.get('API_KEY', '')}"
    }

    # 🔴 核心修改：自动根据URL协议选择HTTP/HTTPS连接
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
                    
                    # 处理普通文本回复
                    if "content" in delta and delta["content"]:
                        if not tool_calls:  # 只有没有工具调用时才打印
                            print("\r" + " " * 20 + "\r", end="", flush=True)
                            print("🤖 AI 回复：", end="", flush=True)
                        token = delta["content"]
                        full_content += token
                        if not tool_calls:
                            print(token, end="", flush=True)
                    
                    # 处理工具调用（流式拼接）
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

# ====================== 主循环 ======================
def main():
    env_vars = load_env()
    if not env_vars: return

    print("=" * 50)
    print("✅ 本地大模型工具助手已启动（双模式兼容版）")
    print(f"模型：{env_vars['MODEL']}")
    print(f"地址：{env_vars['BASE_URL']}")
    print("=" * 50)

    messages = []

    while True:
        prompt = input("\n请输入问题（输入 exit 退出）：")
        if prompt.lower() == "exit": break

        messages.append({"role": "user", "content": prompt})

        while True:
            content, tool_calls, total, duration, speed = call_llm_stream(env_vars, messages)

            if not content and not tool_calls:
                break

            # 处理工具调用
            if tool_calls:
                print(f"\n🔧 检测到工具调用，共 {len(tool_calls)} 个")
                
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    try:
                        params = json.loads(tc["function"]["arguments"])
                    except:
                        params = {}
                    
                    print(f"   执行工具：{tool_name}")
                    
                    # 执行工具
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
                    
                    print(f"   ✅ 工具执行完成")
                    
                    # 将工具结果添加到消息历史
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

                # 继续调用模型，让它根据工具结果生成回答
                continue

            # 没有工具调用，结束本轮对话
            messages.append({"role": "assistant", "content": content})
            
            print("=" * 50)
            print(f"⏱ 耗时：{duration:.2f}s  |  📊 Tokens：{total}  |  ⚡ 速度：{speed:.2f} token/s")
            print("=" * 50)
            break

if __name__ == "__main__":
    main()