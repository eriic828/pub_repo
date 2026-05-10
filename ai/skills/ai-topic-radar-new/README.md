# 斑码AI选题雷达 - 配置指南

## 快速配置

### 1. 获取 Tavily API Key（免费）

1. 访问 https://tavily.com
2. 点击 "Sign Up" 注册账号
3. 登录后进入 Dashboard
4. 复制 API Key（格式：`tvly-xxxxx`）

**免费额度**：1000 credits/月，无需绑卡

---

### 2. 配置 API Key

**方式A：对话中设置**

```
设置Tavily API Key: tvly-xxxxx
```

**方式B：手动编辑配置文件**

编辑 `config.json`：
```json
{
  "tavily_api_key": "tvly-xxxxx",
  "output_path": "topic/"
}
```

---

## 搜索工具说明

| 工具 | 状态 | 免费额度 | 说明 |
|------|------|---------|------|
| **Exa** | 主工具 | 不明确 | 语义搜索强，默认使用 |
| **Tavily** | 备用 | 1000 credits/月 | 响应快，需配置 API Key |
| **GitHub API** | 补充 | 无限制 | 项目搜索，降级方案 |

---

## 使用方式

### 每日推送模式

```
AI选题
```

自动发现 GitHub 热点，生成 Top 10 选题。

### 快速查找模式

```
选题 DeepSeek 教程
```

根据关键词精准搜索。

---

## 故障排除

### Exa 搜索失败

**症状**：返回 "rate limit" 或空结果

**解决**：自动切换到 Tavily（需配置 API Key）

### Tavily 也失败

**症状**：提示 "API key invalid" 或无结果

**解决**：
1. 检查 API Key 是否正确
2. 检查是否有免费额度
3. 使用 GitHub 搜索作为降级方案

### 所有搜索都失败

**症状**：结果不足 10 条

**解决**：更换关键词重试

---

## 版本信息

- **当前版本**：v3.7.0
- **更新日期**：2026-03-24
- **核心特性**：Exa + Tavily 混合策略