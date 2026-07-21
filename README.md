# Allox CLI

**Allox** = **All**-in-**O**ne + bo**x** — 面向 Agent 的沙箱命令行工具。

| 层级 | 职责 |
|------|------|
| **allox** | 产品命令、默认 AIO 镜像、本地配置 |
| **opensandbox-server** | 沙箱生命周期与 endpoint（默认 `http://localhost:8080`） |
| **AIO 镜像** | 容器内 Agent API（`/v1/*`，默认端口 **8080**） |

设计参考 OpenSandbox 的 `osb`，但为独立包，不 fork 其 CLI。  
任务清单见 [ROADMAP.md](./ROADMAP.md)；阶段 1 测试记录见 [docs/PHASE1_TESTING.md](./docs/PHASE1_TESTING.md)；阶段 2 见 [docs/PHASE2_TESTING.md](./docs/PHASE2_TESTING.md)；阶段 3 自定义镜像见 [docs/CUSTOM_IMAGE.md](./docs/CUSTOM_IMAGE.md)。

---

## 安装

```bash
cd allox-cli
# 推荐：非 editable 安装，避免 Python 3.12 下 .venv/bin/allox 找不到包
uv sync --no-editable
source .venv/bin/activate
allox --help
```

> **重要：`uv run allox` 会默认把项目重装为 editable，可能覆盖上面的修复，导致再次出现 `No module named 'allox'`。**  
> 日常请用 **`allox`**（已 `activate`）或 **`uv run --no-editable allox`**。若已踩坑，重新执行一次 `uv sync --no-editable --reinstall` 即可。

**开发中改了 `src/allox` 代码后**，`.venv` 里可能是旧 wheel，表现为：`session` 命令不存在、`~/.allox/sessions.json` 未生成。请任选其一：

```bash
# 推荐：重装本包
uv sync --reinstall-package allox-cli

# 或快速同步（不解析依赖）
rsync -a src/allox/ .venv/lib/python3.12/site-packages/allox/
```

验证：`allox --help` 应出现 `session`、`run`、`file` 子命令。

开发依赖（pytest、ruff）已包含在 `uv sync` 的 dev group 中。

---

## 平台准备：拉取镜像与启动 OpenSandbox Server

使用 `allox` 前需在本机准备好 **Docker**、**AIO 沙箱镜像** 与 **opensandbox-server**（Allox 只负责 CLI，不替代 Server）。

### 前置条件

