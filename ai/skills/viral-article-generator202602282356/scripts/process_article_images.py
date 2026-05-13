#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理文章图片：从Markdown提取千问图片URL，上传到GitHub，更新HTML文件
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

from upload_image_to_github import GitHubImageUploader


def extract_image_urls_from_markdown(md_file: str) -> List[str]:
    """从Markdown文件中提取所有图片URL

    Args:
        md_file: Markdown文件路径

    Returns:
        图片URL列表
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 ![](url) 格式的图片
    pattern = r'!\[.*?\]\((https://[^\)]+)\)'
    urls = re.findall(pattern, content)

    print(f"📋 从Markdown中提取到 {len(urls)} 张图片")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url[:80]}...")

    return urls


def upload_images_to_github(image_urls: List[str]) -> Dict[str, str]:
    """上传图片到GitHub并返回映射关系

    Args:
        image_urls: 千问图片URL列表

    Returns:
        {千问URL: GitHub URL} 的映射字典
    """
    print("\n" + "=" * 60)
    print("📤 开始上传图片到GitHub...")
    print("=" * 60)

    uploader = GitHubImageUploader()
    github_urls = uploader.upload_from_url_batch(image_urls, prefix="article", verify=False)

    # 创建映射关系
    url_mapping = {}
    for qwen_url, github_url in zip(image_urls, github_urls):
        url_mapping[qwen_url] = github_url
        print(f"\n✅ 映射: {qwen_url[:60]}... -> {github_url}")

    return url_mapping


def update_html_with_github_urls(html_file: str, url_mapping: Dict[str, str]) -> None:
    """更新HTML文件中的图片链接为GitHub链接

    Args:
        html_file: HTML文件路径
        url_mapping: URL映射字典
    """
    print("\n" + "=" * 60)
    print("📝 更新HTML文件中的图片链接...")
    print("=" * 60)

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 替换所有千问URL为GitHub URL
    updated_count = 0
    for qwen_url, github_url in url_mapping.items():
        if qwen_url in html_content:
            html_content = html_content.replace(qwen_url, github_url)
            updated_count += 1
            print(f"✅ 已替换: {qwen_url[:60]}...")

    # 写回文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ HTML文件更新完成，共替换 {updated_count} 个图片链接")


def save_mapping_to_json(mapping_file: str, url_mapping: Dict[str, str]) -> None:
    """保存URL映射到JSON文件

    Args:
        mapping_file: 映射文件路径
        url_mapping: URL映射字典
    """
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(url_mapping, f, ensure_ascii=False, indent=2)

    print(f"\n💾 映射关系已保存到: {mapping_file}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python process_article_images.py <markdown_file>")
        print("示例: python process_article_images.py ../assets/articles/20260228_AI_提升职场效率真的会取代我们吗？.md")
        sys.exit(1)

    md_file = sys.argv[1]
    md_path = Path(md_file)

    if not md_path.exists():
        print(f"❌ 文件不存在: {md_file}")
        sys.exit(1)

    # 生成对应的HTML文件路径
    html_file = md_path.with_suffix('.html')
    if not html_file.exists():
        print(f"❌ HTML文件不存在: {html_file}")
        sys.exit(1)

    # 生成映射文件路径
    mapping_file = md_path.parent / f"{md_path.stem}.mapping.json"

    print("=" * 60)
    print("🚀 开始处理文章图片")
    print("=" * 60)
    print(f"Markdown文件: {md_file}")
    print(f"HTML文件: {html_file}")
    print(f"映射文件: {mapping_file}")

    try:
        # 1. 提取图片URL
        image_urls = extract_image_urls_from_markdown(md_file)

        if not image_urls:
            print("\n⚠️  未找到图片，退出")
            sys.exit(0)

        # 2. 上传到GitHub
        url_mapping = upload_images_to_github(image_urls)

        # 3. 更新HTML文件
        update_html_with_github_urls(str(html_file), url_mapping)

        # 4. 保存映射关系
        save_mapping_to_json(str(mapping_file), url_mapping)

        print("\n" + "=" * 60)
        print("✅ 所有操作完成！")
        print("=" * 60)
        print(f"\n下一步：使用 HTML 文件发布到公众号")
        print(f"HTML文件路径: {html_file}")

    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

