from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db

def create_app():
    print("🚀 create_app 被调用")
    app = Flask(__name__)

    # 基本配置
    app.config['JWT_SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ai_checkin.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ 设置 CORS
    CORS(app,
         resources={r"/api/*": {"origins": "http://localhost:5173"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "OPTIONS"]
    )

    # 初始化扩展
    JWTManager(app)
    db.init_app(app)

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.checkin import checkin_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(checkin_bp, url_prefix='/api/checkin')

    # 静态资源服务（上传的图像）
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('uploads', filename)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    print("🚀 正在启动 Flask 应用")
    app = create_app()
    app.run(debug=True)
