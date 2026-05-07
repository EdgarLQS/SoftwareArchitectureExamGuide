---
name: mhtml-reader
description: 读取和解析 MHTML 文件格式，提取其中的文本内容。当用户需要阅读 .mhtml、.mht 文件（网页归档格式）时自动触发此技能。
---

# MHTML Reader

用于读取和解析 MHTML（MIME HTML）文件格式，提取其中保存的网页文本内容。

## 何时使用

- 用户请求读取 `.mhtml` 或 `.mht` 文件
- 用户需要查看网页归档文件中的内容
- 用户想要从保存的网页中提取文本信息

## MHTML 文件格式说明

MHTML（MIME HTML）是一种网页归档格式，它将 HTML 页面及其相关资源（图片、CSS、JS 等）打包成单个文件。文件格式特点：

- 使用 MIME 多部分消息格式
- 包含多个部分：HTML 内容、CSS 样式、图片等
- 使用 quoted-printable 编码
- 可能有 URL 编码的中文字符（如 `%E4%BA%91%E5%8E%9F`）

## 读取步骤

### 步骤 1：确认文件路径

MHTML 文件可能存在于以下位置：
- 当前工作目录
- 用户指定的路径
- 通过 Glob 搜索找到的 `.mhtml` 文件

### 步骤 2：使用 Python 脚本提取内容

由于 MHTML 是二进制编码格式，不能直接用 Read 工具读取。使用以下 Python 脚本提取文本内容：

```python
import re
import html
import urllib.parse

def extract_mhtml_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 HTML 部分
    html_parts = re.findall(
        r'------MultipartBoundary[\s\S]*?Content-Type: text/html[\s\S]*?\n\n([\s\S]*?)(?=------MultipartBoundary|$)', 
        content
    )
    
    cleaned_text = ""
    for part in html_parts:
        # 移除 soft line breaks
        text = re.sub(r'=\n', '', part)
        # 解码 HTML 实体
        text = html.unescape(text)
        # URL 解码
        text = urllib.parse.unquote(text)
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除 JavaScript 和 CSS
        text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', text)
        text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text)
        cleaned_text += text + "\n\n"
    
    return cleaned_text
```

### 步骤 3：执行脚本并输出结果

使用 Bash 工具执行 Python 脚本：

```bash
python3 << 'PYTHON_EOF'
import re
import html
import urllib.parse

with open('文件路径.mhtml', 'r', encoding='utf-8') as f:
    content = f.read()

html_parts = re.findall(
    r'------MultipartBoundary[\s\S]*?Content-Type: text/html[\s\S]*?\n\n([\s\S]*?)(?=------MultipartBoundary|$)', 
    content
)

cleaned_text = ""
for part in html_parts:
    text = re.sub(r'=\n', '', part)
    text = html.unescape(text)
    text = urllib.parse.unquote(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', text)
    text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text)
    cleaned_text += text + "\n\n"

# 输出到临时文件以便后续读取
with open('/tmp/mhtml_extracted.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned_text)

print(f"提取完成，共 {len(cleaned_text)} 字符")
PYTHON_EOF
```

### 步骤 4：整理和总结内容

提取文本后：
1. 过滤掉 UI 噪声（导航菜单、按钮文本等）
2. 识别主要内容（对话、文章正文等）
3. 按逻辑结构整理内容
4. 向用户总结提取到的核心信息

## 注意事项

1. **编码问题**：MHTML 文件使用 quoted-printable 编码，中文字符可能被 URL 编码
2. **文件较大**：MHTML 文件可能很大，提取时注意分块处理
3. **内容过滤**：提取的内容可能包含网页 UI 元素，需要过滤

## 输出格式

提取的内容应按以下格式整理：

```
# [网页标题]

## 主要内容
[提取的正文内容]

## 关键信息
- 关键点 1
- 关键点 2
...
```

## 示例

用户：`阅读 Google Gemini.mhtml 文件`

响应：
1. 使用上述脚本提取 MHTML 内容
2. 整理提取的文本
3. 总结文件包含的核心信息
