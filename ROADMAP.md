# Allox 分阶段路线图 & Todo List

> **Allox** = All-in-One + box。平台层 OpenSandbox，运行时初期用官方 AIO 镜像，CLI 参考 `osb` 但不 fork。  
> 完成一项后将 `[ ]` 改为 `[x]`。建议在文末「里程碑」处记录日期。

---

## 架构速览

```text
allox CLI  →  opensandbox-server  →  AIO 镜像（初期官方 / 后期自建）
                ↓
         agent-sandbox（/v1 shell·file·browser·…）
         execd（平台注入，二期可选暴露）
```

| 层级 | 职责 | 主要依赖 |
|------|------|----------|
| `allox` | 产品命令、默认镜像、会话 | `opensandbox`、`agent-sandbox` |
| `opensandbox-server` | 生命周期、endpoint、超时 | 官方，仅配置 |
| AIO 镜像 | 浏览器 / MCP / VSCode 等 | `ghcr.io/agent-infra/sandbox` |
| `osb`（可选） | 排障用，不 fork | `pip install opensandbox-cli` |

---

## 阶段 0：平台就绪（约 1–2 天）

**目标**：不依赖 Allox，先证明 OpenSandbox + AIO 链路可用。

> **进度核对（2026-05-20）**：**阶段 0 已全部完成** ✅（官方示例 + `allox` 配置 `localhost:8080`）。下一步：**阶段 1.5 端到端验收**。

### 环境

- [x] 本机安装 **Docker**，`docker version` 正常（Client 29.4.3，`desktop-linux`）
- [x] 本机 **Python ≥ 3.10**（`uv python install 3.12` → CPython 3.12.13）
- [x] 安装 `uv` 或 `pipx`（`uv 0.11.15` 已安装）

### 镜像与 Server

- [x] 预拉 AIO 镜像：`docker pull ghcr.io/agent-infra/sandbox:latest`（生产建议 pin 具体 tag）
- [x] 安装并初始化 Server：`opensandbox-server init-config ~/.sandbox.toml --example docker`
- [x] 启动 Server：`opensandbox-server`（示例已连 `http://localhost:8080`，沙箱创建成功）
- [x] 若 macOS Colima：`export DOCKER_HOST=...`（**不适用**：Docker Desktop，已跳过）

### 官方验收（不经 Allox）

- [x] 在 `OpenSandbox` 目录：`uv venv` + `uv pip install opensandbox agent-sandbox==0.0.18 requests`
- [x] 跑通示例：`uv run python examples/aio-sandbox/main.py`
- [x] 确认输出含：`[check] sandbox ready`、`AIO portal endpoint`、`sandbox_screenshot.png`（生成于 `OpenSandbox/` 目录）

### Allox 开发环境

- [x] `cd allox-cli && uv sync`（`.venv` + `allox-cli==0.1.0` 可编辑安装已成功）
- [x] `allox --help` 能正常显示（Banner + sandbox / aio / config 命令组）
- [x] `allox config init` 生成 `~/.allox/config.toml`（已存在）
- [x] `allox config set connection.domain localhost:8080`（与 Server 端口一致）

**阶段 0 完成标准**：官方 `aio-sandbox` 示例成功 + `allox --help` 可用。  
**当前状态**：✅ **已完成**（13/13，含 Colima 跳过项）。

### ~~阶段 0 收尾命令~~（已完成，可备查）

```bash
uv run allox config set connection.protocol http   # 可选，默认已是 http
uv run allox config show
```

---

## 阶段 1：最小可用 CLI（约 2 周）

**目标**：日常 Agent 流程只走 `allox`，镜像仍用官方 AIO。

### 1.1 沙箱生命周期（OpenSandbox）

- [x] `allox sandbox create`（默认镜像 + entrypoint + AIO health_check）
- [x] `allox sandbox kill`
- [x] `allox sandbox list`
- [x] `allox sandbox get`
- [x] `allox sandbox endpoint`
- [x] `allox sandbox create` 支持 `--env KEY=VALUE`（多组）
- [x] `allox sandbox create` 支持 `--metadata`（已有可再测一轮）
- [x] `allox sandbox create` 支持 `--timeout none`（手动清理模式）
- [x] 创建失败时错误信息可读（对齐 `SandboxException` code/message）

### 1.2 AIO Agent 面（agent-sandbox）

