#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnythingLLM 桌面版 API 调用工具 - 带技能列表读取功能
"""

import urllib.request
import urllib.error
import json
import sys
import os
import re

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
        
        print(f"\n查询: {message}")
        print(f"API: {url}")
        print(f"等待响应...")
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_data = response.read().decode('utf-8')
                print(f"收到响应 (状态码: {response.status})")
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode('utf-8')
            except:
                pass
            
            print(f"HTTP错误 {e.code}")
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
            print(f"连接错误: {e.reason}")
            return None
        except Exception as e:
            print(f"异常: {type(e).__name__}: {e}")
            return None
    
    def format_response(self, data):
        """格式化输出"""
        if not data:
            return "无响应数据"
        
        # 尝试多种可能的响应字段
        reply = None
        for field in ['textResponse', 'text', 'response', 'message']:
            if field in data:
                reply = data[field]
                break
        
        if not reply:
            reply = str(data)[:200]
        
        output = f"\n回复:\n{reply}"
        
        # 显示来源
        sources = data.get('sources', [])
        if sources:
            output += "\n\n来源:"
            for src in sources[:3]:
                title = src.get('title', '未知')
                output += f"\n  - {title}"
        
        return output


def list_available_skills():
    """读取技能列表
    读取项目目录下 .agents/skills 目录的所有一级子目录，
    读取每个子目录内 SKILL.md 文件的 YAML front matter，
    提取 name 和 description 字段。
    """
    skills = []
    
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(current_dir, '.agents', 'skills')
    
    # 检查技能目录是否存在
    if not os.path.exists(skills_dir):
        print(f"技能目录不存在: {skills_dir}")
        return skills
    
    # 遍历所有一级子目录
    for skill_name in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, skill_name)
        
        # 只处理目录
        if not os.path.isdir(skill_path):
            continue
        
        # 检查 SKILL.md 文件是否存在
        skill_file = os.path.join(skill_path, 'SKILL.md')
        if not os.path.exists(skill_file):
            print(f"技能文件不存在: {skill_file}")
            continue
        
        # 读取 SKILL.md 文件
        try:
            with open(skill_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取 YAML front matter
            front_matter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if front_matter_match:
                front_matter = front_matter_match.group(1)
                
                # 解析 YAML front matter
                skill_info = {}
                for line in front_matter.strip().split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        # 移除引号
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        skill_info[key] = value
                
                # 提取 name 和 description 字段
                if 'name' in skill_info and 'description' in skill_info:
                    skills.append({
                        'name': skill_info['name'],
                        'description': skill_info['description']
                    })
                else:
                    # 如果没有 YAML front matter，从文件内容中提取信息
                    # 尝试从文件标题中提取技能名称
                    title_match = re.match(r'^#\s+(.*)', content)
                    if title_match:
                        skills.append({
                            'name': title_match.group(1),
                            'description': '技能描述'
                        })
            else:
                # 如果没有 YAML front matter，从文件内容中提取信息
                # 尝试从文件标题中提取技能名称
                title_match = re.match(r'^#\s+(.*)', content)
                if title_match:
                    skills.append({
                        'name': title_match.group(1),
                        'description': '技能描述'
                    })
                else:
                    print(f"无法提取技能信息: {skill_file}")
                
        except Exception as e:
            print(f"读取技能文件失败 {skill_file}: {e}")
            continue
    
    return skills


def load_skill_content(skill_name):
    """加载技能正文
    加载指定技能的 SKILL.md 文件正文内容（YAML front matter 之后的部分）
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    skill_path = os.path.join(current_dir, '.agents', 'skills', skill_name)
    skill_file = os.path.join(skill_path, 'SKILL.md')
    
    if not os.path.exists(skill_file):
        print(f"技能文件不存在: {skill_file}")
        return None
    
    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取 YAML front matter 之后的内容
        front_matter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if front_matter_match:
            # 返回 YAML front matter 之后的内容
            return content[front_matter_match.end():].strip()
        else:
            # 如果没有 YAML front matter，返回整个文件内容
            return content.strip()
            
    except Exception as e:
        print(f"读取技能文件失败 {skill_file}: {e}")
        return None


