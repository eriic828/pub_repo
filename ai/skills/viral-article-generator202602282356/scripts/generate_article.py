#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号爆款文章生成器（带配图和发布功能）
生成可直接发布的 Markdown 和 HTML 格式文章
支持自动发布到微信公众号草稿箱
"""

import json
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from generate_qwen_image import QwenImageGenerator
from markdown_to_html import MarkdownToHTMLConverter


class ArticleGenerator:
    """公众号文章生成器"""

    # 爆款标题模板库
    TITLE_TEMPLATES = {
        "curiosity": [
            "{topic}真的会取代我们吗？",
            "为什么别人用{topic}效率这么高？",
            "{topic}教会我们的3件事，最后一件很多人还做不到",
        ],
        "contrast": [
            "用{topic}3个月，我终于不再加班",
            "普通人用{topic}，也能成为高手",
            "30岁职场人，用{topic}每天多出2小时",
        ],
        "pain_point": [
            "每次写周报要2小时？用{topic}10分钟搞定",
            "这样下去，职场效率永远上不去",
            "你已经很久没有真正休息过了吧？",
        ],
        "benefit": [
            "用{topic}每天省2小时，我是怎么做到的",
            "华为、阿里员工正在用的{topic}资源，请自取",
            "学会这3个{topic}技巧，工作效率翻倍",
        ],
        "number": [
            "3个{topic}方法，让我效率提升200%",
            "用{topic}3个月，我发现5个惊人秘密",
            "7个{topic}工具，让职场人轻松应对工作",
        ],
        "emotional": [
            "因为无所依仗，所以必须学会{topic}",
            "无情！不会用{topic}的人，正在被淘汰",
            "做好心理准备，{topic}已经开始改变职场了",
        ],
        "suspense": [
            "{topic}之后，职场发生了什么变化？",
            "我用了{topic}，结果出乎意料",
            "那些{topic}高手，都做对了什么？",
        ]
    }

    def __init__(self, output_dir: Optional[Path] = None):
        """初始化文章生成器

        Args:
            output_dir: 文章输出目录，默认为 assets/articles/
        """
        skill_dir = Path(__file__).parent.parent
        self.output_dir = output_dir or skill_dir / "assets" / "articles"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.templates_dir = skill_dir / "assets"
        self.image_generator = QwenImageGenerator()

    def generate_article(
        self,
        topic: str,
        template_type: str = "opening-impact",
        image_count: int = 4,
        custom_title: Optional[str] = None
    ) -> Tuple[str, str]:
        """生成一篇带配图的公众号文章

        Args:
            topic: 文章主题
            template_type: 模板类型（opening-impact, story-intro, data-driven, pain-point）
            image_count: 配图数量（1-4 张）
            custom_title: 自定义标题（可选）

        Returns:
            (文章标题, 生成的文章文件路径)
        """
        print(f"📝 开始生成公众号文章...")
        print(f"主题: {topic}")
        print(f"模板: {template_type}")
        print(f"配图数量: {image_count}")

        # 生成标题
        title = custom_title or self._generate_viral_title(topic)
        print(f"标题: {title}")

        # 生成文章内容（不包含标题行）
        article_content = self._generate_article_content(topic, template_type)

        # 生成配图
        print(f"\n🖼️  开始生成配图...")
        qwen_image_urls = self.image_generator.generate_for_article(topic, image_count)

        # 上传到 GitHub 图床（用于 HTML 格式）
        try:
            github_image_urls = self.image_generator.upload_images_to_github(qwen_image_urls, "article")
        except Exception as e:
            print(f"⚠️  GitHub 上传失败，使用原始千问图片链接: {e}")
            github_image_urls = qwen_image_urls

        # 插入配图到文章中（Markdown 使用千问临时链接）
        article_with_images = self._insert_images(article_content, qwen_image_urls)

        # 保存文章（文件名：日期+标题）
        safe_title = self._sanitize_filename(title)
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{date_str}_{safe_title}.md"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(article_with_images)

        print(f"\n✅ Markdown 文章已保存: {filepath}")

        # 保存图片映射（千问链接 -> GitHub 链接）
        image_mapping = dict(zip(qwen_image_urls, github_image_urls))
        mapping_file = filepath.with_suffix('.mapping.json')
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(image_mapping, f, ensure_ascii=False, indent=2)

        # 自动转换为 HTML 格式（使用 GitHub 永久链接）
        print(f"\n🔄 开始转换为 HTML 格式...")
        html_converter = MarkdownToHTMLConverter()
        html_filepath = html_converter.convert_file_with_mapping(filepath, mapping_file)
        print(f"\n✅ HTML 文章已保存: {html_filepath}")

        return title, str(filepath), str(html_filepath)

    def _generate_viral_title(self, topic: str) -> str:
        """根据爆款方法论生成标题

        Args:
            topic: 文章主题

        Returns:
            爆款标题
        """
        # 从各类模板中随机选择
        all_templates = []
        for templates in self.TITLE_TEMPLATES.values():
            all_templates.extend(templates)

        # 随化处理：从所有模板中第一个匹配的替换
        for template in all_templates:
            title = template.replace("{topic}", topic)
            # 检查长度，控制在 30 字以内
            if len(title) <= 30:
                return title

        # 默认返回第一个
        return all_templates[0].replace("{topic}", topic)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名中的特殊字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 移除或替换不安全的字符（包括中文标点符号）
        filename = re.sub(r'[<>:"/\\|?*。，！、；：""''（）\\[\\]【】《》]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        return filename[:100]  # 限制长度

    def _generate_article_content(self, topic: str, template_type: str) -> str:
        """生成文章内容（不包含标题行）

        Args:
            topic: 文章主题
            template_type: 模板类型

        Returns:
            Markdown 格式的文章内容
        """
        # 开头钩子
        article = self._generate_hook(topic)
        article += "\n\n"

        # 第一段：痛点/故事 + 观点
        article += "## 之前的状态\n\n"
        article += self._generate_first_section(topic)
        article += "\n\n"

        # 第二段：方法/案例
        article += "## 核心方法\n\n"
        article += self._generate_second_section(topic)
        article += "\n\n"

        # 第三段：行动指南 + 升华
        article += "## 今天就可以开始\n\n"
        article += self._generate_third_section(topic)
        article += "\n\n"

        # 结尾
        article += "---\n\n"
        article += self._generate_ending(topic)

        return article

    def _generate_hook(self, topic: str) -> str:
        """生成开头钩子"""
        hooks = [
            f"用 {topic} 3 个月，我的工作效率提升了 200%。这 3 个方法，让每天多出 2 小时。",
            f"每次打开电脑，你都觉得时间不够用吗？",
            f"89% 的职场人不会用 {topic}，但 20% 的人已经领先。",
            f"这篇文章读完，你每天能省 3 小时。",
        ]
        return hooks[0]

    def _generate_first_section(self, topic: str) -> str:
        """生成第一段内容"""
        return f"""每次打开电脑，脑子里一堆事：
