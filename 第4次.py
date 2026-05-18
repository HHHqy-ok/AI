#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnythingLLM 桌面版 API 调用工具 - 最终修正版
"""

import urllib.request
import urllib.error
import json
import sys

class AnythingLLMClient:
    """AnythingLLM 桌面版客户端"""
    
    def __init__(self, base_url="http://127.0.0.1:3001", workspace=None, api_key=None):
        self.base_url = base_url
        self.workspace = workspace
        self.api_key = api_key
    
    def get_workspaces(self):
        """获取所有工作区 - 用于自动发现"""
        url = f"{self.base_url}/api/v1/workspaces"
        req = urllib.request.Request(url, method='GET')
        
        # 尝试添加API密钥（如果有）
        if self.api_key:
            req.add_header('Authorization', f'Bearer {self.api_key}')
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("⚠️ 需要API密钥认证")
            return None
        except Exception as e:
            print(f"❌ 获取工作区失败: {e}")
            return None
    
    def query(self, message, timeout=60):
        """发送查询到AnythingLLM"""
        
        if not self.workspace:
            print("❌ 未指定工作区，请先设置工作区名称")
            return None
        
        # 桌面版的正确API路径
        url = f"{self.base_url}/api/v1/workspace/{self.workspace}/chat"
        
        payload = {
            "message": message,
            "mode": "chat"
        }
        
        json_data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            method='POST'
        )
        
        # 添加API密钥认证（必需）
        if self.api_key:
            req.add_header('Authorization', f'Bearer {self.api_key}')
        
        print(f"\n📤 查询: {message}")
        print(f"📍 API: {url}")
        print(f"⏳ 等待响应...")
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                print(f"✅ 收到响应 (状态码: {response.status})")
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except:
                pass
            
            print(f"❌ HTTP错误 {e.code}")
            if e.code == 401:
                print("   API密钥无效或未提供")
                print("   请在AnythingLLM设置中生成API密钥")
            elif e.code == 404:
                print(f"   工作区 '{self.workspace}' 不存在")
                print("   请检查工作区名称是否正确")
            elif error_body:
                print(f"   详情: {error_body[:200]}")
            return None
            
        except urllib.error.URLError as e:
            print(f"❌ 连接错误: {e.reason}")
            return None
        except Exception as e:
            print(f"❌ 异常: {type(e).__name__}: {e}")
            return None
    
    def format_response(self, data):
        """格式化输出"""
        if not data:
            return "❌ 无响应数据"
        
        # 尝试多种可能的响应字段
        reply = None
        for field in ['textResponse', 'text', 'response', 'message']:
            if field in data:
                reply = data[field]
                break
        
        if not reply:
            reply = str(data)[:200]
        
        output = f"\n🤖 回复:\n{reply}"
        
        # 显示来源
        sources = data.get('sources', [])
        if sources:
            output += "\n\n📚 来源:"
            for src in sources[:3]:
                title = src.get('title', '未知')
                output += f"\n  - {title}"
        
        return output


def main():
    print("="*60)
    print("🤖 AnythingLLM 桌面版客户端 - 最终版")
    print("="*60)
    
    # ====== 请在这里填写你的配置 ======
    BASE_URL = "http://127.0.0.1:3001"
    API_KEY = "7CXA8FC-31BMD13-GNQYHKP-XN6J7MX"  # ⚠️ 重要：在AnythingLLM设置中生成API密钥后填在这里
    WORKSPACE = "ai"  # ⚠️ 重要：填写你的实际工作区名称
    # ================================
    
    # 先测试服务是否可访问
    print(f"\n🔌 测试服务: {BASE_URL}")
    try:
        req = urllib.request.Request(BASE_URL, method='GET')
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"✅ 服务可访问 (状态码: {resp.status})")
    except Exception as e:
        print(f"❌ 服务不可访问: {e}")
        print("\n请确保AnythingLLM已启动")
        return
    
    # 如果没有配置API密钥，提示用户
    if not API_KEY:
        print("\n⚠️ 未配置API密钥")
        print("\n请按以下步骤生成API密钥：")
        print("1. 在浏览器中打开 http://127.0.0.1:3001")
        print("2. 点击左下角设置图标（⚙️）")
        print("3. 找到 'API Keys' 选项")
        print("4. 点击 'Generate New Key' 生成密钥")
        print("5. 复制密钥，在代码中设置 API_KEY 变量")
        print("\n然后重新运行程序")
        return
    
    # 自动获取工作区列表
    print("\n🔍 正在获取工作区列表...")
    client = AnythingLLMClient(BASE_URL, None, API_KEY)
    workspaces = client.get_workspaces()
    
    if workspaces:
        print(f"✅ 找到工作区:")
        if isinstance(workspaces, list):
            for ws in workspaces:
                ws_name = ws.get('slug', ws.get('name', '未知'))
                print(f"   - {ws_name}")
            
            # 如果没指定工作区，使用第一个
            if not WORKSPACE and workspaces:
                WORKSPACE = workspaces[0].get('slug', workspaces[0].get('name'))
                print(f"\n💡 自动使用工作区: {WORKSPACE}")
    else:
        print("⚠️ 无法获取工作区列表")
        if not WORKSPACE:
            print("\n请手动指定工作区名称：")
            print("1. 在浏览器中打开 http://127.0.0.1:3001")
            print("2. 查看你的工作区名称")
            print("3. 在代码中设置 WORKSPACE 变量")
            return
    
    # 确认工作区已设置
    if not WORKSPACE:
        print("❌ 未指定工作区，无法继续")
        return
    
    # 创建客户端并测试
    client = AnythingLLMClient(BASE_URL, WORKSPACE, API_KEY)
    
    # 测试简单查询
    print("\n🔍 测试API调用...")
    test_result = client.query("你好", timeout=30)
    if test_result:
        print(client.format_response(test_result))
        print("\n✅ API测试成功！")
    else:
        print("\n❌ API测试失败")
        print("\n可能的原因：")
        print("1. API密钥无效")
        print("2. 工作区名称不正确")
        print("3. LLM模型未配置")
        return
    
    # 交互式对话
    print("\n" + "="*60)
    print("💬 开始对话 (输入 'exit' 退出)")
    print("="*60)
    
    while True:
        try:
            question = input("\n你: ").strip()
            if question.lower() in ['exit', 'quit']:
                print("👋 再见")
                break
            if not question:
                continue
            
            result = client.query(question, timeout=90)
            if result:
                print(client.format_response(result))
            else:
                print("\n❌ 查询失败")
                
        except KeyboardInterrupt:
            print("\n👋 再见")
            break


if __name__ == "__main__":
    main()