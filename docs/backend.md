# 后端设计

首先，这个项目是一个前后端分离的项目，前端使用React NextJS。后端使用 Python Flask，前端和后端之间通过 `RESTful API` 进行通信。

## 核心模块

后端可以将登录的邮箱读取邮件存到数据库里面，这是一个后端的定时任务，而当前端使用AI对话式来分析邮箱的时候，比如：“分析我一个月的邮件信息，将相同类型的归纳”，而后端使用AI
API 向数据库读取邮件内容并分析最后将内容发送到邮箱和在对话式页面显示

### 邮箱模块

使用 python 自带的 `email` 库来处理邮件内容。
流程：

```mermaid
sequenceDiagram
    participant 邮箱登录
    participant 邮箱采集
    participant 邮箱发送
    邮箱登录 ->> 邮箱采集: 登录邮箱
    邮箱采集 ->> 邮箱发送: 获取邮件内容
    邮箱发送 ->> 邮箱采集: 发送邮件
```

#### 邮箱登录模块

登录我打算使用验证码登录，因为密码登录的话，需要存储密码，这样不安全。

不对，使用验证码有点麻烦，我打算使用Gmail API登录，然后使用 `OAuth2` 来授权，这样更好点（可能。

| 组件   | 技术方案                  | 特性优势                                   |
|------|-----------------------|----------------------------------------|
| 协议支持 | IMAP/SMTP + Gmail API | 双协议支持                                  |
| 认证方式 | OAuth2.0 + Token      | 生产环境使用Gmail OAuth，测试环境使用Mailtrap Token |
| 任务调度 | APScheduler           | 支持Cron式调度，动态任务管理                       ||
| 配置管理 | 环境变量 + Config类        | 实现开发/生产环境零修改切换                         |

