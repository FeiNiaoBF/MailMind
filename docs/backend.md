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

#### 邮箱采集模块

使用 `IMAP` 协议登录邮箱，获取邮件内容。

#### 邮箱发送模块

使用 `SMTP` 协议发送邮件。

### 数据存储模块

使用 SQLite 数据库存储邮件内容。利用 ORM 框架 `SQLAlchemy` 来统一 ORM 模型定义范式.

#### 数据库设计

```mermaid
erDiagram
    MAIL ||--o{ ANALYSIS: has

    MAIL {
        string uid PK "IMAP UID"
        string from
        string to
        string subject
        text body
        datetime date "发件时间"
        json attachments "JSON存储附件信息"
        json labels "标签分类"
        datetime created_at "收集时间"
    }

    ANALYSIS {
        int id PK
        string mail_uid FK
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

1. **MAIL**模型应捕获电子邮件元数据，包括发件人、收件人、主题、正文、附件（序列化格式，例如 JSON 或逗号分隔的文件名列表）、标签（序列化格式）和创建时间戳。
2. **ANALYSIS**模型应存储分析结果，通过外键链接回“MAIL”模型，并包括分析类型（例如情绪分析、主题提取）、分析结果本身（序列化格式）、分析的时间戳和使用的
   AI 模型（例如“GPT”、“DeepSeek”）。
3. **TASK_LOG**模型应跟踪任务的执行情况，例如获取、分析和发送电子邮件、记录开始和结束时间、成功状态（布尔值）以及任何错误消息（字符串）。

### AI 分析模块

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
