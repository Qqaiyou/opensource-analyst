# M13 Step 5: 验收标准

## 测试命令

```bash
# 启动开发服务器
uv run uvicorn src.opensource_analyst.main:app --reload --host 127.0.0.1 --port 8000

# 运行 M13 单元测试（20 个）
uv run pytest tests/test_conversation_state.py tests/test_conversation_api.py -v

# 运行全量回归（148 个）
uv run pytest -v
```

## 预期输出

### 1. 单元测试输出

```
tests/test_conversation_state.py: 10 passed
tests/test_conversation_api.py:   10 passed
======================== 20 passed ================
```

### 2. 全量回归输出

```
128 existing tests + 20 M13 tests = 148 passed, 0 failed
```

### 3. 浏览器功能验收

1. 访问 `http://localhost:8000/chat` → 显示三栏布局页面（左侧分析摘要 + 中间对话 + 右侧推理轨迹）
2. 粘贴 `https://github.com/msiemens/tinydb` → 点 Analyze
3. 左侧状态显示 `Analyzing...` → `Status: running` → `Ready`
4. 左侧出现可折叠的分析报告：Overview / Tech Stack / Dependencies / Architecture / Learning Path / Interview Questions / Reflection / Mermaid Diagrams
5. Mermaid 图在展开时被渲染为 SVG
6. 中间聊天区出现系统消息：`Analysis complete. You can now ask questions...`
7. 输入 "这个项目是做什么的？" → AI 回答（不调工具，直接基于分析报告）
8. 输入 "查询引擎怎么实现的，给我看代码" → 右侧面板出现 ReAct 步骤：`Action: search_code` → `Observation: 3 个代码片段` → AI 回复引用代码
9. 继续问 "上面的 storage 是怎么实现的" → AI 能理解"上面"指上一个回复中的内容
10. 输入 "有哪些 GitHub Issues" → AI 调用 MCP 工具查询（如 MCP Server 已配置）

## 常见问题

### Q: 前端页面空白或 404

**原因**：`/chat` 路由未正确配置

**检查**：
```bash
curl http://127.0.0.1:8000/chat
# 应返回 HTML 内容（<html>...）
```

### Q: 分析完成后左侧无显示

**原因**：`/task/{id}/result` 返回的外层结构是 `{task_id, status, result: {...}}`，前端需取 `data.result`

**检查**：打开浏览器 console (F12)，查看 `Raw API response` 日志，确认 `result` 字段存在

### Q: AI 回复 "（AI 未生成回复）"

**原因**：DeepSeek API 调用失败

**检查**：
1. `.env` 中 `DEEPSEEK_API_KEY` 是否有效
2. 服务器终端日志中是否有 `openai.BadRequestError` 或 `call_model 失败`
3. 确认 DeepSeek API 余额充足

### Q: AI 不记得之前聊过什么

**原因**：`send_message` 未从 `session.messages` 恢复历史

**检查**：
```python
# 在 send_message 中添加日志
logger.info("历史消息数: %d", len(session.messages))
```

### Q: search_code 工具返回 "未找到相关代码片段"

**原因**：向量存储中没有数据（可能是 `/analyze` 没有完成 RAG 索引步骤）

**检查**：重新运行 `/analyze`，确认 status 为 `completed`（不是 error）
