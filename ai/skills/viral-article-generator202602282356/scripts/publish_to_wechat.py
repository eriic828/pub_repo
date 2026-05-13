#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号发布脚本
使用绿联 API 将 HTML 文章发布到公众号草稿箱
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import requests


class WeChatPublisher:
    """绿联 API 发布器"""

    @staticmethod
    def _get_env_from_shell(var_name: str) -> Optional[str]:
        """从环境变量获取值

        Args:
            var_name: 环境变量名称

        Returns:
            环境变量值，不存在则返回 None

        说明：
            由于脚本从 zsh 终端运行，会自动继承 .zshrc 中配置的环境变量
            直接使用 os.getenv 即可获取
        """
        value = os.getenv(var_name)
        if value and value.strip():
            return value.strip()
        return None

    def __init__(self, api_key: Optional[str] = None):
        """初始化发布器

        Args:
            api_key: 绿联 API Key，默认从环境变量读取
        """
        self.api_key = api_key or self._get_env_from_shell("WECHAT_API_KEY")
        self.accounts_url = "https://wx.limyai.com/api/openapi/wechat-accounts"
        self.publish_url = "https://wx.limyai.com/api/openapi/wechat-publish"

        if not self.api_key:
            raise ValueError("请设置 WECHAT_API_KEY 环境变量（可在 ~/.zshrc 中添加: export WECHAT_API_KEY=your_key）")

    def get_accounts(self) -> Dict:
        """获取公众号列表

        Returns:
            公众号列表
        """
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        print("📋 获取公众号列表...")

        try:
            response = requests.post(self.accounts_url, headers=headers, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("success"):
                return result.get("data", {})
            else:
                raise Exception(f"获取公众号列表失败：{result}")
        except Exception as e:
            raise Exception(f"获取公众号列表失败：{e}")

    def parse_html_for_publish(self, html_file: Optional[Path] = None, html_content: Optional[str] = None, title_override: Optional[str] = None) -> Dict[str, str]:
        """解析 HTML，提取标题和内容

        Args:
            html_file: HTML 文件路径（可选）
            html_content: HTML 内容字符串（可选）
            title_override: 强制指定标题（可选，优先级最高）

        Returns:
            {'title': 提取的标题, 'content': 清理后的 HTML 内容}
        """
        # 参数校验：至少提供一个
        if not html_file and not html_content:
            raise ValueError("必须提供 html_file 或 html_content 参数")

        # 读取 HTML 内容
        if html_content:
            # 直接使用传入的 HTML 内容
            content_str = html_content
        else:
            # 从文件读取
            with open(html_file, 'r', encoding='utf-8') as f:
                content_str = f.read()

        # 使用 BeautifulSoup 解析 HTML
        from bs4 import BeautifulSoup
        import re
        soup = BeautifulSoup(content_str, 'html.parser')

        # 确定标题
        if title_override:
            # 优先使用强制指定的标题
            title = title_override
        elif html_file:
            # 从文件名提取标题（去掉日期前缀，如 20260227_）
            filename = html_file.stem
            title_match = re.match(r'^\d{8}_(.+)$', filename)
            if title_match:
                title = title_match.group(1)
            else:
                # 如果文件名不符合格式，尝试从 HTML 中提取
                title = ""
                for tag in ['h1', 'h2', 'h3']:
                    heading = soup.find(tag)
                    if heading:
                        title = heading.get_text(strip=True)
                        break

                # 如果还是没有找到，使用文件名
                if not title:
                    title = filename
        else:
            # 没有文件路径，从 HTML 中提取标题
            title = ""
            for tag in ['h1', 'h2', 'h3']:
                heading = soup.find(tag)
                if heading:
                    title = heading.get_text(strip=True)
                    break

            # 如果还是没有找到，使用默认标题
            if not title:
                title = "未命名文章"

        # 保留 body 内的内容（不移除任何标题标签）
        body = soup.find('body')
        if body:
            content = body.decode_contents().strip()
        else:
            content = content_str

        return {'title': title, 'content': content}

    def publish_article(
        self,
        html_file: Optional[Path] = None,
        html_content: Optional[str] = None,
        title_override: Optional[str] = None,
        author: str = "567",
        summary: str = "",
        wechat_appid: Optional[str] = None,
        content_format: str = "html",
        article_type: str = "news"
    ) -> Dict:
        """发布文章到公众号草稿箱

        Args:
            html_file: HTML 文件路径（可选，与 html_content 二选一）
            html_content: HTML 内容字符串（可选，与 html_file 二选一）
            title_override: 强制指定标题（可选，优先级最高）
            author: 作者，默认 "567"
            summary: 文章摘要，默认空
            wechat_appid: 公众号 App ID（可选）
            content_format: 内容格式，默认 "html"
            article_type: 文章类型，默认 "news"（图文）

        Returns:
            API 响应结果
        """
        print(f"\n📝 开始发布文章...")
        if html_file:
            print(f"HTML 文件: {html_file}")
        else:
            print(f"HTML 内容: 直接传入")
        print(f"作者: {author}")
        print(f"内容格式: {content_format}")
        print(f"文章类型: {article_type}")

        # 解析 HTML 内容
        print("\n📖 解析 HTML 内容...")
        parsed = self.parse_html_for_publish(html_file, html_content, title_override)
        title = parsed['title']
        content = parsed['content']

        print(f"✅ 标题: {title}")
        print(f"✅ 内容长度: {len(content)} 字符")

        # 如果没有指定 wechat_appid，尝试获取第一个可用公众号
        if not wechat_appid:
            print("\n📋 获取公众号信息...")
            accounts = self.get_accounts()
            accounts_list = accounts.get('accounts', [])

            if not accounts_list:
                raise Exception("没有可用的公众号，请先在绿联平台添加公众号")

            # 使用第一个可用的公众号
            first_account = accounts_list[0]
            wechat_appid = first_account.get('wechatAppid')
            account_name = first_account.get('name', '未知公众号')

            print(f"✅ 使用公众号: {account_name}")
            print(f"✅ AppID: {wechat_appid}")

        # 构建发布请求
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "wechatAppid": wechat_appid,
            "title": title,
            "content": content,
            "author": author,
            "summary": summary,
            "contentFormat": content_format,
            "articleType": article_type
        }

        print("\n📤 发送发布请求...")

        try:
            response = requests.post(
                self.publish_url,
                headers=headers,
                json=payload,
                timeout=180  # 增加超时时间到3分钟
            )

            # 打印详细的错误信息
            if response.status_code != 200:
                print(f"\n❌ HTTP 状态码: {response.status_code}")
                print(f"❌ 响应内容: {response.text}")

            response.raise_for_status()

            result = response.json()

            if result.get("success"):
                print("\n✅ 发布成功！")
                print("=" * 60)
                return result
            else:
                error_msg = result.get('message', '未知错误')
                print(f"\n❌ 发布失败：{error_msg}")
                print("=" * 60)
                return result

        except Exception as e:
            print(f"\n❌ 发布失败：{e}")
            print("=" * 60)
            raise


