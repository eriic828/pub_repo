#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里千问文生图服务调用脚本
支持单次和多张图片生成，自动处理频率限制
"""

import json
import os
import subprocess
import sys
import time
from typing import List, Optional

import requests


# 导入 GitHub 上传器
try:
    from upload_image_to_github import GitHubImageUploader
except ImportError:
    GitHubImageUploader = None


class QwenImageGenerator:
    """阿里千问文生图生成器"""

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
        """初始化生成器

        Args:
            api_key: 阿里云 API Key，默认从 shell 环境变量 DASHSCOPE_API_KEY 读取
        """
        self.api_key = api_key or self._get_env_from_shell("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量（可在 ~/.zshrc 中添加: export DASHSCOPE_API_KEY=your_key）")

        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        size: str = "1664*928",
        watermark: bool = False,
        prompt_extend: bool = True
    ) -> Optional[str]:
        """生成单张图片

        Args:
            prompt: 图片描述提示词
            negative_prompt: 负面提示词，描述不希望出现的内容
            size: 图片尺寸，格式 "宽*高"，如 "1664*928"
            watermark: 是否添加水印
            prompt_extend: 是否扩展提示词

        Returns:
            图片 URL，失败返回 None
        """
        if negative_prompt is None:
            negative_prompt = (
                "低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，"
                "蜡像感，人脸无细节，过度光滑，画面具有AI感。"
                "构图混乱。文字模糊，扭曲。"
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": "qwen-image-max",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
                "size": size
            }
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            result = response.json()

            # 提取图片 URL
            image_url = (
                result.get("output", {})
                       .get("choices", [{}])[0]
                       .get("message", {})
                       .get("content", [{}])[0]
                       .get("image")
            )

            if image_url:
                print(f"✅ 图片生成成功: {image_url}")
                return image_url
            else:
                print(f"❌ 响应中没有图片 URL: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"❌ 解析响应失败: {e}")
            return None

    def generate_images(
        self,
        prompts: List[str],
        wait_between: int = 30
    ) -> List[str]:
        """批量生成图片

        Args:
            prompts: 图片描述提示词列表
            wait_between: 每张图片生成之间的等待时间（秒），默认 30 秒

        Returns:
            图片 URL 列表，失败的项为 None
        """
        if len(prompts) > 4:
            print(f"⚠️  一次最多生成 4 张图片，自动截取前 4 张")
            prompts = prompts[:4]

        image_urls = []

        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] 正在生成第 {i} 张图片...")
            print(f"提示词: {prompt}")

            image_url = self.generate_image(prompt)
            image_urls.append(image_url)

            # 最后一张图片不需要等待
            if i < len(prompts):
                print(f"⏳ 等待 {wait_between} 秒后再生成下一张图片...")
                time.sleep(wait_between)

        return image_urls

    def generate_for_article(
        self,
        article_topic: str,
        image_positions: int = 4
    ) -> List[str]:
        """为公众号文章自动生成配图

        Args:
            article_topic: 文章主题
            image_positions: 需要生成图片的位置数量，默认 4 张

        Returns:
            图片 URL 列表
        """
        # 根据文章主题自动生成配图提示词
        prompts = self._generate_prompts_for_topic(article_topic, image_positions)
        return self.generate_images(prompts)

    def upload_images_to_github(
        self,
        image_urls: List[str],
        prefix: str = "img"
    ) -> List[str]:
        """将生成的图片上传到 GitHub 作为长期图床

        Args:
            image_urls: 千问图片 URL 列表
            prefix: 文件名前缀

        Returns:
            GitHub 图片 URL 列表，上传失败的项保持原 URL
        """
        if GitHubImageUploader is None:
            print("⚠️  GitHub 上传器未安装，跳过上传步骤")
            print("   如需使用 GitHub 图床，请运行: pip install PyGithub")
            return image_urls

        try:
            print("\n" + "=" * 60)
            print("📤 开始上传图片到 GitHub 图床...")
            print("=" * 60)

            uploader = GitHubImageUploader()
            github_urls = uploader.upload_from_url_batch(image_urls, prefix)

            print("\n" + "=" * 60)
            print("✅ 图片上传完成！")
            print("=" * 60)

            return github_urls

        except Exception as e:
            print(f"\n⚠️  GitHub 上传失败: {e}")
            print("   使用原始千问图片链接")
            return image_urls

    @staticmethod
    def _generate_prompts_for_topic(topic: str, count: int) -> List[str]:
        """根据主题生成配图提示词

        Args:
            topic: 文章主题
            count: 需要生成的图片数量

        Returns:
            提示词列表
        """
        # 这里提供一些通用的配图提示词模板
        # 实际使用中，可以根据文章内容动态调整
        base_templates = [
            f"现代科技风格的{topic}主题插画，简洁专业，适合公众号文章配图",
            f"展示{topic}相关场景的商务风格插图，扁平化设计，色彩温和",
            f"{topic}概念的抽象表现图，现代简约风格，适合作为文章插图",
            f"职场人使用{topic}工具的场景插画，温暖励志，符合公众号调性"
        ]

        # 如果只需要部分图片，返回对应数量的提示词
        if count <= len(base_templates):
            return base_templates[:count]

        # 如果需要更多图片，循环使用模板
        prompts = []
        for i in range(count):
            template = base_templates[i % len(base_templates)]
            prompts.append(f"{template}，风格变化{i+1}")

        return prompts


def main():
    """命令行接口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  # 单张图片")
        print("  python generate_qwen_image.py \"一张现代风格的办公场景插画\"")
        print()
        print("  # 多张图片（自动等待30秒）")
        print("  python generate_qwen_image.py \"场景1\" \"场景2\" \"场景3\" \"场景4\"")
        print()
        print("  # 为文章主题自动生成配图")
        print("  python generate_qwen_image.py --article \"AI 工具提升效率\"")
        print()
        print("  # 上传到 GitHub 图床（解决千问图片24小时有效期问题）")
        print("  python generate_qwen_image.py \"场景\" --github")
        print()
        print("环境变量:")
        print("  DASHSCOPE_API_KEY - 阿里千问 API Key（必需，可在 ~/.zshrc 中配置）")
        print("  GITHUB_TOKEN - GitHub Token（用于上传图片，推荐，可在 ~/.zshrc 中配置）")
        print("  GITHUB_REPO - GitHub 仓库（默认: prepared48/skillImages567，可在 ~/.zshrc 中配置）")
        sys.exit(1)

    # 检查是否需要上传到 GitHub
    upload_to_github = "--github" in sys.argv

    try:
        generator = QwenImageGenerator()

        # 检查是否是文章主题模式
        if sys.argv[1] == "--article" and len(sys.argv) >= 3:
            article_topic = " ".join(sys.argv[2:])
            print(f"📝 为文章主题「{article_topic}」自动生成配图...")

            image_urls = generator.generate_for_article(article_topic)

            print("\n" + "=" * 60)
            print("🖼️  所有图片生成完成！")
            print("=" * 60)

            # 如果需要上传到 GitHub
            if upload_to_github:
                image_urls = generator.upload_images_to_github(image_urls, "article")

            for i, url in enumerate(image_urls, 1):
                if url:
                    print(f"\n图片 {i}: {url}")
                else:
                    print(f"\n图片 {i}: 生成失败")

            # 输出可复制的 Markdown 格式
            print("\n" + "=" * 60)
            print("📋 Markdown 格式图片链接：")
            print("=" * 60)
            for i, url in enumerate(image_urls, 1):
                if url:
                    print(f"\n![图片 {i}]({url})")
        else:
            # 普通模式：生成指定的图片
            prompts = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
            image_urls = generator.generate_images(prompts)

            print("\n" + "=" * 60)
            print("🖼️  图片生成完成！")
            print("=" * 60)

            # 如果需要上传到 GitHub
            if upload_to_github:
                image_urls = generator.upload_images_to_github(image_urls, "img")

            for i, url in enumerate(image_urls, 1):
                if url:
                    print(f"\n图片 {i}: {url}")
                else:
                    print(f"\n图片 {i}: 生成失败")

            # 输出可复制的 Markdown 格式
            print("\n" + "=" * 60)
            print("📋 Markdown 格式图片链接：")
            print("=" * 60)
            for i, url in enumerate(image_urls, 1):
                if url:
                    print(f"\n![图片 {i}]({url})")

    except ValueError as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
