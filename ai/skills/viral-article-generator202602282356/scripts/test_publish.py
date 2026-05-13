#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证公众号发布功能
"""

import os
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from publish_to_wechat import WeChatPublisher


def test_get_accounts():
    """测试获取公众号列表"""
    print("=" * 60)
    print("测试 1：获取公众号列表")
    print("=" * 60)

    try:
        publisher = WeChatPublisher()
        accounts = publisher.get_accounts()

        print(f"\n✅ 成功获取公众号列表")
        print(f"公众号数量: {accounts.get('total', 0)}")

        for account in accounts.get('accounts', []):
            print(f"\n公众号名称: {account.get('name')}")
            print(f"AppID: {account.get('wechatAppid')}")
            print(f"类型: {account.get('type')}")
            print(f"状态: {account.get('status')}")

        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False


def test_parse_html():
    """测试 HTML 解析功能"""
    print("\n" + "=" * 60)
    print("测试 2：HTML 解析功能")
    print("=" * 60)

    # 创建测试 HTML 文件
    test_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试文章</title>
</head>
<body>
    <h2>这是测试标题</h2>
    <p>这是测试内容第一段。</p>
    <p>这是测试内容第二段。</p>
</body>
</html>"""

    test_file = Path(__file__).parent.parent / "assets" / "test_article.html"
    test_file.parent.mkdir(parents=True, exist_ok=True)

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_html)

    try:
        publisher = WeChatPublisher()
        parsed = publisher.parse_html_for_publish(test_file)

        print(f"\n✅ HTML 解析成功")
        print(f"标题: {parsed['title']}")
        print(f"内容长度: {len(parsed['content'])} 字符")
        print(f"内容预览: {parsed['content'][:100]}...")

        # 清理测试文件
        test_file.unlink()

        return True
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
        return False


def main():
    """运行所有测试"""
    print("\n🧪 开始测试公众号发布功能\n")

    # 检查环境变量
    if not os.getenv("WECHAT_API_KEY"):
        print("❌ 错误：未设置 WECHAT_API_KEY 环境变量")
        print("请运行: export WECHAT_API_KEY=your_api_key")
        sys.exit(1)

    results = []

    # 测试 1：获取公众号列表
    results.append(("获取公众号列表", test_get_accounts()))

    # 测试 2：HTML 解析
    results.append(("HTML 解析功能", test_parse_html()))

    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n💡 提示：现在可以使用以下命令发布文章：")
        print("  python publish_to_wechat.py <html文件路径>")
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        sys.exit(1)


if __name__ == "__main__":
    main()