[OAuth2.0](https://developers.google.com/identity/protocols/oauth2)

```mermaid
sequenceDiagram
    participant User
    participant APP
    participant Gmail Auth
    participant Gmail Resource
    User ->> APP: 点击登录
    APP ->> Gmail Auth: Authorize Service
    Gmail Auth ->> User: 显出登录页面
    User ->> Gmail Auth: 请求授权
    Gmail Auth ->> APP: 返回授权码`authorization_url`
    APP ->> Gmail Auth: 通过授权码获取令牌`fetch_token`
    Gmail Auth ->> APP: 返回令牌
    APP ->> Gmail Resource: 使用令牌访问资源
    Gmail Resource ->> APP: 返回资源
    APP ->> Gmail Auth: 刷新令牌`refresh_token`
    Gmail Auth ->> APP: 返回新令牌
```

#### 完整令牌处理流程

1. 初始授权请求 → 生成 `authorization_url`
   2 .接收回调 → 通过 `fetch_token` 获取令牌
2. 自动刷新 → 当访问令牌过期时自动获取新令牌
3. 安全存储 → 将刷新令牌持久化存储

[Gmail Auth](https://developers.google.com/identity/protocols/oauth2/scopes?hl=zh-cn#gmail)

[Gmail API](https://developers.google.com/workspace/gmail/api/reference/rest?apix=true&hl=zh-cn)

1. 用户输入邮箱地址
2. 指向Gmail登录页面
3. 用户登录Gmail并授权
4. 返回授权码
5. 使用授权码获取 `access_token` 和 `refresh_token`
6. 使用 `access_token` 登录邮箱
7. 获取邮件内容
8. AI分析内容
9. 发送邮件

#### 邮箱采集模块

使用 `IMAP` 协议登录邮箱，获取邮件内容。

为了更好的利用AI分析！

1. 预处理。将邮件格式转为txt text 内容
2. 内容分析。摘要生成、关键字等
3. 存储。存储到数据库
4. Error Handling。处理异常情况

#### 邮箱发送模块

使用 `SMTP` 协议发送邮件。

学习一下邮箱的操作，额，我是不是不知量力了，好复杂

```mermaid
sequenceDiagram
    participant S as 同步服务
    participant D as 数据库
    participant M as 邮件服务器
    S ->> M: 连接IMAP（使用uidvalidity验证）
    M -->> S: 返回当前邮箱状态
    S ->> D: 查询最后同步UID（select max(uid) where user_id=?)
    D -->> S: 返回最后UID=1000
    S ->> M: 获取UID>1000的邮件
    M -->> S: 返回新邮件数据

    loop 处理每封邮件
        S ->> D: 检查唯一约束(user_id+uid)
        alt 新邮件
            S ->> D: 插入完整邮件数据
        else 已存在
            S ->> D: 更新labels等元数据
        end
    end

    S ->> D: 记录同步日志
```

### 数据存储模块

使用 SQLite 数据库存储邮件内容。利用 ORM 框架 `SQLAlchemy` 来统一 ORM 模型定义范式.

#### 数据库设计

```mermaid
erDiagram
    USER ||--o{ EMAIL: "1:N"
    USER ||--o{ VERIFICATION_CODE: "1:N"
    USER ||--o{ TASK_LOG: "1:N"
    EMAIL ||--o{ ANALYSIS: "1:N"

    USERS {
        int id PK
        string email "邮箱地址-UNIQUE"
        boolean is_active "是否激活"
        datetime last_login "最后登录时间"
        datetime created_at
        string oauth_uid "OAuth UID"
        json oauth_token "OAuth Token"
        string oauth_provider "OAuth Provider"
    }

    EMAILS {
        bigint uid PK "IMAP UID"
        int id FK "对应用户ID"
        string from "寄件方"
        string to "发送方"
        string subject
        text body
        datetime rece_date "发件时间"
        json attachments "JSON存储附件信息"
        json labels "标签分类"
        datetime created_at "收集时间"
    }

    ANALYSIS {
        int id PK
        bigint email_uid FK
        string analysis_type "summary/keywords/action_items"
        json result "分析结果"
        datetime analyzed_at
        string model_used "如gpt"
    }

    TASK_LOG {
        int id PK
        string task_type "fetch/analyze/send"
        datetime start_time
        datetime end_time
        bool success
        string error_msg
    }
```

数据库模式应包括三个模型：“**MAIL**”，“**ANALYSIS**”和“**TASK_LOG**”。

大纲流程：

```text
邮箱服务器 → 定时任务 → EMAIL表 → AI分析 → ANALYSIS表
```

数据流程：

```text
用户登录 → 生成验证码 → 验证通过
触发邮箱同步 → 记录TASK_LOG → 存储EMAIL数据
发起分析请求 → 创建ANALYSIS记录 → 更新TASK_LOG状态
```

1. **MAIL**模型应捕获电子邮件元数据，包括发件人、收件人、主题、正文、附件（序列化格式，例如 JSON 或逗号分隔的文件名列表）、标签（序列化格式）和创建时间戳。
2. **ANALYSIS**模型应存储分析结果，通过外键链接回“MAIL”模型，并包括分析类型（例如情绪分析、主题提取）、分析结果本身（序列化格式）、分析的时间戳和使用的
   AI 模型（例如“GPT”、“DeepSeek”）。
3. **TASK_LOG**模型应跟踪任务的执行情况，例如获取、分析和发送电子邮件、记录开始和结束时间、成功状态（布尔值）以及任何错误消息（字符串）。
4. **USER**模型应存储用户信息，包括电子邮件地址、是否激活、最后登录时间和创建时间戳。

### AI 分析模块

#### Flask路由集成

| api                          | 作用      |
|------------------------------|---------|
| `GET/POST: /api/v1/chat`     | 与AI模型对话 |
| `GET/POST: /api/v1/analyze`  | 分析邮件内容  |
| `GET/POST: /api/v1/summary`  | 获取邮件摘要  |
| `GET/POST: /api/v1/keywords` | 获取邮件关键字 |

#### 配置项

```python
# config.py
class Config:
    # OpenAI配置
    OPENAI_API_KEY = "api-key"
    OPENAI_MODEL = "gpt"

    ## 其他
    # 重试策略
    API_RETRY_TIMES = 3
    API_TIMEOUT = 10
```

#### 部署架构

```mermaid
graph TD
    A[客户端] --> B{Flask服务器}
    B --> C[对话管理模块]
    C --> D[OpenAI API]
    B --> G[MySQL日志存储]
    D --> H{响应返回}
```

### 邮件发送模块

## 后端流程

```mermaid
sequenceDiagram
    participant Client
    participant Flask
    participant 邮箱采集
    participant 数据存储
    participant AI 分析模块
    Client ->> Flask: Request
    Flask ->> 邮箱采集: 从邮箱获取数据
    邮箱采集 ->> 数据存储: 存储数据
    邮箱采集 ->> AI 分析模块: 调用AI模型进行分析
    AI 分析模块 ->> 数据存储: Return Result
    数据存储 ->> Flask: Return Result
    Flask ->> Client: Return Result
```
