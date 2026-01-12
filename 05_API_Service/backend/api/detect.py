"""
推理检测模块 API
处理图片上传、调用C++推理、上传OSS、存储记录等业务
"""
from flask import request, jsonify, current_app
from api import detect_bp
from api.auth import token_required
from models import db
from models.record import Record
from utils.cpp_client import get_cpp_client
from utils.oss_client import get_oss_client
from utils.image_proc import get_image_processor
from werkzeug.utils import secure_filename
import os
import uuid
import time
from config import Config


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@detect_bp.route('/image', methods=['POST'])
@token_required
def detect_image(current_user):
    """
    上传并检测图片
    
    POST /api/v1/detect/image
    Header: Authorization: Bearer <token>
    Content-Type: multipart/form-data
    Form Data: 
        - file: 图片文件
        - model_type: 模型类型(可选，默认v11-nodecode-fp32)
        - conf_threshold: 置信度阈值(可选，默认0.25)
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "检测完成",
            "data": {
                "record_id": 1024,
                "oss_url": "http://...",
                "result_oss_url": "http://...",
                "inference_time_ms": 25.5,
                "defect_count": 2,
                "objects": [...]
            }
        }
    """
    try:
        # 1. 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'msg': '没有上传文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'code': 400,
                'msg': '文件名为空'
            }), 400
        
        # 2. 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'code': 400,
                'msg': f'不支持的文件类型，仅支持: {", ".join(Config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # 3. 获取可选参数
        model_type = request.form.get('model_type', Config.DEFAULT_MODEL_TYPE)
        conf_threshold = float(request.form.get('conf_threshold', Config.DEFAULT_CONFIDENCE_THRESHOLD))
        
        # 4. 生成唯一文件名并保存到本地
        original_filename = secure_filename(file.filename)
        file_ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        local_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(local_path)
        print(f"[检测] 文件已保存到本地: {local_path}")
        
        # 5. 调用C++推理服务
        cpp_client = get_cpp_client()
        cpp_result = cpp_client.predict(
            image_path=local_path, 
            conf_threshold=conf_threshold, 
            model_type=model_type,
            auto_convert_path=True
        )
        
        if not cpp_result:
            # 清理本地文件
            os.remove(local_path)
            return jsonify({
                'code': 500,
                'msg': 'C++推理服务调用失败'
            }), 500
        
        # 6. 解析C++返回的结果
        detections = cpp_result.get('data', [])
        inference_time_ms = cpp_result.get('inference_time_ms', 0)
        
        print(f"[检测] C++推理完成，检测到 {len(detections)} 个目标")
        
        # 7. 上传原图到OSS
        oss_client = get_oss_client()
        oss_url = oss_client.upload_file(local_path, prefix='originals')
        
        if not oss_url:
            os.remove(local_path)
            return jsonify({
                'code': 500,
                'msg': 'OSS上传失败'
            }), 500
        
        # 8. 绘制检测框并保存结果图
        result_filename = f"{uuid.uuid4().hex}_result{file_ext}"
        result_local_path = os.path.join(Config.UPLOAD_FOLDER, result_filename)
        
        image_processor = get_image_processor()
        draw_success = image_processor.draw_detection_boxes(
            local_path, 
            detections, 
            result_local_path
        )
        
        result_oss_url = None
        if draw_success:
            # 上传结果图到OSS
            result_oss_url = oss_client.upload_file(result_local_path, prefix='results')
            # 删除本地结果图
            os.remove(result_local_path)
        
        # 9. 保存检测记录到数据库
        record = Record(
            user_id=current_user.id,
            filename=original_filename,
            oss_url=oss_url,
            result_oss_url=result_oss_url,
            model_type=model_type,
            inference_time_ms=inference_time_ms,
            conf_threshold=conf_threshold
        )
        record.set_objects(detections)
        
        db.session.add(record)
        db.session.commit()
        
        print(f"[检测] 记录已保存到数据库，ID: {record.id}")
        
        # 10. 清理本地原图
        os.remove(local_path)
        
        # 11. 返回结果
        return jsonify({
            'code': 200,
            'msg': '检测完成',
            'data': {
                'record_id': record.id,
                'oss_url': oss_url,
                'result_oss_url': result_oss_url,
                'inference_time_ms': inference_time_ms,
                'defect_count': record.defect_count,
                'objects': detections
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[检测异常] {e}")
        
        # 清理可能残留的本地文件
        try:
            if 'local_path' in locals() and os.path.exists(local_path):
                os.remove(local_path)
            if 'result_local_path' in locals() and os.path.exists(result_local_path):
                os.remove(result_local_path)
        except:
            pass
        
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500


@detect_bp.route('/health', methods=['GET'])
def check_cpp_health():
    """
    检查C++服务健康状态
    
    GET /api/v1/detect/health
    
    Returns:
        JSON: {"code": 200, "msg": "C++服务运行正常", "data": {...}}
    """
    try:
        cpp_client = get_cpp_client()
        health_info = cpp_client.health_check()
        
        if health_info.get('status') == 'running':
            return jsonify({
                'code': 200,
                'msg': 'C++服务运行正常',
                'data': health_info
            }), 200
        else:
            return jsonify({
                'code': 503,
                'msg': 'C++服务异常',
                'data': health_info
            }), 503
            
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'健康检查失败: {str(e)}'
        }), 500


@detect_bp.route('/batch', methods=['POST'])
@token_required
def detect_batch(current_user):
    """
    批量上传并检测图片
    
    POST /api/v1/detect/batch
    Header: Authorization: Bearer <token>
    Content-Type: multipart/form-data
    Form Data: 
        - files: 多个图片文件（字段名都是 files）
        - model_type: 模型类型(可选，默认v11-nodecode-fp32)
        - conf_threshold: 置信度阈值(可选，默认0.25)
    
    Returns:
        JSON: {
            "code": 200,
            "msg": "批量检测完成",
            "data": {
                "total": 3,
                "success": 2,
                "failed": 1,
                "results": [...]
            }
        }
    """
    try:
        # 1. 检查是否有文件上传
        if 'files' not in request.files:
            return jsonify({
                'code': 400,
                'msg': '没有上传文件'
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                'code': 400,
                'msg': '文件列表为空'
            }), 400
        
        # 限制最大数量
        MAX_FILES = 20
        if len(files) > MAX_FILES:
            return jsonify({
                'code': 400,
                'msg': f'一次最多上传 {MAX_FILES} 张图片'
            }), 400
        
        # 2. 获取可选参数
        model_type = request.form.get('model_type', Config.DEFAULT_MODEL_TYPE)
        conf_threshold = float(request.form.get('conf_threshold', Config.DEFAULT_CONFIDENCE_THRESHOLD))
        
        # 3. 初始化客户端
        cpp_client = get_cpp_client()
        oss_client = get_oss_client()
        image_processor = get_image_processor()
        
        # 4. 批量处理
        results = []
        success_count = 0
        failed_count = 0
        
        for file in files:
            result = {}
            local_path = None
            result_local_path = None
            
            try:
                # 检查文件名
                if file.filename == '':
                    result = {
                        'filename': 'unknown',
                        'status': 'failed',
                        'error': '文件名为空'
                    }
                    results.append(result)
                    failed_count += 1
                    continue
                
                # 检查文件类型
                if not allowed_file(file.filename):
                    result = {
                        'filename': file.filename,
                        'status': 'failed',
                        'error': f'不支持的文件类型'
                    }
                    results.append(result)
                    failed_count += 1
                    continue
                
                original_filename = secure_filename(file.filename)
                file_ext = os.path.splitext(original_filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                
                # 保存文件
                local_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
                file.save(local_path)
                
                # 调用C++推理
                cpp_result = cpp_client.predict(
                    image_path=local_path, 
                    conf_threshold=conf_threshold, 
                    model_type=model_type,
                    auto_convert_path=True
                )
                
                if not cpp_result:
                    result = {
                        'filename': original_filename,
                        'status': 'failed',
                        'error': 'C++推理服务调用失败'
                    }
                    results.append(result)
                    failed_count += 1
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    continue
                
                # 解析结果
                detections = cpp_result.get('data', [])
                inference_time_ms = cpp_result.get('inference_time_ms', 0)
                
                # 上传原图到OSS
                oss_url = oss_client.upload_file(local_path, prefix='originals')
                
                if not oss_url:
                    result = {
                        'filename': original_filename,
                        'status': 'failed',
                        'error': 'OSS上传失败'
                    }
                    results.append(result)
                    failed_count += 1
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    continue
                
                # 绘制检测框
                result_filename = f"{uuid.uuid4().hex}_result{file_ext}"
                result_local_path = os.path.join(Config.UPLOAD_FOLDER, result_filename)
                
                draw_success = image_processor.draw_detection_boxes(
                    local_path, 
                    detections, 
                    result_local_path
                )
                
                result_oss_url = None
                if draw_success:
                    result_oss_url = oss_client.upload_file(result_local_path, prefix='results')
                    if os.path.exists(result_local_path):
                        os.remove(result_local_path)
                
                # 保存记录到数据库
                record = Record(
                    user_id=current_user.id,
                    filename=original_filename,
                    oss_url=oss_url,
                    result_oss_url=result_oss_url,
                    model_type=model_type,
                    inference_time_ms=inference_time_ms,
                    conf_threshold=conf_threshold
                )
                record.set_objects(detections)
                
                db.session.add(record)
                db.session.flush()  # 获取 record.id
                
                # 成功结果
                result = {
                    'filename': original_filename,
                    'status': 'success',
                    'record_id': record.id,
                    'oss_url': oss_url,
                    'result_oss_url': result_oss_url,
                    'inference_time_ms': inference_time_ms,
                    'defect_count': record.defect_count,
                    'objects': detections
                }
                results.append(result)
                success_count += 1
                
                # 清理本地文件
                if os.path.exists(local_path):
                    os.remove(local_path)
                
            except Exception as e:
                print(f"[批量检测异常] {original_filename if 'original_filename' in locals() else 'unknown'}: {e}")
                result = {
                    'filename': original_filename if 'original_filename' in locals() else file.filename,
                    'status': 'failed',
                    'error': f'处理异常: {str(e)}'
                }
                results.append(result)
                failed_count += 1
                
                # 清理文件
                try:
                    if local_path and os.path.exists(local_path):
                        os.remove(local_path)
                    if result_local_path and os.path.exists(result_local_path):
                        os.remove(result_local_path)
                except:
                    pass
        
        # 5. 提交数据库事务
        db.session.commit()
        
        # 6. 返回结果
        return jsonify({
            'code': 200,
            'msg': '批量检测完成',
            'data': {
                'total': len(files),
                'success': success_count,
                'failed': failed_count,
                'results': results
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[批量检测总体异常] {e}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}'
        }), 500

