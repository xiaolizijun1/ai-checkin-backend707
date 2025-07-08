import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Checkin
from datetime import datetime
from werkzeug.utils import secure_filename
import torch
from torchvision import models, transforms
from PIL import Image

checkin_bp = Blueprint('checkin', __name__)

# ✅ 加载模型（简单示例用 ResNet18）
model = models.resnet18(pretrained=True)
model.eval()

# ✅ 图像预处理
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# ✅ 上传识别接口
@checkin_bp.route('/', methods=['POST', 'OPTIONS'])  # ✅ 注意：结尾是 '/'，必须与前端一致
@jwt_required(optional=True)  # ✅ 允许 OPTIONS 请求跳过认证
def upload_checkin():
    if request.method == 'OPTIONS':
        print("⚙️ 收到 OPTIONS 预检请求，放行")
        return '', 204

    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({'msg': '未登录，不能打卡'}), 401

    if 'image' not in request.files:
        return jsonify({'msg': '未找到图像文件'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'msg': '文件名为空'}), 400

    filename = secure_filename(file.filename)
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    upload_path = os.path.join('uploads', filename)
    file.save(upload_path)

    # 图像识别逻辑
    try:
        image = Image.open(upload_path).convert('RGB')
        input_tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            output = model(input_tensor)
        _, predicted = torch.max(output, 1)
        result = f"Class-{predicted.item()}"
    except Exception as e:
        return jsonify({'msg': f'图像识别出错: {str(e)}'}), 500

    # 保存打卡记录
    user = User.query.filter_by(username=current_user).first()
    checkin = Checkin(
        user_id=user.id,
        image_path=upload_path,
        result=result,
        timestamp=datetime.now()
    )
    db.session.add(checkin)
    db.session.commit()

    return jsonify({'msg': '识别成功', 'result': result}), 200

# ✅ 获取打卡历史记录
@checkin_bp.route('/history', methods=['GET'])
@jwt_required()
def get_checkin_history():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()

    checkins = Checkin.query.filter_by(user_id=user.id).order_by(Checkin.timestamp.desc()).all()

    history = []
    for c in checkins:
        history.append({
            'timestamp': c.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'result': c.result,
            'image_url': f'/static/{os.path.basename(c.image_path)}'
        })

    return jsonify({'history': history}), 200
