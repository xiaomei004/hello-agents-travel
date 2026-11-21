# travel-agent

一个用于学习 **ReAct（Reasoning + Acting）** 的最小旅行助手：模型先思考，再调用天气/景点工具，拿到结果后继续思考，直到给出最终答案。

## 功能

- 查询城市实时天气（wttr.in，无需 Key）
- 根据城市和天气搜索景点推荐（Tavily Search API）
- 用 DeepSeek / 任意 OpenAI 兼容接口驱动 ReAct 循环
- 严格的 `Thought / Action / Observation` 解析
- 配置校验、超时、错误提示
- 单元测试、Ruff 静态检查、GitHub Actions CI

## 项目结构

```text
travel-agent/
├─ main.py                     # 兼容入口：python main.py
├─ travel_agent/
│  ├─ __init__.py              # 版本号
│  ├─ __main__.py              # python -m travel_agent
│  ├─ cli.py                   # 命令行参数与启动流程
│  ├─ config.py                # 环境变量、Settings、占位符校验
│  ├─ llm.py                   # OpenAI 兼容客户端、LLMError
│  ├─ prompts.py               # ReAct 系统提示词
│  ├─ agent.py                 # ReAct 循环与 Action 解析
│  └─ tools/
│     ├─ __init__.py           # 工具注册表
│     ├─ weather.py            # get_weather
│     └─ attractions.py        # get_attraction
├─ tests/
│  ├─ test_agent.py            # 解析器与 ReAct 循环测试
│  ├─ test_tools.py            # 天气/景点工具测试
│  └─ test_config.py           # 配置校验测试
├─ docs/
│  └─ 学习笔记.md              # 环境排查与项目构建记录
├─ .github/workflows/ci.yml    # GitHub Actions：ruff + pytest
├─ requirements.txt            # 运行依赖
├─ requirements-dev.txt        # 开发依赖
├─ pyproject.toml              # 项目元数据与工具配置
├─ .env.example                # 环境变量模板
├─ .gitignore
└─ README.md
```

> 这是一个**应用型**项目，所以包直接放在根目录，`python main.py` 即可运行。
> 如果是准备发布到 PyPI 的库，通常会用 `src/travel_agent/` 布局，避免测试时误导入源码目录。

## 快速开始

### 1. 创建虚拟环境

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

开发时（需要跑测试和 Ruff）：

```bash
pip install -r requirements-dev.txt
```

### 3. 配置环境变量

```bash
copy .env.example .env
```

编辑 `.env`：

```text
DEEPSEEK_API_KEY=sk-你的真实key
TAVILY_API_KEY=tvly-你的真实key
```

> `.env` 已被 `.gitignore` 忽略，不要提交。
> Tavily CLI 的 OAuth 凭证和 `TAVILY_API_KEY` 不是同一个东西，Python SDK 需要单独的 API Key。

### 4. 运行

```bash
python main.py
```

或：

```bash
python -m travel_agent
```

也可以直接提问：

```bash
python main.py "帮我查一下杭州明天的天气，再推荐一个景点"
```

安装为命令（可选）：

```bash
pip install -e .
travel-agent "帮我查一下杭州明天的天气"
```

## 配置项

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `DEEPSEEK_API_KEY` | 是 | 无 | 大模型 API Key |
| `DEEPSEEK_BASE_URL` | 否 | `https://api.deepseek.com` | OpenAI 兼容接口地址 |
| `DEEPSEEK_MODEL` | 否 | `deepseek-flash` | 模型名，按账号实际可用模型修改 |
| `TAVILY_API_KEY` | 是 | 无 | Tavily Search API Key |
| `AGENT_MAX_STEPS` | 否 | `5` | 最大 ReAct 循环次数 |
| `USER_PROMPT` | 否 | 内置示例问题 | 不传命令行问题时的默认提问 |
| `LLM_TIMEOUT` | 否 | `60` | 单次模型调用超时（秒） |

## 运行链路

```text
用户问题
  → TravelAgent 组装历史
  → OpenAICompatibleClient 调模型
  → 模型返回 Thought + Action
  → parse_action / parse_tool_call 解析
  → 执行 get_weather / get_attraction
  → 结果作为 Observation 写回历史
  → 继续循环，直到 Finish[...] 或达到最大步数
```

## 测试与检查

```bash
ruff check .
pytest
```

测试不需要真实 API Key：LLM 和 Tavily 都被替换成了假实现。

## 设计说明

- **配置集中**：所有环境变量在 `config.py` 读取和校验，避免散落在各个脚本。
- **错误不吞掉**：模型调用失败抛 `LLMError`，由 CLI 统一处理；工具错误转成 `Observation`，让模型有机会自我修正。
- **解析与执行分离**：`agent.py` 里的解析函数是纯函数，方便单元测试。
- **工具注册表**：新增工具只需在 `tools/__init__.py` 注册，不用改主循环。
- **可替换**：`TravelAgent` 只依赖 `generate()` 协议，测试时可以注入假 LLM。

## 常见问题

### 为什么 venv 里还要重新装依赖？

venv 默认不继承全局 Python 的包。新建 venv 后必须：

```bash
pip install -r requirements.txt
```

### 为什么 PyCharm 还是爆红？

确认解释器选的是：

```text
travel-agent\venv\Scripts\python.exe
```

然后 `File → Invalidate Caches → Invalidate and Restart`。

### 报 `No module named 'dotenv'`？

装错包了。正确包名是 `python-dotenv`，不是 `dotenv`。

### 模型名报错？

把 `.env` 里的 `DEEPSEEK_MODEL` 改成你账号实际可用的模型，例如 `deepseek-chat`。

## 学习笔记

环境排查、venv、pip 与解释器错位的详细记录见 [docs/学习笔记.md](docs/学习笔记.md)。

## License

暂未添加开源许可证。如需公开使用，建议补充 MIT 或 Apache-2.0。
