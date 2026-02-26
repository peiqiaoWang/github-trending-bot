#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Trending Bot - 每日自动推送 GitHub 热门项目到飞书
功能：
1. 爬取 GitHub Trending
2. 生成飞书文档
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


def create_feishu_document(repos, tenant_access_token):
    """
    创建飞书文档
    注意：此功能需要飞书开放平台应用的权限
    如果没有配置，将跳过文档创建
    """
    if not tenant_access_token:
        print("⚠️ 未配置 FEISHU_TENANT_ACCESS_TOKEN，跳过文档创建")
        return None
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 构建文档 Markdown 内容
    md_content = f"""# GitHub Trending 热门项目 - {date_str}

> 数据采集时间：{time_str} | 来源：[GitHub Trending](https://github.com/trending)

以下是今日 GitHub 最受关注的开源项目。

---

## 🏆 今日热门项目排行

| 排名 | 项目 | Stars | 今日新增 | 语言 |
|:---:|------|------:|--------:|:----:|
"""
    
    for repo in repos[:10]:
        md_content += f"| {repo['rank']} | ['name'][{repo}]({repo['url']}) | {repo['stars']} | {repo['today']} | {repo['language']} |\n"
    
    md_content += "\n---\n\n## 📊 项目详情\n\n"
    
    for repo in repos:
        md_content += f"""### {repo['rank']}. {repo['name']}
**🌟 {repo['stars']} Stars | 今日 {repo['today']} | {repo['language']}**

{repo['description']}

🔗 项目地址：{repo['url']}

---

"""
    
    md_content += "\n*本报告由 GitHub Trending Bot 自动生成*"
    
    # 创建飞书文档
    create_url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json"
    }
    
    # 创建空文档
    create_payload = {
        "title": f"GitHub Trending 热门项目 - {date_str}",
        "folder_token": ""  # 创建在根目录
    }
    
    try:
        response = requests.post(create_url, headers=headers, json=create_payload, timeout=30)
        result = response.json()
        
        if result.get("code") != 0:
            print(f"❌ 创建文档失败: {result}")
            return None
        
        document_id = result["data"]["document"]["document_id"]
        
        # 获取文档块 ID
        block_url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children"
        
        # 构建文档内容块
        blocks = []
        
        # 添加标题
        blocks.append({
            "block_type": 3,  # Heading1
            "heading1": {
                "elements": [{"text_run": {"content": f"GitHub Trending 热门项目 - {date_str}"}}]
            }
        })
        
        # 添加描述
        blocks.append({
            "block_type": 2,  # Text
            "text": {
                "elements": [{"text_run": {"content": f"数据采集时间：{time_str} | 来源：GitHub Trending"}}]
            }
        })
        
        # 添加表格数据作为文本
        for repo in repos[:10]:
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": ['rank']}. "}},
                        {"text_run": {"content": repo['name'], "text_element_style": {"bold": True}}},
                        {"text_run": {"content": f" - ⭐{repo['stars']} | 今日{repo['today']} | {repo['language']}"}},
                    ]
                }
            })
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": ['description'][:100] + "..." if len(repo['description']) > 100 else repo['description']}}]
                }
            })
        
        # 批量添加内容块
        batch_payload = {"children": blocks}
        response = requests.post(block_url, headers=headers, json=batch_payload, timeout=30)
        
        doc_url = f"https://bytedance.larkoffice.com/docx/{document_id}"
        print(f"✅ 文档创建成功: {doc_url}")
        return doc_url
        
    except Exception as e:
        print(f"❌ 创建文档出错: {e}")
        return None


def build_feishu_card(repos, doc_url=None):
    """构建飞书卡片消息"""
    
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 构建内容（Top 5 预览）
    content_lines = [f"📅 **更新时间**: {time_str}\n"]
    for repo in repos[:5]:
        line = f"**{repo['rank']}.** ['name'][{repo}]({repo['url']})\n"
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


def get_tenant_access_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    if not app_id or not app_secret:
        return None
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        if result.get("code") == 0:
            return result.get("tenant_access_token")
        else:
            print(f"⚠️ 获取 token 失败: {result}")
            return None
    except Exception as e:
        print(f"⚠️ 获取 token 出错: {e}")
        return None


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
    
    # 获取环境变量
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    
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
    
    # Step 2: 获取飞书 Token（可选）
    doc_url = None
    if app_id and app_secret:
        print("\n🔑 [2/4] 正在获取飞书访问令牌...")
        tenant_token = get_tenant_access_token(app_id, app_secret)
        
        if tenant_token:
            # Step 3: 创建飞书文档
            print("\n📄 [3/4] 正在创建飞书文档...")
            doc_url = create_feishu_document(repos, tenant_token)
        else:
            print("⚠️ 无法获取访问令牌，跳过文档创建")
    else:
        print("\n⚠️ [2/4] 未配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET，跳过文档创建")
        print("   如需自动生成飞书文档，请参考 README 配置应用凭证")
    
    # Step 4: 发送飞书消息
    print("\n📤 [4/4] 正在发送到飞书群...")
    message = build_feishu_card(repos, doc_url)
    result = send_to_feishu(message)
    
    print("\n" + "=" * 60)
    print("🎉 任务完成!")
    if doc_url:
        print(f"📄 文档地址: {doc_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
