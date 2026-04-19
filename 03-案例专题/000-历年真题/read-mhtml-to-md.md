# MHTML 转 MD 真题文档操作指南

## 场景

从方才 coding 等网站导出的 `.mhtml` 软考真题文件中提取内容，整理为干净的 Markdown 文档。

## 步骤

### 1. 批量提取文本内容

使用 mhtml-reader skill 的脚本提取所有 MHTML 文件的文本：

```bash
python3 /Users/edgarlqs/.claude/skills/mhtml-reader/scripts/extract_mhtml.py ./软考真题.mhtml --json 2>&1
```

对目录下每个 MHTML 文件执行一次，提取 `[].sections[0]` 作为题目文本内容。

### 2. 提取嵌入图片

```python
python3 -c "
import email, os, hashlib
os.makedirs('./extracted', exist_ok=True)
for fname in glob('*.mhtml'):
    prefix = fname.replace('.mhtml', '')
    with open(fname, 'r', encoding='utf-8') as f:
        msg = email.message_from_string(f.read())
    img_count = 0
    for part in msg.walk():
        ct = part.get_content_type()
        if ct.startswith('image/'):
            data = part.get_payload(decode=True)
            if data:
                ext = ct.split('/')[1]
                img_name = f'{prefix}_img_{img_count}.{ext}'
                with open(f'./extracted/{img_name}', 'wb') as out:
                    out.write(data)
                img_count += 1
"
```

### 3. 识别图片类型

- **架构图/流程图**：用 mermaid 复刻到 MD 中
- **二维码/Logo/UI 装饰**：在附录中说明，不放入正文
- **题目表格截图**：转为 Markdown 表格

### 4. 整理为 MD 文档

输出文件命名格式：`YYYY年MM月-系统架构设计师-案例真题.md`

结构模板：

```markdown
# YYYY年MM月 系统架构设计师 案例分析真题

> 来源：方才coding 软考真题

---

## 第 X 大题：题目主题

**案例背景：**

（去除"收藏"、"查看答案"、"上一题"、"答题卡"等 UI 文字）

---

### 试题 N

（题干内容，表格用 Markdown 表格）

```mermaid
（架构图/序列图用 mermaid 复刻）
```

---

## 附录：提取的图片

（说明哪些图已复刻、哪些省略）
```

### 5. 清理临时文件

```bash
rm -rf ./extracted/
```

## 关键注意点

1. **过滤 UI 噪声**：去除导航栏、按钮、版权信息、二维码等
2. **保留真题完整性**：题干、选项、表格、填空位置不能遗漏
3. **图片处理**：架构图优先 mermaid 复刻，无法复刻的截图保留为图片引用
4. **表格还原**：MHTML 中的 HTML 表格转为 Markdown 表格
5. **序列图/架构图**：题目中的图用 mermaid 还原框架，标注填空位置