- [x] `allox aio exec <id> -- <cmd>`
- [x] `allox aio read <id> <path>`
- [x] `allox aio screenshot <id> -f <file>`（`-o` 保留给 json 输出格式）
- [x] `allox aio jupyter run <id> --code '...'`（或 `aio code`）
- [x] `allox aio browser info <id>`（输出 CDP URL，便于 Playwright）
- [x] MCP 子命令（见 **阶段 2.6**，覆盖沙箱内全部 MCP server）

### 1.3 配置与输出

- [x] `allox config init | show | set | path`
- [x] 配置优先级：CLI flag > 环境变量 > `~/.allox/config.toml`
- [x] 所有 create/endpoint 命令稳定支持 `-o json`（供脚本调用）
- [x] README 中写明默认：`image`、`entrypoint`、`aio_port`

### 1.4 文档与测试

- [x] README「快速开始」与本机 Server 端口逐步对齐（避免 8080/8090 混用）
- [x] `tests/test_cli_help.py`（help 冒烟）
- [x] 增加 create 的 mock 测试或集成测试说明（标记 `@integration`）
- [x] 在 README 增加「与 osb 分工」：日常 `allox`，排障可装 `osb`
- [x] 阶段 1 测试汇总见 `docs/PHASE1_TESTING.md`

### 1.5 端到端验收

- [ ] `allox sandbox create -o json` → 记录 `id`、`aio_url`
- [ ] `allox aio exec <id> -- ls -la`
- [ ] `allox aio screenshot <id> -o test.png`
- [ ] `allox sandbox kill <id>`
- [ ] 全程不启动 `osb`（仅 Allox）

**阶段 1 完成标准**：上述端到端验收 4 条全部通过。

---

## 阶段 2：产品化 CLI（约 2–4 周）

**目标**：更好给人用、给 Agent 脚本用；仍用官方 AIO 镜像。

### 2.1 会话与状态

- [x] 本地会话文件 `~/.allox/sessions.json`（`sandbox_id`、`aio_url`、`created_at`）
- [x] `allox sandbox create` 自动写入当前 session
- [x] `allox session current` / `allox session use <id>` / `allox session clear`
- [x] `aio` 子命令支持省略 `<sandbox_id>`（默认当前 session）

### 2.2 命令体验

- [x] 统一 `-o table|json|raw|yaml`（与 osb 行为对照表写进 README）
- [x] `allox sandbox list` 表格化输出（Rich，参考 osb）
- [x] `allox sandbox create` 显示等待 AIO 就绪耗时
- [x] `allox aio exec` 支持 `--workdir`（若 SDK 支持）
- [x] 全局 `--verbose` 打印 HTTP / 健康检查细节

### 2.3 元数据与多环境

- [x] `create` 默认 metadata：`tool=allox`、`version=...`
- [x] 支持 `--profile dev|prod` 或多配置文件 `--config ~/.allox/dev.toml`
- [x] 文档：dev / staging / prod 三套 `connection.domain` 示例

### 2.4 可靠性

- [x] 健康检查可配置：`defaults.aio_health_path`（默认 `/v1/shell/sessions`）
- [x] `create --ready-timeout 60s` 与配置项联动
- [x] 连接 AIO 失败时提示检查 `sandbox endpoint` 与防火墙
- [x] `allox sandbox renew <id>`（若 Server 支持续期）

### 2.5 可选：暴露 execd 能力（与 AIO 并行）

> 同一容器内 execd 由平台注入；仅在你需要与 osb 对齐运维面时做。

- [x] `allox run <id> -- <cmd>`（走 `sandbox.commands.run`，非 AIO shell）
- [x] `allox file cat|write <id> ...`（走 opensandbox files API）
- [x] README 说明：**Agent 业务优先 `aio *`，运维可选 `run`/`file`**

### 2.6 MCP 服务 CLI

> 沙箱内 MCP 通过 REST `GET/POST /v1/mcp/*` 暴露（`agent-sandbox` SDK 已封装）；Hub 协议端点 `/mcp` 供 Agent 直连，**CLI 优先走 REST**，与现有 `aio exec` / `aio read` 等命令一致。

#### 2.6.1 盘点 AIO Sandbox MCP Server（前置）

实现 CLI 前，先对照官方文档与**运行中的沙箱**确认当前镜像内置 server 列表（`GET /v1/mcp/servers`），避免文档与镜像版本漂移。

