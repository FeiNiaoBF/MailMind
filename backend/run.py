"""
应用启动文件
"""
import os
from dotenv import load_dotenv

from app import create_app

# 加载环境变量
load_dotenv()


def main():
    """主函数"""
    # 创建应用实例
    app = create_app()

    # 获取配置
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')

    # 启动应用
    app.run(
        host=host,
        port=port,
    )


if __name__ == '__main__':
    main()
