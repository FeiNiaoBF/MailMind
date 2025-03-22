# MailMind Backend

MailMind是一个智能邮件管理系统的后端服务。

## 技术栈

- Python 3.11+
- Flask 3.1+
- Poetry（包管理）
- JWT认证
- 结构化日志系统

## 开发环境设置

1. 安装Poetry（如果还没有安装）:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. 安装项目依赖:

```bash
poetry install
```

3. 激活虚拟环境:

```bash
poetry shell
```

4. 创建.env文件:

```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
PORT=5000
```

5. 运行开发服务器:

```bash
poetry run python run.py
```

## 生产环境部署

1. 设置环境变量:

```bash
export FLASK_ENV=production
export SECRET_KEY=<your-production-secret-key>
export JWT_SECRET_KEY=<your-production-jwt-secret>
export DATABASE_URI=<your-production-database-uri>
```

2. 使用gunicorn启动服务:

```bash
poetry run gunicorn run:create_app()
```

## 项目结构

```
backend/
├── app/
│   ├── api/           # API蓝图和路由
│   ├── config/        # 配置文件
│   └── utils/         # 工具函数
├── tests/             # 测试文件
├── pyproject.toml     # 项目配置和依赖
└── run.py            # 应用入口点
```

## API文档

### 基础端点

- `GET /api/health` - 健康检查
- `GET /api/error-test` - 错误处理测试

## 开发指南

- 使用`poetry add <package>`添加新依赖
- 使用`poetry add -D <package>`添加开发依赖
- 运行测试: `poetry run pytest`
- 代码格式化: `poetry run black .`
- 类型检查: `poetry run mypy .`
