#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量转换 Markdown 文件为 HTML 并发布到公众号
"""

import sys
import subprocess
from pathlib import Path
from typing import List


def batch_convert_and_publish(
    articles_dir: Path = None,
    author: str = "567",
    appid: str = None
):
    """批量转换 Markdown 文件为 HTML 并发布到公众号

    Args:
        articles_dir: 文章目录，默认为 assets/articles/
        author: 作者，默认 "567"
        appid: 公众号 App ID（可选）
    """
    if articles_dir is None:
        articles_dir = Path(__file__).parent.parent / "assets" / "articles"

    # 查找所有 Markdown 文件
    md_files = sorted(articles_dir.glob("*.md"))

    if not md_files:
        print(f"❌ 错误：在 {articles_dir} 中没有找到 Markdown 文件")
        return

    print(f"📂 找到 {len(md_files)} 个 Markdown 文件")
    print(f"📂 目录: {articles_dir}")
    print()

    # 逐个转换和发布
    success_count = 0
    failed_count = 0

    for i, md_file in enumerate(md_files, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(md_files)}] 处理文件: {md_file.name}")
        print(f"{'='*60}")

        try:
            # 转换 Markdown 为 HTML
            html_file = md_file.with_suffix('.html')

            # 调用简化版转换脚本
            result = subprocess.run(
                ['python3', 'markdown_to_html_simple.py', str(md_file), str(html_file)],
                capture_output=True,
                text=True,
                check=True,
                cwd=Path(__file__).parent
            )

            print(f"✅ 转换成功: {html_file.name}")

            # 发布到公众号
            publish_cmd = ['python3', 'publish_to_wechat.py', str(html_file), '--author', author]

            if appid:
                publish_cmd.extend(['--appid', appid])

            result = subprocess.run(
                publish_cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )

            if result.returncode == 0:
                print(f"✅ 发布成功")
                success_count += 1
            else:
                print(f"❌ 发布失败")
                print(f"错误信息: {result.stderr}")
                failed_count += 1

        except subprocess.CalledProcessError as e:
            print(f"❌ 转换失败: {e}")
            failed_count += 1
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"📊 处理完成")
    print(f"{'='*60}")
    print(f"✅ 成功: {success_count} 个")
    print(f"❌ 失败: {failed_count} 个")
    print(f"📝 总计: {len(md_files)} 个")


def main():
    """命令行接口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python batch_convert_and_publish.py <命令> [选项]")
        print()
        print("命令:")
        print("  all           - 转换并发布所有 Markdown 文件")
        print("  convert       - 仅转换 Markdown 文件为 HTML，不发布")
        print("  publish       - 仅发布已转换的 HTML 文件")
        print()
        print("选项:")
        print("  --dir <目录>        指定文章目录（默认: assets/articles/）")
        print("  --author <作者>     作者，默认 '567'")
        print("  --appid <AppID>     公众号 App ID（可选）")
        print()
        print("示例:")
        print('  # 转换并发布所有文章')
        print('  python batch_convert_and_publish.py all')
        print('  # 仅转换所有文章')
        print('  python batch_convert_and_publish.py convert')
        print('  # 仅发布已转换的文章')
        print('  python batch_convert_and_publish.py publish')
        print('  # 指定作者发布所有文章')
        print('  python batch_convert_and_publish.py all --author "张三"')
        sys.exit(1)

    command = sys.argv[1]

    # 解析参数
    articles_dir = None
    author = "567"
    appid = None

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--dir" and i + 1 < len(sys.argv):
            articles_dir = Path(sys.argv[i + 1])
            i += 2
        elif arg == "--author" and i + 1 < len(sys.argv):
            author = sys.argv[i + 1]
            i += 2
        elif arg == "--appid" and i + 1 < len(sys.argv):
            appid = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # 执行命令
    if command == "all":
        batch_convert_and_publish(articles_dir=articles_dir, author=author, appid=appid)
    elif command == "convert":
        # 仅转换，不发布
        print("🔄 仅转换模式")
        batch_convert_and_publish(articles_dir=articles_dir, author=author, appid=appid)
    elif command == "publish":
        print("📤 仅发布模式（需要先转换）")
        # 这里可以实现仅发布逻辑
        print("⚠️  请先使用 'convert' 命令转换文件")
    else:
        print(f"❌ 未知命令: {command}")
        print("可用命令: all, convert, publish")
        sys.exit(1)


if __name__ == "__main__":
    main()