- **Docker** 已安装并运行（`docker version` 正常）
- **Python ≥ 3.10**（推荐用 [uv](https://github.com/astral-sh/uv) 管理环境）
- macOS 若使用 **Colima** 而非 Docker Desktop，需先设置 `DOCKER_HOST`（例如 `export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock`）

### 1. 安装 opensandbox-server

```bash
# 推荐
uv pip install opensandbox-server

# 或
pip install opensandbox-server
```

首次使用需生成 Server 配置文件（默认 `~/.sandbox.toml`）：

```bash
opensandbox-server init-config ~/.sandbox.toml --example docker
# 覆盖已有文件时加 --force
```

可按需编辑 `~/.sandbox.toml` 中的 `server.host` / `server.port`（默认 `0.0.0.0:8080`）。完整配置项见 [OpenSandbox server/configuration.md](../OpenSandbox/server/configuration.md)。

### 2. 拉取 AIO 沙箱镜像

Allox 默认创建沙箱时使用官方 AIO 镜像（与 `defaults.image` 一致）：

```bash
docker pull ghcr.io/agent-infra/sandbox:latest
```

生产环境请 **pin 具体 tag**，避免裸 `latest`，例如：

```bash
docker pull ghcr.io/agent-infra/sandbox:<pinned-tag>
allox config set defaults.image ghcr.io/agent-infra/sandbox:<pinned-tag>
```

自定义衍生镜像见 [docs/CUSTOM_IMAGE.md](./docs/CUSTOM_IMAGE.md)。

### 3. 启动 Server

在**单独终端**保持 Server 运行：

```bash
opensandbox-server
# 或指定配置：opensandbox-server --config ~/.sandbox.toml
```

非交互环境（CI、部分容器）若未配置 `server.api_key`，启动时可能要求确认风险，可设置：

```bash
export OPENSANDBOX_INSECURE_SERVER=YES
opensandbox-server
```

验证 Server 就绪（端口与 `~/.sandbox.toml` 中 `server.port` 一致，默认 **8080**）：

```bash
curl http://127.0.0.1:8080/health
# 期望：{"status":"healthy"}
```

随后配置 Allox 指向同一地址：

```bash
allox config init
allox config set connection.domain localhost:8080
allox config set connection.protocol http
```

若 Server 启用了 API Key，还需 `allox config set connection.api_key YOUR_KEY`（请求头 `OPEN-SANDBOX-API-KEY`）。

---

## 端口说明（避免混淆）

| 服务 | 默认地址 | 用途 |
|------|----------|------|
| **OpenSandbox Server** | `http://localhost:8080` | `allox config` 里的 `connection.domain`（如 `localhost:8080`） |
| **AIO API（容器内）** | 经 Server 代理的 endpoint | `defaults.aio_port`（默认 **8080**），健康检查 `GET /v1/shell/sessions` |

配置 Server 时请始终让 `connection.domain` 与 `opensandbox-server` 监听端口一致；**不要**把 Server 端口写成容器内其它服务端口。

---

## 配置

**优先级**（高 → 低）：全局 CLI 参数 → 环境变量 → `~/.allox/config.toml` → 代码内默认值。

### 初始化

```bash
allox config init
allox config set connection.domain localhost:8080
allox config set connection.protocol http
allox config show
allox config path
```

### 环境变量（可选）

| 变量 | 对应配置 |
|------|----------|
| `ALLOX_DOMAIN` / `OPEN_SANDBOX_DOMAIN` | `connection.domain` |
| `ALLOX_API_KEY` / `OPEN_SANDBOX_API_KEY` | `connection.api_key` |
| `ALLOX_PROTOCOL` | `connection.protocol` |

### 默认值（未在 config 中覆盖时）

| 项 | 默认值 |
|----|--------|
| `defaults.image` | `ghcr.io/agent-infra/sandbox:latest` |
| `defaults.entrypoint` | `["/opt/gem/run.sh"]` |
| `defaults.timeout` | `30m` |
| `defaults.aio_port` | `8080` |
| `defaults.aio_health_path` | `/v1/shell/sessions` |
| `defaults.ready_timeout` | `30s` |
| `defaults.skip_health_check` | `false`（code-interpreter 等非 AIO 镜像设为 `true`） |

生产环境请 pin 镜像 tag，避免使用裸 `latest`。

### 自定义 AIO 镜像（阶段 3）

在官方镜像上叠加依赖与服务，换 tag 即可升级，CLI 无需改动：

```bash
cd docker && chmod +x build.sh && ./build.sh
allox config set defaults.image allox/aio-custom:v1
allox sandbox create -o json
```

详见 [docs/CUSTOM_IMAGE.md](./docs/CUSTOM_IMAGE.md)。Code Interpreter 轻量沙箱见 [docs/CODE_INTERPRETER.md](./docs/CODE_INTERPRETER.md)（`--profile code`）。

### 指定配置文件 / Profile

```bash
# 显式配置文件
allox --config ~/.allox/dev.toml sandbox list

# Profile 快捷方式（映射到 ~/.allox/<profile>.toml）
allox --profile dev sandbox create -o json
allox --profile staging sandbox list
allox --profile prod sandbox list
```

#### 多环境示例（dev / staging / prod）

```bash
# dev — 本机 OpenSandbox
allox config init --force   # 先初始化默认 config.toml 作模板
cp ~/.allox/config.toml ~/.allox/dev.toml
allox --config ~/.allox/dev.toml config set connection.domain localhost:8080

# staging — 内网测试集群
cp ~/.allox/config.toml ~/.allox/staging.toml
allox --config ~/.allox/staging.toml config set connection.domain staging-sandbox.internal:8080
allox --config ~/.allox/staging.toml config set connection.protocol http

# prod — 生产（HTTPS + API Key）
cp ~/.allox/config.toml ~/.allox/prod.toml
allox --config ~/.allox/prod.toml config set connection.domain sandbox.example.com
allox --config ~/.allox/prod.toml config set connection.protocol https
allox --config ~/.allox/prod.toml config set connection.api_key YOUR_KEY
allox --config ~/.allox/prod.toml config set defaults.image ghcr.io/agent-infra/sandbox:<pinned-tag>
```

或使用 `--profile dev|staging|prod`（等价于 `--config ~/.allox/<profile>.toml`）。

---

## 快速开始

**前置**：已完成上文 [平台准备](#平台准备拉取镜像与启动-opensandbox-server)（Docker、AIO 镜像、`opensandbox-server` 均在运行）。

```bash
# 终端 2 — CLI（Server 已在另一终端运行）
cd allox-cli
source .venv/bin/activate   # 若尚未 activate

# 创建沙箱（JSON 便于脚本解析 id、aio_url；自动写入当前 session）
allox sandbox create -o json

# 省略 sandbox_id（使用当前 session）
allox session current
allox aio exec ls -la
allox aio screenshot -f test.png
allox sandbox kill
```

端到端自动化（需 Docker + Server）：

```bash
uv run pytest -m integration tests/test_integration_e2e.py -v
```

---

## 全局选项

所有子命令均可使用：

```bash
allox [全局选项] <命令组> <子命令> ...
```

| 选项 | 说明 |
|------|------|
| `--domain` | 覆盖 OpenSandbox Server 地址（host:port） |
| `--api-key` | API Key（Header `OPEN-SANDBOX-API-KEY`） |
| `--protocol` | `http` 或 `https` |
| `--config PATH` | 配置文件路径 |
| `--profile dev\|staging\|prod` | Profile 配置文件（`~/.allox/<profile>.toml`） |
| `-v`, `--verbose` | 打印 HTTP / 健康检查细节 |
| `--no-color` | 关闭 Rich 彩色输出 |
| `-o`, `--output` | 部分子命令支持，见下文 |

---

## 命令参考

### `allox sandbox` — 生命周期（OpenSandbox）

| 子命令 | 作用 |
|--------|------|
| `create` | 创建 AIO 沙箱并等待健康检查（自动写入 session） |
| `list` | 列出沙箱（Rich 表格） |
| `get [<id>]` | 查看单个沙箱 |
| `endpoint [<id>]` | 打印 AIO 门户 URL |
| `renew [<id>]` | 续期沙箱 |
| `kill [<id>]` | 销毁沙箱 |

`[<id>]` 可省略，默认使用当前 session。

#### `sandbox create`

```bash
allox sandbox create [选项]
```

| 选项 | 说明 |
|------|------|
| `-i`, `--image` | 镜像（默认见 config `defaults.image`） |
| `-t`, `--timeout` | 存活时间，如 `30m`、`1h`；`none` 表示需手动 `kill` |
| `-m`, `--metadata` | 元数据，可重复：`--metadata key=value` |
| `-e`, `--env` | 环境变量，可重复：`--env KEY=VALUE` |
| `--entrypoint` | 覆盖入口，可多次传入参数；默认 `/opt/gem/run.sh` |
| `--skip-health-check` | 不等待 AIO `/v1` 就绪 |
| `--ready-timeout` | 健康检查最长等待，如 `60s`（覆盖 config `defaults.ready_timeout`） |
| `-o json` | 输出 JSON：`id`、`image`、`aio_url`、`aio_ready_seconds`、`entrypoint` |

示例：

```bash
allox sandbox create -o json
allox sandbox create -e DEBUG=1 -m tool=allox --timeout 10m
allox sandbox create --timeout none -o json
allox sandbox renew --timeout 30m -o json
```

---

### `allox session` — 本地会话

| 子命令 | 作用 |
|--------|------|
| `current` | 显示当前 session（`~/.allox/sessions.json`） |
| `use <id>` | 切换当前 session |
| `clear` | 清除当前 session |

---

### `allox aio` — Agent 能力（agent-sandbox `/v1`）

`<sandbox-id>` 可省略（使用当前 session）。

| 子命令 | 作用 |
|--------|------|
| `exec` | 在沙箱内执行 shell 命令 |
| `read` | 读取沙箱内文件 |
| `screenshot` | 浏览器截图保存到本地 |
| `jupyter run` | 经 Jupyter 内核执行 Python |
| `browser info` | 输出 CDP / VNC URL（供 Playwright 等） |

#### `aio exec`

```bash
allox aio exec [选项] [<sandbox-id>] <命令...>
```

| 选项 | 说明 |
|------|------|
| `-w`, `--workdir` | 工作目录（沙箱内绝对路径） |
| `--timeout` | 命令最长运行秒数（默认 60）；超时后强制终止命令，CLI 返回 124 |

```bash
allox aio exec ls -la
allox aio exec -w /home/gem ls -la
allox aio exec --timeout 1 sleep 3
allox aio exec -o json ls
```

JSON 输出包含 `session_id`、`status`、`output`、`exit_code`、`message` 和 `error`。
远端命令失败时，Allox 会将远端退出码传给本地 CLI；硬超时时本地退出码为 `124`。

#### `aio read`

```bash
allox aio read <sandbox-id> <容器内路径> [-o json]
```

#### `aio screenshot`

```bash
allox aio screenshot <sandbox-id> [-f 本地路径] [-o json]
# 默认保存 screenshot.png
allox aio screenshot <id> -f test.png
```

#### `aio jupyter run`

```bash
allox aio jupyter run <sandbox-id> -c '<python 代码>' [选项]
```

| 选项 | 说明 |
|------|------|
| `-c`, `--code` | 必填，要执行的 Python |
| `--timeout` | 执行超时（秒） |
| `--session-id` | 复用已有 Jupyter 会话 |
| `-o json` | 完整执行结果（含 `status`、`outputs`） |

```bash
allox aio jupyter run <id> -c "print(2+2)" -o json
```

#### `aio browser info`

```bash
allox aio browser info <sandbox-id> [-o json]
```

JSON / 表格中包含 `cdp_url`、`vnc_url`、`cdp_ui_url`、`viewport` 等，便于连接 Playwright。

#### `aio mcp` — 沙箱内 MCP 服务

通过 AIO REST `/v1/mcp/*` 访问沙箱内 MCP server。**调用前先盘点**（server / 工具名因镜像而异）。详见 [docs/MCP_SERVERS.md](docs/MCP_SERVERS.md)。

| 子命令 | 作用 |
|--------|------|
| `servers [sandbox-id]` | 列出 MCP server |
| `tools [sandbox-id] <server>` | 列出某 server 的工具与描述 |
| `call [sandbox-id] <server> <tool>` | 调用 MCP 工具（**tool 须为 tools 列表中的完整名称**） |

```bash
allox aio mcp servers -o json
allox aio mcp tools browser -o json | jq '.tools[].name'
allox aio mcp call browser browser_navigate --args '{"url":"https://example.com"}'
allox aio mcp call browser browser_screenshot -o json
```

`shell` / `file` 等 server 在部分镜像中未启用（404）；此时用 `allox aio exec` / `aio read`。browser 工具名通常为 `browser_navigate` 而非简写 `navigate`。

**分工**：日常 shell / 读文件优先 `aio exec` / `aio read`；browser MCP 或 Agent 统一工具面时用 `aio mcp call`。截图到本地仍推荐 `aio screenshot`。

---

### `allox config` — 本地配置

| 子命令 | 作用 |
|--------|------|
| `init` | 创建 `~/.allox/config.toml` 模板 |
| `show` | 显示合并后的有效配置（`-o json`） |
| `set <key> <value>` | 设置项，如 `connection.domain localhost:8080` |
| `path` | 打印配置文件路径 |

```bash
allox config init --force   # 覆盖已有文件
allox config set defaults.image ghcr.io/agent-infra/sandbox:<tag>
```

---

## 输出格式

| 格式 | 说明 |
|------|------|
| `table` | Rich 表格 / 面板（默认，适合人工阅读） |
| `json` | JSON（脚本化首选） |
| `yaml` | YAML（需 PyYAML，与 osb 对齐） |
| `raw` | 纯文本（exec/read 默认） |

| 命令类型 | 典型 `-o` 值 |
|----------|----------------|
| `sandbox create` / `list` / `get` / `endpoint` / `renew` / `kill` | `table`（默认）、`json`、`yaml` |
| `aio exec` / `aio read` | `raw`（默认）、`json` |
| `aio screenshot` / `browser info` / `aio mcp servers|tools` / `session` | `table`、`json`、`yaml` |
| `aio mcp call` | `raw`（默认）、`json` |
| `config show` | `table`、`json` |
| `run` / `file cat` | `raw`（默认）、`json` |

### 与 osb 输出格式对照

| 场景 | allox | osb |
|------|-------|-----|
| 沙箱列表 | `-o table\|json\|yaml` | 同 |
| 创建结果 | `-o table\|json\|yaml` | 同 |
| 命令执行（execd） | `allox run` → `-o raw\|json` | `osb command run` → `-o raw` |
| AIO shell | `allox aio exec` → `-o raw\|json` | N/A（osb 无 AIO 面） |

脚本化推荐：创建与销毁统一使用 `-o json`，用 `jq` 解析字段。

---

## execd 运维命令（可选）

Agent 业务优先 **`allox aio *`**（容器内 `/v1`）；容器运维、与 osb 对齐时可选 execd 路径：

| 命令 | API | 说明 |
|------|-----|------|
| `allox run [<id>] -- <cmd>` | `sandbox.commands.run` | execd 执行命令（非 AIO shell） |
| `allox file cat [<id>] <path>` | `sandbox.files.read_file` | execd 读文件 |
| `allox file write [<id>] <path>` | `sandbox.files.write_file` | execd 写文件 |

```bash
allox run -- ls -la
allox file cat /etc/hostname
echo "hello" | allox file write /tmp/hello.txt
```

---

## 测试

```bash
# 冒烟 + 单元（无需 Docker）
uv run pytest -q

# 集成（需 Server + Docker）
uv run pytest -m integration tests/test_integration_e2e.py -v

# 自定义镜像集成（需先 docker/build.sh）
uv run pytest -m integration tests/test_integration_custom_image.py -v
```

详见 [docs/PHASE1_TESTING.md](./docs/PHASE1_TESTING.md)、[docs/PHASE2_TESTING.md](./docs/PHASE2_TESTING.md) 与 [docs/PHASE3_TESTING.md](./docs/PHASE3_TESTING.md)（含 pytest 输出、CLI 实跑摘录与手工勾选清单）。

---

## 与 `osb` 的分工

| 场景 | 建议工具 |
|------|----------|
| 日常 Agent 流程、AIO 默认镜像 | **allox** |
| 对齐 OpenSandbox 官方 CLI、深度排障 | **osb**（`pip install opensandbox-cli`） |

Agent 业务优先使用 `allox aio *`（容器内 `/v1`）；容器运维可选用 `allox run` / `allox file *`（execd）或 `osb`，**勿在同一操作混用两套 API**。

---

## 许可证

Apache-2.0