def main():
    """命令行接口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python publish_to_wechat.py <html文件>")
        print()
        print("选项:")
        print("  --author <作者>          作者，默认 '567'")
        print("  --appid <AppID>          公众号 App ID（可选）")
        print("  --summary <摘要>          文章摘要（可选）")
        print()
        print("示例:")
        print('  python publish_to_wechat.py article.html')
        print('  python publish_to_wechat.py article.html --author "张三"')
        print()
        print("编程接口使用:")
        print("  from publish_to_wechat import WeChatPublisher")
        print("  publisher = WeChatPublisher()")
        print("  # 方式1：使用文件路径")
        print('  publisher.publish_article(html_file=Path("article.html"))')
        print("  # 方式2：直接使用 HTML 内容")
        print('  publisher.publish_article(html_content="<p>文章内容</p>", title_override="文章标题")')
        print()
        print("环境变量:")
        print("  WECHAT_API_KEY: 绿联 API Key（必需）")
        sys.exit(1)

    html_file = Path(sys.argv[1])

    # 检查文件是否存在
    if not html_file.exists():
        print(f"❌ 错误：文件不存在: {html_file}")
        sys.exit(1)

    # 检查文件扩展名
    if html_file.suffix.lower() != '.html':
        print(f"⚠️  警告：输入文件不是 .html 格式: {html_file}")

    # 解析参数
    author = "567"
    wechat_appid = None
    summary = ""

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--author" and i + 1 < len(sys.argv):
            author = sys.argv[i + 1]
            i += 2
        elif arg == "--appid" and i + 1 < len(sys.argv):
            wechat_appid = sys.argv[i + 1]
            i += 2
        elif arg == "--summary" and i + 1 < len(sys.argv):
            summary = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # 发布文章
    try:
        publisher = WeChatPublisher()
        result = publisher.publish_article(
            html_file=html_file,
            author=author,
            summary=summary,
            wechat_appid=wechat_appid,
            content_format="html",
            article_type="news"
        )

        # 打印结果
        print("\n📊 发布结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        print(f"\n✅ 文章已发布到公众号草稿箱")
        print(f"🔗 请在微信公众号后台查看草稿箱")
        print(f"📱 草稿箱入口：内容管理 -> 草稿箱")

    except Exception as e:
        print(f"\n❌ 发布失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
