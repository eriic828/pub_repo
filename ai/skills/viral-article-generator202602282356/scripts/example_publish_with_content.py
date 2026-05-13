#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示如何使用 HTML 内容直接发布到公众号
"""

from pathlib import Path
from publish_to_wechat import WeChatPublisher

# 示例 1：使用文件路径发布（原有方式，保持兼容）
def publish_from_file():
    """从文件路径发布"""
    publisher = WeChatPublisher()
    result = publisher.publish_article(
        html_file=Path("assets/articles/20260227_你的标题.html"),
        author="567"
    )
    print(result)


# 示例 2：直接使用 HTML 内容发布（新功能）
def publish_from_content():
    """直接使用 HTML 内容发布"""
    html_content = """
    <h3>AI 工具如何改变你的工作方式</h3>
    <p>这是第一段内容，介绍 AI 工具的重要性。</p>
    <p>这是第二段内容，提供具体的使用方法。</p>
    <p>这是第三段内容，总结全文并给出行动建议。</p>
    """

    publisher = WeChatPublisher()
    result = publisher.publish_article(
        html_content=html_content,
        title_override="AI 工具如何改变你的工作方式",  # 强制指定标题
        author="567"
    )
    print(result)


# 示例 3：从动态生成的 HTML 发布
def publish_from_generated_html():
    """从动态生成的 HTML 发布"""
    # 这里可以是从 API 获取的、或从模板渲染生成的 HTML
    generated_html = f"""
    <h3>今日 AI 资讯</h3>
    <p>这是动态生成的 HTML 内容。</p>
    <p>可以来自于任何数据源。</p>
    """

    publisher = WeChatPublisher()
    result = publisher.publish_article(
        html_content=generated_html,
        title_override="今日 AI 资讯",
        author="567"
    )
    print(result)


if __name__ == "__main__":
    import os

    # 检查环境变量
    if not os.getenv("WECHAT_API_KEY"):
        print("❌ 请设置 WECHAT_API_KEY 环境变量")
        print("export WECHAT_API_KEY=your_api_key")
        exit(1)

    print("=" * 60)
    print("示例 1：使用文件路径发布")
    print("=" * 60)
    # publish_from_file()  # 取消注释以测试

    print("\n" + "=" * 60)
    print("示例 2：直接使用 HTML 内容发布")
    print("=" * 60)
    publish_from_content()

    print("\n" + "=" * 60)
    print("示例 3：从动态生成的 HTML 发布")
    print("=" * 60)
    publish_from_generated_html()