- 要写周报，但不知道从哪开始
- 客户邮件要回复，但措辞总不满意
- 项目进度要追踪，但整理信息就花半天
- 还要准备 PPT，模板找半天

结果就是，看似很忙，实际产出很低。加班成了常态，成就感越来越低。

## 核心观点

{topic} 不是取代我们，而是放大我们的能力。关键是掌握正确的方法，让它成为你的效率助手。"""

    def _generate_second_section(self, topic: str) -> str:
        """生成第二段内容"""
        return f"""### 方法一：AI 写作助手，10 分钟搞定所有文字工作

写周报、邮件、文案，每次都要花 1-2 小时？

用 ChatGPT 作为写作助手，具体这样操作：

1. 告诉 AI 背景："帮我写周报，本周完成了项目 A，主要产出是用户量增长 30%，下周计划优化产品体验"
2. 让 AI 优化："帮我把这段话改得更专业一点"
3. 让 AI 检查："帮我检查这段话有没有语病"

**效果**：周报从 2 小时降到 10 分钟，质量还提升了

> 真实案例：
> 之前写客户邮件，总担心语气不对。现在给 AI："帮我写封邮件，客户在催进度，我需要解释原因并给出解决方案"，1 分钟得到初稿，稍作修改就能发。客户反馈比以前更清晰专业。

### 方法二：AI 信息整理，30 分钟梳理一周工作

项目信息散落在各处，整理要花半天？

用 Claude 作为信息整理助手，具体这样操作：

1. 把所有信息丢给 AI："帮我整理这些项目信息，按优先级排序，标注风险点"
2. 让 AI 生成日报："根据今天的工作记录，生成今天的日报"
3. 让 AI 总结会议："帮我把会议纪要提炼成 3 个关键结论"

**效果**：信息整理从半天降到 30 分钟，重点更清晰

> 真实案例：
> 上周要写项目总结，10 个项目的信息到处都是。用 Claude 整理后，自动按进度、风险、资源维度分类，2 小时完成总结。老板看完说："终于看到重点了。"

### 方法三：AI PPT 生成，1 小时搞定专业演示

PPT 总要找模板、调格式，3 小时起步？

用 Gamma 作为 PPT 生成助手，具体这样操作：

1. 输入主题："帮我做一个关于 AI 工具效率提升的 PPT，受众是职场人"
2. 选择模板和风格
3. 让 AI 生成内容："帮我在每页写上关键要点"
4. 手动微调细节

**效果**：PPT 从 3 小时降到 1 小时，设计还更专业

