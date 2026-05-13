---
name: viral-article-generator
description: 公众号爆款文章生成器，为 AI+职场主题生成可直接发布的文章。自动生成爆款标题和内容，调用千问文生图生成配图，上传 GitHub 图床获取永久链接，转换为公众号 HTML 格式，支持一键发布到公众号草稿箱。使用场景：(1) 生成 AI+职场主题的公众号文章 (2) 创建带配图的深度好文 (3) 转换 Markdown 为公众号 HTML 格式 (4) 发布文章到公众号草稿箱
---

# 公众号爆款文章生成器

## 快速开始

生成文章并发布到公众号：

```bash
export GITHUB_TOKEN=
python3 scripts/generate_article.py "AI 工具提升效率" --publish
```

### 必需环境变量

```bash
export DASHSCOPE_API_KEY=your_api_key           # 千问文生图
export WECHAT_API_KEY=your_api_key              # 绿联 API（公众号发布）
export GITHUB_TOKEN=your_token                 # GitHub Token（图片图床）
```

## 核心脚本

### generate_article.py

主脚本，完整流程：生成文章 → 千问配图 → 上传 GitHub → 转 HTML → 发布

```bash
# 基础用法
python3 scripts/generate_article.py "主题"

# 自定义参数
python3 scripts/generate_article.py "主题" --images 3 --title "自定义标题" --publish
```

### markdown_to_html.py

独立转换脚本，Markdown 转公众号 HTML 格式

```bash
python3 scripts/markdown_to_html.py article.md
```

### publish_to_wechat.py

发布 HTML 文章到公众号草稿箱

```bash
python3 scripts/publish_to_wechat.py article.html --author "567"
```

## 选题参考

热门选题方向：[references/ai-topics.md](references/ai-topics.md)

## 输出文件

| 文件 | 说明 | 图片链接 |
|------|------|----------|
| `YYYYMMDD_标题.md` | Markdown 原文 | 千问临时链接（24小时） |
| `YYYYMMDD_标题.html` | 公众号格式 | GitHub 永久链接 |
| `YYYYMMDD_标题.mapping.json` | 链接映射 | 千问 → GitHub |