- [x] 在已创建沙箱上执行 `GET /v1/mcp/servers`，记录实际返回的 server 名称（见 `docs/MCP_SERVERS.md` 实测节；集成测试 `test_integration_mcp.py`）
- [x] 对每个 server 执行 `GET /v1/mcp/{server}/tools`，整理工具名与参数 schema（见 `docs/MCP_SERVERS.md`）
- [x] 将盘点结果写入 `docs/MCP_SERVERS.md`（server 列表、工具清单、代表性调用示例）
- [x] 官方镜像 `ghcr.io/agent-infra/sandbox` **当前文档记载 4 类**（集成测试校验；镜像升级后复测）：

| server | 典型工具 | 能力 |
|--------|----------|------|
| `browser` | `browser_navigate`, `browser_screenshot`, `browser_click`, … | 浏览器自动化（较常启用；工具名带前缀） |
| `file` | `read`, `write`, `list`, … | 文件系统（部分镜像未启用） |
| `shell` | `exec`, `create_session`, `kill` | Shell（部分镜像未启用） |
| `markitdown` | `convert`, `extract_text`, … | 文档转 Markdown（部分镜像未启用） |

参考：`AIOsandbox/README.md`（MCP Servers 表）、`AIOsandbox/website/docs/zh/guide/basic/mcp.md`、OpenAPI `/v1/mcp/*`。

#### 2.6.2 CLI 命令（覆盖盘点出的全部 MCP server）

基于 `obj.aio_client(id).mcp`（`list_mcp_servers` / `list_mcp_tools` / `execute_mcp_tool`），不重复实现 HTTP 层。

- [x] `allox aio mcp servers [sandbox_id]` — 列出 MCP server（`-o table|json|yaml`）
- [x] `allox aio mcp tools [sandbox_id] <server>` — 列出指定 server 的工具及描述
- [x] `allox aio mcp call [sandbox_id] <server> <tool>` — 调用工具（`--args '<json>'` 或多次 `--arg key=value`）
- [x] 支持省略 `sandbox_id`（默认当前 session，与阶段 2.1 一致）
- [x] 调用结果支持 `-o json|raw`，便于 Agent 脚本消费

#### 2.6.3 验收（每个 MCP server 至少 1 个代表性工具）

- [x] `browser`：`browser_navigate` 或 `browser_screenshot`（`test_mcp_call_browser_tool`）
- [x] `file`：`list`（`test_mcp_call_file_list_if_configured`，镜像无则 skip）
- [x] `shell`：`exec`（`test_mcp_call_shell_exec_if_configured`，镜像无则 skip）
- [x] `markitdown`：`convert`（`test_mcp_call_markitdown_if_configured`，镜像无则 skip）
- [x] 集成测试标记 `@integration`；用例写入 `docs/PHASE2_TESTING.md`
- [x] README：说明 MCP CLI 与 `aio exec` / `aio read` / `aio screenshot` 的分工（Agent 统一工具面 vs 人类直调）

**阶段 2 完成标准**：session 省略 sandbox_id + `-o json` 脚本化 + 多 profile 文档齐全 + **2.6 MCP 验收通过**。

---

## 阶段 3：自定义镜像（按需，与 CLI 解耦）

**目标**：换镜像 tag 即可升级环境，CLI 尽量不改。

### 3.1 衍生 AIO 镜像

- [x] 编写 `docker/Dockerfile`：`FROM ghcr.io/agent-infra/sandbox:<pinned-tag>`
- [x] 按 AIO 文档添加 apt/pip/npm 依赖
- [x] 按需添加 supervisord / nginx 配置（`/opt/gem/supervisord`、`/opt/gem/nginx`）
- [x] 构建并推送私有仓库：`your-registry/your-aio:v1`（见 `docker/build.sh`）
- [x] `allox config set defaults.image your-registry/your-aio:v1`

### 3.2 验证自定义镜像

- [x] `allox sandbox create` 使用新镜像且 health_check 通过
- [x] 验证新增服务端口（`allox sandbox endpoint` / 自定义端口文档）
- [x] 若删减 AIO 组件（如 Code Server），同步删减/调整 `aio` 子命令文档

### 3.3 长期：非 AIO 镜像（可选）