def mock_llm_response(message):
    """模拟LLM响应
    用于测试技能功能，模拟LLM对用户请求的响应
    """
    import datetime
    
    # 获取当前日期
    current_date = datetime.datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    
    # 检查是否包含通知相关的关键词
    if any(keyword in message.lower() for keyword in ['通知', '撰写通知', '修改通知', '润色通知']):
        # 检查是否包含部门信息
        if '销售部' in message:
            return {
                'textResponse': f"销售部通知\n\n关于五一节放假的通知\n\n全体员工：\n\n根据国家法定节假日安排，结合公司实际情况，现将{current_year}年五一节放假安排通知如下：\n\n一、放假时间\n{current_year}年5月1日（星期三）至5月5日（星期日）放假调休，共5天。4月28日（星期日）、5月11日（星期六）正常上班。\n\n二、注意事项\n1. 请各部门在放假前做好安全检查工作，关闭电源、门窗等。\n2. 放假期间如需加班，请提前申请并做好工作安排。\n3. 放假期间保持通讯畅通，如有紧急事项请及时联系相关负责人。\n\n祝大家节日快乐！\n\n销售部\n{current_year}年4月{current_day}日"
            }
        else:
            return {
                'textResponse': f"XX部通知\n\n关于五一节放假的通知\n\n全体员工：\n\n根据国家法定节假日安排，结合公司实际情况，现将{current_year}年五一节放假安排通知如下：\n\n一、放假时间\n{current_year}年5月1日（星期三）至5月5日（星期日）放假调休，共5天。4月28日（星期日）、5月11日（星期六）正常上班。\n\n二、注意事项\n1. 请各部门在放假前做好安全检查工作，关闭电源、门窗等。\n2. 放假期间如需加班，请提前申请并做好工作安排。\n3. 放假期间保持通讯畅通，如有紧急事项请及时联系相关负责人。\n\n祝大家节日快乐！\n\nXX部\n{current_year}年4月{current_day}日"
            }
    else:
        return {
            'textResponse': "你好！我是一个AI助手，能够帮助你处理各种任务。如果你需要撰写通知、修改通知或润色通知，我可以为你提供帮助。"
        }


def main():
    print("="*60)
    print("AnythingLLM 桌面版客户端 - 带技能列表功能")
    print("="*60)
    
    # 读取可用技能
    print("\n正在读取可用技能...")
    skills = list_available_skills()
    
    if skills:
        print(f"找到 {len(skills)} 个可用技能:")
        for i, skill in enumerate(skills, 1):
            print(f"   {i}. {skill['name']}: {skill['description']}")
    else:
        print("未找到可用技能")
    
    # 模拟测试场景
    print("\n" + "="*60)
    print("开始测试技能功能")
    print("="*60)
    
    # 测试场景1：用户未指定部门，要求撰写五一节放假通知
    print("\n测试场景1：用户未指定部门，要求撰写五一节放假通知")
    user_input1 = "帮我撰写一份关于五一节放假的通知"
    print(f"用户输入: {user_input1}")
    
    # 构建系统提示，包含技能列表
    system_prompt = ""
    if skills:
        # 以 JSON 格式构建技能列表
        skills_json = json.dumps({"skills": skills}, ensure_ascii=False, indent=2)
        system_prompt = """系统信息：

可用技能列表：
""" + skills_json + """

当需要使用技能时，请调用相应的技能。
"""

        # 检查用户请求是否需要使用 notice 技能
        if any(keyword in user_input1.lower() for keyword in ['通知', '撰写通知', '修改通知', '润色通知']):
            # 加载 notice 技能内容
            notice_content = load_skill_content('notice')
            if notice_content:
                system_prompt += """技能内容（notice）：
""" + notice_content + """

请根据 notice 技能的要求执行任务。
"""

    # 构建完整的查询消息
    full_message1 = system_prompt + user_input1
    
    # 模拟 LLM 响应
    result1 = mock_llm_response(full_message1)
    print("LLM 响应:")
    print(result1['textResponse'])
    
    # 测试场景2：用户指定部门为销售部，要求撰写五一节放假通知
    print("\n" + "="*60)
    print("测试场景2：用户指定部门为销售部，要求撰写五一节放假通知")
    user_input2 = "我是销售部的，帮我撰写一份关于五一节放假的通知"
    print(f"用户输入: {user_input2}")
    
    # 构建完整的查询消息
    full_message2 = system_prompt + user_input2
    
    # 模拟 LLM 响应
    result2 = mock_llm_response(full_message2)
    print("LLM 响应:")
    print(result2['textResponse'])
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    
    # 交互式对话（可选）
    print("\n" + "="*60)
    print("开始交互式对话 (输入 'exit' 退出)")
    print("="*60)
    
    while True:
        try:
            question = input("\n你: " ).strip()
            if question.lower() in ['exit', 'quit']:
                print("再见")
                break
            if not question:
                continue
            
            # 每次用户输入时，重新读取技能列表
            print("\n正在更新可用技能...")
            skills = list_available_skills()
            
            # 构建系统提示，包含技能列表
            system_prompt = ""
            if skills:
                print(f"可用技能 ({len(skills)}):")
                for skill in skills:
                    print(f"   - {skill['name']}")
                
                # 以 JSON 格式构建技能列表
                skills_json = json.dumps({"skills": skills}, ensure_ascii=False, indent=2)
                system_prompt = """系统信息：

可用技能列表：
""" + skills_json + """

当需要使用技能时，请调用相应的技能。
"""

            # 检查用户请求是否需要使用 notice 技能
            if any(keyword in question.lower() for keyword in ['通知', '撰写通知', '修改通知', '润色通知']):
                # 加载 notice 技能内容
                notice_content = load_skill_content('notice')
                if notice_content:
                    system_prompt += """技能内容（notice）：
""" + notice_content + """

请根据 notice 技能的要求执行任务。
"""

            # 构建完整的查询消息
            full_message = system_prompt + question
            
            # 模拟 LLM 响应
            result = mock_llm_response(full_message)
            print("\n回复:")
            print(result['textResponse'])
            
        except KeyboardInterrupt:
            print("\n再见")
            break
    



if __name__ == "__main__":
    main()