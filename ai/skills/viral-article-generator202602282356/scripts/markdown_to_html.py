#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 转 HTML 转换脚本
将 Markdown 格式的文章转换为微信公众号支持的 HTML 格式
"""

import json
import sys
from pathlib import Path
from typing import Dict

try:
    import markdown
except ImportError as e:
    print(f"错误：缺少依赖库。请运行: pip install -r requirements.txt")
    print(f"详细错误: {e}")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        from beautifulsoup4 import BeautifulSoup
    except ImportError:
        print("错误：缺少 BeautifulSoup4 库。请运行: pip install beautifulsoup4")
        sys.exit(1)


class MarkdownToHTMLConverter:
    """Markdown 转 HTML 转换器"""

    # 微信公众号样式配置
    STYLES = {
        'container': """
            max-width: 800px;
            margin: 0 auto;
            font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            line-height: 1.8;
            color: #333;
            padding: 0 15px;
        """,
        'h3': """
            color: #800000;
            font-size: 17px;
            font-weight: bold;
            margin: 20px 0 15px 0;
            padding-bottom: 10px;
        """,
        'h2': """
            color: #333;
            font-size: 18px;
            font-weight: bold;
            margin: 25px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        """,
        'p': """
            color: #555;
            font-size: 16px;
            margin: 15px 0;
            line-height: 1.8;
            text-align: justify;
        """,
        'ul': """
            color: #555;
            font-size: 16px;
            margin: 15px 0;
            padding-left: 25px;
        """,
        'li': """
            margin: 8px 0;
            line-height: 1.8;
        """,
        'blockquote': """
            border-left: 4px solid #ddd;
            background-color: #f9f9f9;
            padding: 15px 20px;
            margin: 20px 0;
            color: #666;
            font-size: 15px;
        """,
        'strong': """
            color: #333;
            font-weight: bold;
        """,
        'a': """
            color: #576b95;
            text-decoration: none;
        """,
        'img': """
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px 0;
            border-radius: 4px;
        """,
        'hr': """
            border: none;
            border-top: 1px solid #eee;
            margin: 30px 0;
        """
    }

    def __init__(self):
        """初始化转换器"""
        self.md = markdown.Markdown(
            extensions=['tables', 'fenced_code', 'nl2br']
        )

    def convert_file(self, md_file: Path, output_file: Path = None) -> str:
        """转换 Markdown 文件为 HTML

        Args:
            md_file: Markdown 文件路径
            output_file: 输出 HTML 文件路径（可选，默认与 md 文件同目录）

        Returns:
            生成的 HTML 文件路径
        """
        # 读取 Markdown 文件
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 转换为 HTML
        html_content = self.md.convert(md_content)

        # 应用样式
        styled_html = self._apply_styles(html_content)

        # 特殊处理：图片换行
        styled_html = self._fix_image_breaks(styled_html)

        # 包裹在 HTML 文档结构中
        final_html = self._wrap_html(styled_html)

        # 确定输出文件路径
        if output_file is None:
            output_file = md_file.with_suffix('.html')

        # 保存 HTML 文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)

        print(f"✅ HTML 文件已保存: {output_file}")

        return str(output_file)

    def convert_file_with_mapping(self, md_file: Path, mapping_file: Path, output_file: Path = None) -> str:
        """转换 Markdown 文件为 HTML，使用图片映射替换链接

        Args:
            md_file: Markdown 文件路径
            mapping_file: 图片映射文件（JSON 格式：千问链接 -> GitHub 链接）
            output_file: 输出 HTML 文件路径（可选，默认与 md 文件同目录）

        Returns:
            生成的 HTML 文件路径
        """
        # 读取 Markdown 文件
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 读取图片映射
        with open(mapping_file, 'r', encoding='utf-8') as f:
            image_mapping = json.load(f)

        # 替换图片链接（千问链接 -> GitHub 链接）
        for qwen_url, github_url in image_mapping.items():
            md_content = md_content.replace(qwen_url, github_url)

        # 转换为 HTML
        html_content = self.md.convert(md_content)

        # 应用样式
        styled_html = self._apply_styles(html_content)

        # 特殊处理：图片换行
        styled_html = self._fix_image_breaks(styled_html)

        # 包裹在 HTML 文档结构中
        final_html = self._wrap_html(styled_html)

        # 确定输出文件路径
        if output_file is None:
            output_file = md_file.with_suffix('.html')

        # 保存 HTML 文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)

        print(f"✅ HTML 文件已保存: {output_file}")

        return str(output_file)

    def _convert_lists_to_paragraphs(self, html: str) -> str:
        """将有序列表转换为带编号的段落

        Args:
            html: 原始 HTML

        Returns:
            转换后的 HTML
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 处理有序列表 (ol)
        for ol in soup.find_all('ol'):
            items = ol.find_all('li', recursive=False)
            for index, li in enumerate(items, 1):
                # 创建新的 p 标签，包含编号和内容
                new_p = soup.new_tag('p')
                number_span = soup.new_tag('span')
                number_span.string = f"{index}. "
                number_span['style'] = "font-weight: bold;"
                new_p.append(number_span)

                # 复制 li 的内容
                for child in list(li.children):
                    new_p.append(child)

                ol.insert_before(new_p)
            ol.decompose()

        # 处理无序列表 (ul)
        for ul in soup.find_all('ul'):
            items = ul.find_all('li', recursive=False)
            for li in items:
                # 创建新的 p 标签，包含符号和内容
                new_p = soup.new_tag('p')
                new_p.append("• ")  # 项目符号

                # 复制 li 的内容
                for child in list(li.children):
                    new_p.append(child)

                ul.insert_before(new_p)
            ul.decompose()

        return str(soup)

    def _apply_styles(self, html: str) -> str:
        """应用内联样式到 HTML

        Args:
            html: 原始 HTML

        Returns:
            应用样式后的 HTML
        """
        # 先转换列表为段落
        html = self._convert_lists_to_paragraphs(html)

        soup = BeautifulSoup(html, 'html.parser')

        # 应用容器样式到根元素
        for elem in soup.find_all(['p', 'h2', 'h3', 'blockquote', 'hr']):
            # 清理现有的 style 属性（使用我们的样式覆盖）
            elem['style'] = ''

        # 按顺序应用样式
        # h3
        for h3 in soup.find_all('h3'):
            existing_style = h3.get('style', '')
            h3['style'] = self.STYLES['h3'] + existing_style

        # h2
        for h2 in soup.find_all('h2'):
            existing_style = h2.get('style', '')
            h2['style'] = self.STYLES['h2'] + existing_style

        # p
        for p in soup.find_all('p'):
            existing_style = p.get('style', '')
            p['style'] = self.STYLES['p'] + existing_style

        # blockquote
        for bq in soup.find_all('blockquote'):
            existing_style = bq.get('style', '')
            bq['style'] = self.STYLES['blockquote'] + existing_style
            # 为 blockquote 内的 p 标签移除 margin，避免重复
            for bq_p in bq.find_all('p'):
                existing_bq_p_style = bq_p.get('style', '')
                # 移除 margin 相关样式
                new_style = existing_bq_p_style.replace('margin: 15px 0;', '').replace('margin:8px 0;', '')
                bq_p['style'] = new_style

        # strong
        for strong in soup.find_all('strong'):
            existing_style = strong.get('style', '')
            strong['style'] = self.STYLES['strong'] + existing_style

        # a
        for a in soup.find_all('a'):
            existing_style = a.get('style', '')
            a['style'] = self.STYLES['a'] + existing_style

        # img
        for img in soup.find_all('img'):
            existing_style = img.get('style', '')
            img['style'] = self.STYLES['img'] + existing_style

        # hr
        for hr in soup.find_all('hr'):
            existing_style = hr.get('style', '')
            hr['style'] = self.STYLES['hr'] + existing_style

        return str(soup)

    def _fix_image_links(self, html: str) -> str:
        """修复图片链接中的 HTML 实体编码

        将 &amp; 还原为 &，确保图片链接可访问

        Args:
            html: 原始 HTML

        Returns:
            修复后的 HTML
        """
        soup = BeautifulSoup(html, 'html.parser')

        # 修复所有 img 标签的 src 属性
        for img in soup.find_all('img'):
            if img.has_attr('src'):
                src = img['src']
                # 将 &amp; 还原为 &
                src_fixed = src.replace('&amp;', '&')
                img['src'] = src_fixed

        return str(soup)

    def _fix_image_breaks(self, html: str) -> str:
        """修复图片换行问题

        Args:
            html: 原始 HTML

        Returns:
            修复后的 HTML
        """
        # 先修复图片链接
        html = self._fix_image_links(html)

        soup = BeautifulSoup(html, 'html.parser')

        # 处理所有 img 标签：移除 style 和 alt 属性，用 p 标签包裹
        for img in soup.find_all('img'):
            if img.has_attr('src'):
                src = img['src']

                # 创建新的 p 标签包裹 img
                new_p = soup.new_tag('p')
                new_p['style'] = 'text-align: center; margin: 20px 0;'

                # 创建新的 img 标签（不带 style 和 alt）
                new_img = soup.new_tag('img')
                new_img['src'] = src
                # 不设置 style 和 alt 属性

                # 将 img 添加到 p 中
                new_p.append(new_img)

                # 替换原来的 img 标签
                img.replace_with(new_p)

        return str(soup)

    def _wrap_html(self, body_content: str) -> str:
        """将内容包裹在完整的 HTML 文档结构中

        Args:
            body_content: HTML body 内容

        Returns:
            完整的 HTML 文档
        """
        # 修复图片链接中的 HTML 实体编码
        # 将 &amp; 还原为 &，确保图片链接可访问
        body_content_fixed = body_content.replace('&amp;', '&')

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>公众号文章</title>
</head>
<body>
    <div style="{self.STYLES['container']}">
        {body_content_fixed}
    </div>
</body>
</html>
"""


def main():
    """命令行接口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python markdown_to_html.py <markdown文件> [输出html文件]")
        print()
        print("示例:")
        print('  python markdown_to_html.py article.md')
        print('  python markdown_to_html.py article.md article.html')
        sys.exit(1)

    md_file = Path(sys.argv[1])

    # 检查文件是否存在
    if not md_file.exists():
        print(f"错误：文件不存在: {md_file}")
        sys.exit(1)

    # 检查文件扩展名
    if md_file.suffix.lower() != '.md':
        print(f"警告：输入文件不是 .md 格式: {md_file}")

    # 确定输出文件
    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = md_file.with_suffix('.html')

    # 转换文件
    try:
        converter = MarkdownToHTMLConverter()
        converter.convert_file(md_file, output_file)
        print(f"\n📄 Markdown: {md_file}")
        print(f"📄 HTML: {output_file}")

    except Exception as e:
        print(f"❌ 转换失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