- [x] 评估 `opensandbox/code-interpreter` 作为「轻量代码沙箱」第二镜像
- [x] 新增命令组 `allox code ...` 或 `allox sandbox create --profile code`
- [x] 参考 `OpenSandbox/sandboxes/code-interpreter/build.sh` 建立 CI 构建

**阶段 3 完成标准**：私有镜像在生产配置中默认使用，阶段 1 端到端验收仍通过。

---

## 阶段 4：进阶（季度级，按需选做）

- [ ] CI：lint（ruff）+ pytest + 可选集成测试（需 Docker）
- [ ] 发布：`pip install allox-cli` 或内部 PyPI
- [ ] `allox` 输出 shell 补全（click-shell 或 argcomplete）
- [ ] 与 Agent 框架集成示例（LangGraph / OpenAI tools 调用 `allox -o json`）
- [ ] K8s：文档化 `opensandbox-server` + AIO 镜像在集群中的部署
- [ ] 监控：记录 create/kill 耗时与失败率（日志或 OpenTelemetry）

---

## 关键约定（全阶段有效）

| 项 | 约定 |
|----|------|
| AIO entrypoint | `["/opt/gem/run.sh"]`（官方镜像） |
| AIO API 端口 | `8080`（`defaults.aio_port`） |
| 健康检查 | `GET /v1/shell/sessions` → 200 |
| 镜像 tag | 生产禁止裸 `latest`，使用 pin 版本 |
| API Key | Header `OPEN-SANDBOX-API-KEY`，配置 `connection.api_key` |
| 双 API | Agent 用 **AIO `/v1`**；运维/execd 用 **opensandbox**（勿混用同一操作的两种 API） |

---

## 里程碑记录

| 阶段 | 计划完成 | 实际完成 | 备注 |
|------|----------|----------|------|
| 0 平台就绪 | | **2026-05-20 完成** | 官方 `main.py` + `~/.allox/config.toml` + `domain=localhost:8080` |
| 1 最小 CLI | | | 脚手架已含 create/aio/config 基础命令 |
| 2 产品化 | | | |
| 3 自定义镜像 | | **2026-06-22 完成** | `docker/` 衍生镜像 + `docs/CUSTOM_IMAGE.md` + code profile |
| 4 进阶 | | | |

---

## 相关路径

| 资源 | 路径 |
|------|------|
| Allox 项目 | `Agent/allox-cli/` |
| Allox README | `Agent/allox-cli/README.md` |
| 阶段 1 测试记录 | `Agent/allox-cli/docs/PHASE1_TESTING.md` |
| 阶段 2 测试记录 | `Agent/allox-cli/docs/PHASE2_TESTING.md` |
| OpenSandbox AIO 示例 | `Agent/OpenSandbox/examples/aio-sandbox/` |
| osb 参考实现 | `Agent/OpenSandbox/cli/` |
| AIO 定制镜像文档 | `Agent/AIOsandbox/website/docs/en/blog/announcing-0.mdx`（Custom Images） |
| AIO MCP 文档 | `Agent/AIOsandbox/website/docs/zh/guide/basic/mcp.md` |
| AIO MCP OpenAPI | `Agent/AIOsandbox/website/docs/public/v1/openapi.json`（`/v1/mcp/*`） |
| Allox MCP 盘点 | `Agent/allox-cli/docs/MCP_SERVERS.md` |
| 自定义 AIO 镜像 | `Agent/allox-cli/docker/`、`docs/CUSTOM_IMAGE.md` |
| 阶段 3 测试记录 | `Agent/allox-cli/docs/PHASE3_TESTING.md` |
| Code Interpreter 评估 | `Agent/allox-cli/docs/CODE_INTERPRETER.md` |
| code-interpreter 构建 | `Agent/OpenSandbox/sandboxes/code-interpreter/` |

---

## 建议执行顺序（每周参考）

| 周次 | 聚焦 |
|------|------|
| 第 1 周 | 阶段 0 全部 + 阶段 1.5 端到端验收 |
| 第 2 周 | 阶段 1 未完成项（env、错误信息、jupyter/browser） |
| 第 3–4 周 | 阶段 2（session、json、多 profile、**2.6 MCP CLI**） |
| 第 5 周+ | 阶段 3 自定义 Dockerfile；阶段 4 按需 |

---

*文档版本：与 Allox `0.1.0` 脚手架同步。更新脚手架命令时请同步勾选「已完成」项。*
