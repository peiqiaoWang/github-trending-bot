#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending Bot - 每日自动推送 GitHub 热门项目到飞书
功能：
1. 爬取 GitHub Trending
2. 生成飞书文档（可选）
3. 通过机器人发送卡片消息（含文档链接）
"""

import requests
from bs4 import BeautifulSoup
import os
import hashlib
import hmac
import base64
import time
import json
from datetime import datetime


def fetch_github_trending():
    """爬取 GitHub Trending 页面"""
    url = "https://github.com/trending"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    repos = []
    articles = soup.select('article.Box-row')
    
    for i, article in enumerate(articles[:15], 1):
        try:
            # 仓库名
            h2 = article.select_one('h2 a')
            if not h2:
                continue
            repo_path = h2.get('href', '').strip('/')
            repo_name = repo_path
            repo_url = f"https://github.com/{repo_path}"
            
            # 描述
            desc_elem = article.select_one('p')
            description = desc_elem.get_text(strip=True) if desc_elem else "暂无描述"
            
            # 语言
            lang_elem = article.select_one('[itemprop="programmingLanguage"]')
            language = lang_elem.get_text(strip=True) if lang_elem else "-"
            
            # Stars 总数
            stars_elems = article.select('a.Link--muted')
            stars = "0"
            if stars_elems:
                stars_text = stars_elems[0].get_text(strip=True)
                stars = stars_text.replace(',', '')
            
            # 今日新增
            today_elem = article.select_one('span.d-inline-block.float-sm-right')
            today_stars = today_elem.get_text(strip=True) if today_elem else "N/A"
            today_stars = today_stars.replace('stars today', '').replace('stars', '').strip()
            if today_stars and today_stars != "N/A":
                today_stars = f"+{today_stars}"
            
            repos.append({
                "rank": i,
                "name": repo_name,
                "url": repo_url,
                "description": description,
                "language": language,
                "stars": stars,
                "today": today_stars
            })
        except Exception as e:
            print(f"解析第 {i} 个仓库时出错: {e}")
            continue
    
    return repos


def build_feishu_card(repos, doc_url=None):
    """构建飞书卡片消息"""
    
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 构建内容（Top 5 预览）
    content_lines = [f"📅 **更新时间**: {time_str}\n"]
    for repo in repos[:5]:
        line = f"**{repo['rank']}.** [{repo['name']}]({repo['url']})\n"
        line += f"⭐ {repo['stars']} | 今日 {repo['today']} | {repo['language']}\n"
        desc = repo['description'][:40] + "..." if len(repo['description']) > 40 else repo['description']
        line += f"{desc}\n"
        content_lines.append(line)
    
    content = "\n".join(content_lines)
    
    # 构建元素列表
    elements = [
        {"tag": "markdown", "content": content},
        {"tag": "hr"}
    ]
    
    # 按钮组
    buttons = [
        {
            "tag": "button",
            "text": {"tag": "plain_text", "content": "🌐 GitHub Trending"},
            "url": "https://github.com/trending",
            "type": "default"
        }
    ]
    
    # 如果有文档链接，添加文档按钮
    if doc_url:
        buttons.insert(0, {
            "tag": "button",
            "text": {"tag": "plain_text", "content": "📄 查看完整报告"},
            "url": doc_url,
            "type": "primary"
        })
    
    elements.append({
        "tag": "action",
        "actions": buttons
    })
    
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"数据来源: GitHub Trending | {date_str} 自动推送"}]
    })
    
    card = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "🔥 GitHub Trending 今日热门"},
                "template": "blue"
            },
            "elements": elements
        }
    }
    return card


def gen_sign(timestamp, secret):
    """生成飞书签名"""
    string_to_sign = f'{timestamp}\n{secret}'
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), 
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign


def send_to_feishu(message):
    """发送消息到飞书群"""
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    secret = os.environ.get("FEISHU_SECRET", "")
    
    if not webhook_url:
        raise ValueError("❌ 错误: FEISHU_WEBHOOK_URL 环境变量未设置")
    
    if secret:
        timestamp = str(int(time.time()))
        sign = gen_sign(timestamp, secret)
        message["timestamp"] = timestamp
        message["sign"] = sign
    
    response = requests.post(
        webhook_url, 
        json=message,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    result = response.json()
    if result.get("code") == 0:
        print("✅ 消息发送成功!")
    else:
        print(f"❌ 发送失败: {result}")
    
    return result


def main():
    print("=" * 60)
    print("🚀 GitHub Trending Bot 启动")
    print("=" * 60)
    
    # Step 1: 爬取 GitHub Trending
    print("\n📡 [1/4] 正在爬取 GitHub Trending...")
    repos = fetch_github_trending()
    print(f"✅ 成功获取 {len(repos)} 个热门仓库")
    
    if not repos:
        print("❌ 未获取到任何仓库数据，退出")
        return
    
    print("\n📝 Top 5 项目预览:")
    for repo in repos[:5]:
        print(f"   {repo['rank']}. {repo['name']} - ⭐{repo['stars']} ({repo['today']})")
    
    # Step 2: 构建飞书消息（基础模式）
    print("\n📤 [2/4] 正在发送到飞书群...")
    message = build_feishu_card(repos)
    result = send_to_feishu(message)
    
    print("\n" + "=" * 60)
    print("🎉 任务完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
