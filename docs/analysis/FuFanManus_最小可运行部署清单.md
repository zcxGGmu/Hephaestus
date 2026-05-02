# FuFanManus 最小可运行部署清单

## 1. 目标

这份清单的目标不是“生产部署”，而是：

- 在本机把 Part 1 项目跑起来
- 打通前端、后端、数据库、Redis 的最小链路
- 验证注册、登录、进入页面、发起 Agent 任务这条主路径

当前建议以解压后的源码为基准：

- 后端目录：`K:\2025全年班_大模型Agent(4)\实战项目四：“Manus”通用智能体项目开发实战（完结）\_extracted\part1\backend`
- 前端目录：`part 1` 压缩包内的 `frontend`

---

## 2. 最小运行所需组件

从课件、脚本和源码看，最小运行依赖如下：

1. `Node.js`
2. `Python 3.11`
3. `PostgreSQL`
4. `Redis`
5. 模型 API Key

严格来说，沙箱服务在很多高级能力里会用到，但如果目标只是先跑起最小链路，可以先把它视为第二阶段配置项。

---

## 3. 推荐的最小运行顺序

推荐顺序如下：

1. 先启动 PostgreSQL
2. 再启动 Redis
3. 配置后端 `.env`
4. 初始化数据库表
5. 启动后端 API
6. 启动后端 Worker
7. 配置前端 `.env.local`
8. 启动前端

---

## 4. 后端最小运行步骤

### 4.1 进入后端目录

```powershell
cd "K:\2025全年班_大模型Agent(4)\实战项目四：“Manus”通用智能体项目开发实战（完结）\_extracted\part1\backend"
```

### 4.2 创建 Python 环境

课程里推荐 Conda，但只要是 Python 3.11 环境即可。  
如果用 Conda：

```powershell
conda create -n my_fufanmanus python=3.11 -y
conda activate my_fufanmanus
```

如果不用 Conda，也可以使用 venv。

### 4.3 安装依赖

当前后端 `requirements.txt` 至少包含：

- `fastapi`
- `asyncpg`
- `redis`
- `dramatiq`
- `google-adk`
- `litellm`

安装方式：

```powershell
pip install -r requirements.txt
```

### 4.4 配置数据库

可以直接运行项目自带脚本：

```powershell
python scripts/01_setup_database.py
```

它会：

- 测试 PostgreSQL 连通性
- 如有需要尝试创建数据库
- 自动写入 `.env`

如果你想手工配置，最核心的是：

```env
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/fufanmanus
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 4.5 配置 Redis

运行：

```powershell
python scripts/02_setup_redis.py
```

它会把下面这些字段补入 `.env`：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

### 4.6 初始化数据库表

运行：

```powershell
python scripts/03_init_fufanmanus_table.py
```

该脚本会执行：

- `migrations/fufanmanus.sql`

并创建核心表，包括：

- `users`
- `projects`
- `threads`
- `messages`
- `agents`
- `agent_runs`
- `sessions`
- `events`

### 4.7 配置模型相关环境变量

这是后端真正能执行 Agent 的关键。  
至少需要配置一组可用模型。

从源码与课件看，最关键的是：

```env
LOGGING_LEVEL=WARNING
ENV_MODE=local

OPENAI_API_KEY=你的Key
DEEPSEEK_API_KEY=你的Key
DEEPSEEK_API_BASE=https://api.deepseek.com
MODEL_TO_USE=deepseek/deepseek-chat
```

建议：

- 不要直接使用课件里的示例密钥
- 全部替换成你自己的有效 Key

### 4.8 可选配置

如果你后续要启用完整能力，可能还会用到：

- `LANGFUSE_*`
- `E2B_API_KEY`
- `SANDBOX_TEMPLATE_ID`
- `TAVILY_API_KEY`
- `FIRECRAWL_API_KEY`

但最小跑通阶段可以先不全配。

---

## 5. 启动后端服务

### 5.1 启动 API

在后端目录执行：

```powershell
python api.py
```

或者更标准一些：

```powershell
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 启动 Worker

另开一个终端，在同一后端目录执行：

```powershell
dramatiq run_agent_background
```

如果你的环境里 `dramatiq` 可执行不可用，也可以尝试：

```powershell
python -m dramatiq run_agent_background
```

### 5.3 健康检查

后端启动后，应优先检查：

- `http://localhost:8000`
- `http://localhost:8000/api/health`

如果没有健康接口，也至少要确认服务端口已监听且日志无初始化报错。

---

## 6. 前端最小运行步骤

### 6.1 进入前端目录

前端目录来自 `part 1` 的 `frontend.zip`。  
如果你已手动解压，进入对应目录即可。

### 6.2 安装依赖

```powershell
npm install
```

如果依赖锁文件一致，也可以用：

```powershell
npm ci
```

### 6.3 配置前端环境变量

根据 `frontend/env.example`，创建 `.env.local`：

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api
NEXT_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_ENV_MODE=LOCAL
NEXT_PUBLIC_TOLT_REFERRAL_ID=
```

### 6.4 启动前端

```powershell
npm run dev
```

默认访问地址：

```text
http://localhost:3000
```

---

## 7. 最小验证路径

项目跑起来后，建议按下面顺序验证：

1. 打开前端首页
2. 进入登录/注册页
3. 完成注册
4. 使用账号登录
5. 进入 dashboard
6. 创建项目或线程
7. 发送一条消息
8. 观察后端日志与 Worker 日志中是否出现 Agent run

如果这条链路跑通，说明最小系统已经成立。

---

## 8. 你最可能遇到的问题

### 8.1 数据库连接失败

优先检查：

- PostgreSQL 服务是否已启动
- 用户名密码是否正确
- `DATABASE_URL` 是否指向存在的数据库

### 8.2 Redis 连接失败

优先检查：

- Redis 是否已启动
- 密码是否为空或填写正确
- `.env` 中 `REDIS_HOST/PORT/PASSWORD` 是否一致

### 8.3 前端能开，登录失败

优先检查：

- `NEXT_PUBLIC_BACKEND_URL` 是否正确
- 后端认证接口是否正常
- 浏览器里是否有 `auth_session` 被写入

### 8.4 登录成功，但 Agent 不运行

优先检查：

- Worker 是否已经启动
- Redis 是否正常
- 模型 Key 是否有效
- `MODEL_TO_USE` 是否指向可用模型

### 8.5 页面打开后部分功能报错

这是很可能的，因为当前项目仍带有迁移期遗留逻辑。  
优先看：

- 后端日志
- Worker 日志
- 浏览器控制台

---

## 9. Docker 相关判断

后端源码里确实存在：

- `Dockerfile`
- `docker-compose.yml`

但当前交付包更偏课程环境，本地脚本方式更容易排错。  
建议顺序是：

1. 先按脚本方式跑通
2. 再考虑转成 Docker 化运行

否则你会同时面对：

- 依赖问题
- 容器网络问题
- 环境变量问题
- 卷挂载问题

定位难度会明显上升。

---

## 10. 关于安全的明确提醒

课件和样例文件中出现过真实格式的密钥内容。  
实际运行时请务必：

1. 使用你自己的 Key
2. 不要把有效 Key 回写进课程原文件
3. 不要把 `.env` 提交到仓库
4. 如果你怀疑历史密钥可用，先全部作废再使用

---

## 11. 建议的下一步

如果你已经准备继续深入，建议按下面顺序推进：

1. 先解压前端源码到固定目录
2. 实际跑起前后端
3. 记录第一轮报错
4. 再针对报错逐项修复

这样后续分析才会从“静态读代码”进入“动态调系统”阶段。