> 真实案例：
> 上周要做季度汇报，通常要准备 2 天。用 Gamma，输入大纲后自动生成 20 页 PPT，花 1 小时调整内容。领导说："这比以前的 PPT 清晰多了。\""""

    def _generate_third_section(self, topic: str) -> str:
        """生成第三段内容"""
        return f"""别等明天，现在就试试这 3 步：

**第一步**：注册 ChatGPT 或国内 AI 工具（如文心一言、通义千问）

**第二步**：从最简单的任务开始，比如让 AI 帮你写一封邮件

**第三步**：用 AI 处理 5 个任务后，总结自己的使用心得

## 关键提醒

AI 不是万能的，但用对就能效率翻倍。记住这 3 个原则：

- **从小场景开始**：别一上来就想解决大问题
- **持续迭代优化**：多试几次，找到适合自己的方式
- **建立人机协作**：AI 生成，你来决策，效率最高"""

    def _generate_ending(self, topic: str) -> str:
        """生成结尾内容"""
        return f"""**写在最后**

{topic} 时代，最大的差距不是工具，而是使用工具的思维方式。从今天开始，用 {topic} 放大你的能力。

---

你觉得 {topic} 最大的价值是什么？欢迎在评论区分享你的使用心得。

如果这篇文章对你有帮助，**点赞、在看、转发**三连，让更多职场人看到 {topic} 的力量。

下期我会分享《AI 辅助学习，7 天掌握新技能》，关注我不错过。"""

    def _insert_images(self, article: str, image_urls: List[str]) -> str:
        """将配图插入到文章的合适位置

        Args:
            article: 文章内容
            image_urls: 图片 URL 列表

        Returns:
            插入图片后的文章
        """
        lines = article.split("\n")
        result = []
        image_index = 0
        section_count = 0

        for line in lines:
            result.append(line)

            # 在每个主要章节后插入图片（最多插入 image_count 张）
            if line.startswith("## ") and image_index < len(image_urls):
                section_count += 1
                # 在第 2、4、6 个章节后插入图片
                if section_count in [2, 4, 6]:
                    image_url = image_urls[image_index]
                    result.append("")
                    result.append(f"![]({image_url})")
                    result.append("")
                    image_index += 1

        # 如果还有图片没插入，在文章最后追加
        while image_index < len(image_urls):
            image_url = image_urls[image_index]
            result.append("")
            result.append("")
            result.append(f"![]({image_url})")
            result.append("")
            image_index += 1

        return "\n".join(result)


def main():
    """命令行接口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python generate_article.py \"文章主题\"")
        print()
        print("选项:")
        print("  --template <模板类型>    选择模板 (opening-impact, story-intro, data-driven, pain-point)")
        print("  --images <数量>          配图数量 (1-4)")
        print("  --title <标题>          自定义文章标题")
        print("  --publish              生成后发布到公众号草稿箱")
        print("  --auto-publish        生成文章后自动发布")
        print()
        print("示例:")
        print('  python generate_article.py "AI 工具提升效率"')
        print('  python generate_article.py "AI 工具提升效率" --images 2')
        print('  python generate_article.py "AI 工具提升效率" --template story-intro')
        print('  python generate_article.py "AI 工具提升效率" --title "3 个 AI 工具让我效率翻倍"')
        print('  python generate_article.py "AI 工具提升效率" --publish')
        print('  python generate_article.py "AI 工具提升效率" --auto-publish')
        sys.exit(1)

    # 解析参数
    topic = sys.argv[1]
    template_type = "opening-impact"
    image_count = 4
    custom_title = None
    auto_publish = False

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--template" and i + 1 < len(sys.argv):
            template_type = sys.argv[i + 1]
            i += 2
        elif arg == "--images" and i + 1 < len(sys.argv):
            try:
                image_count = int(sys.argv[i + 1])
                image_count = min(max(1, image_count), 4)
                i += 2
            except ValueError:
                print(f"⚠️  图片数量必须是 1-4 之间的整数")
                sys.exit(1)
        elif arg == "--title" and i + 1 < len(sys.argv):
            custom_title = sys.argv[i + 1]
            i += 2
        elif arg == "--publish":
            auto_publish = True
            i += 1
        elif arg == "--auto-publish":
            auto_publish = True
            i += 2
        else:
            i += 1

    try:
        generator = ArticleGenerator()
        title, filepath, html_filepath = generator.generate_article(
            topic=topic,
            template_type=template_type,
            image_count=image_count,
            custom_title=custom_title
        )

        # 自动发布到公众号
        if auto_publish:
            print("\n🔄 自动发布到微信公众号...")
            try:
                publish_script = Path(__file__).parent / "publish_to_wechat.py"
                result = subprocess.run(
                    [sys.executable, str(publish_script), html_filepath],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    print("✅ 发布成功！")
                    print(result.stdout)
                else:
                    print(f"❌ 发布失败：{result.stderr}")
            except Exception as e:
                print(f"❌ 自动发布失败：{e}")

        print(f"\n📄 文章标题: {title}")
        print(f"📄 文章文件: {filepath}")
        print(f"📄 HTML 文件: {html_filepath}")

        if auto_publish:
            print("=" * 60)
            print("📱 草稿箱入口：内容管理 -> 草稿箱")
        else:
            print("\n💡 提示：如需手动发布，运行以下命令：")
            print(f"  python publish_to_wechat.py {html_filepath}")

    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
