import os
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.logger.info('应用启动')
    app.logger.debug(f'环境: {app.config.get("FLASK_ENV", "development")}')
    app.logger.debug(f'调试模式: {app.debug}')
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
