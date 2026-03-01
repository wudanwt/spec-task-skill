#!/usr/bin/env python3
"""
Team Skill Platform 同步脚本
用于将任务清单数据同步到效率追踪平台

用法:
    python sync.py -f 任务清单.md

配置优先级:
    1. 环境变量 (TEAM_SKILL_EMAIL, TEAM_SKILL_PASSWORD, TEAM_SKILL_API)
    2. 配置文件 (~/.gemini/antigravity/skills/spec-task/.sync_config.json)
    3. 交互式输入
"""
import argparse
import getpass
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ 缺少依赖：pip install requests")
    sys.exit(1)

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / ".sync_config.json"


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ 配置已保存到 {CONFIG_FILE}")
    except IOError as e:
        print(f"⚠️ 保存配置失败：{e}")


def get_credentials() -> tuple:
    """获取凭据（配置文件 > 交互式输入）"""
    api_base = 'http://localhost:8000/api'
    
    # 1. 尝试从配置文件获取
    config = load_config()
    if config.get('email') and config.get('password'):
        print(f"📁 使用配置文件凭据 ({config['email']})")
        return config['email'], config['password'], config.get('api', api_base)
    
    # 2. 交互式输入
    print("🔐 未找到配置，请输入登录信息：")
    sys.stdout.flush()
    
    email = input("  邮箱：").strip()
    sys.stdout.flush()
    
    password = getpass.getpass("  密码：")
    sys.stdout.flush()
    
    api_input = input(f"  API 地址 [{api_base}]: ").strip()
    if api_input:
        api_base = api_input
    sys.stdout.flush()
    
    # 询问是否保存
    save = input("  是否保存配置？(y/N): ").strip().lower()
    if save == 'y':
        save_config({
            'email': email,
            'password': password,
            'api': api_base
        })
    
    return email, password, api_base


def parse_task_list(content: str) -> list:
    """解析 任务清单.md 文件"""
    tasks = []
    current_section = None
    lines = content.split('\n')
    
    for line in lines:
        if '## 进行中' in line:
            current_section = 'in_progress'
        elif '## 已完成' in line:
            current_section = 'completed'
        elif line.startswith('## '):
            current_section = None
        
        if current_section and line.strip().startswith('- ['):
            task = parse_task_entry(line, lines, current_section)
            if task:
                tasks.append(task)
    
    return tasks


def parse_task_entry(line: str, all_lines: list, section: str) -> dict:
    """解析单个任务条目"""
    match = re.search(r'\*\*([^*]+)\*\*\s*-\s*(.+)', line)
    if not match:
        return None
    
    change_id = match.group(1).strip()
    title = match.group(2).strip()
    
    if '- [x]' in line:
        status = 'completed'
    elif '- [/]' in line:
        status = 'in_progress'
    else:
        status = 'pending'
    
    task = {
        'change_id': change_id,
        'title': title,
        'status': status,
        'complexity': 3,
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'interaction_count': 0,
        'rework_count': 0,
        'efficiency_score': None,
        'skill_name': None,
        'project_name': None
    }
    
    start_idx = all_lines.index(line)
    for i in range(start_idx + 1, min(start_idx + 15, len(all_lines))):
        detail_line = all_lines[i].strip()
        
        if detail_line.startswith('- [') or detail_line.startswith('##'):
            break
        
        if '开始时间:' in detail_line:
            time_match = re.search(r'开始时间:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', detail_line)
            if time_match:
                task['start_time'] = time_match.group(1).replace(' ', 'T') + ':00'
        
        if '完成时间:' in detail_line:
            time_match = re.search(r'完成时间:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', detail_line)
            if time_match:
                task['end_time'] = time_match.group(1).replace(' ', 'T') + ':00'
        
        if '复杂度:' in detail_line:
            stars = detail_line.count('⭐')
            if stars > 0:
                task['complexity'] = stars
        
        if '交互轮次:' in detail_line:
            count_match = re.search(r'交互轮次:\s*(\d+)', detail_line)
            if count_match:
                task['interaction_count'] = int(count_match.group(1))
        
        if '返工次数:' in detail_line:
            count_match = re.search(r'返工次数:\s*(\d+)', detail_line)
            if count_match:
                task['rework_count'] = int(count_match.group(1))
        
        if '效率得分:' in detail_line:
            score_match = re.search(r'效率得分:\s*([\d.]+)', detail_line)
            if score_match:
                task['efficiency_score'] = float(score_match.group(1))
        
        if 'Skill:' in detail_line or 'skill:' in detail_line:
            skill_match = re.search(r'Skill:\s*(.+)', detail_line, re.IGNORECASE)
            if skill_match:
                task['skill_name'] = skill_match.group(1).strip()
    
    return task


def main():
    parser = argparse.ArgumentParser(description='Team Skill Platform 任务同步')
    parser.add_argument('--file', '-f', required=True, help='任务清单文件路径')
    parser.add_argument('--clear-config', action='store_true', help='清除保存的配置')
    args = parser.parse_args()
    
    # 清除配置
    if args.clear_config:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            print("✅ 配置已清除")
        else:
            print("ℹ️ 无配置文件")
        return
    
    # 获取凭据
    email, password, api_base = get_credentials()
    
    if not email or not password:
        print("❌ 未提供凭据")
        sys.exit(1)
    
    # 读取任务清单
    task_file = Path(args.file)
    if not task_file.exists():
        print(f"❌ 文件不存在：{args.file}")
        sys.exit(1)
    
    content = task_file.read_text(encoding='utf-8')
    tasks = parse_task_list(content)
    
    if not tasks:
        print("⚠️ 未找到任务")
        return
    
    # 提取项目名称（从任务清单所在目录名）
    project_name = task_file.resolve().parent.name
    print(f"📁 项目：{project_name}")
    
    # 为所有任务设置项目名称
    for task in tasks:
        task['project_name'] = project_name
    
    print(f"📋 找到 {len(tasks)} 个任务")
    
    # 登录
    print("🔐 正在登录...")
    resp = requests.post(
        f"{api_base}/auth/login",
        data={"username": email, "password": password}
    )
    if resp.status_code != 200:
        detail = resp.json().get('detail', '未知错误') if resp.text else '连接失败'
        print(f"❌ 登录失败：{detail}")
        sys.exit(1)
    
    token = resp.json()['access_token']
    
    # 同步
    print("📤 正在同步...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{api_base}/tasks/sync",
        json={"tasks": tasks},
        headers=headers
    )
    
    if resp.status_code != 200:
        print(f"❌ 同步失败：{resp.text}")
        sys.exit(1)
    
    results = resp.json()
    print(f"✅ 已同步到 Team Skill Platform ({len(results)} 个任务)")


if __name__ == '__main__':
    main()
