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
from utils.exif_parser import get_exif_parser  # 新增: EXIF解析器
from utils.geocoding import get_geocoding_client  # 新增: 逆地理编码
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
        
        # 5. 解析EXIF提取GPS信息
        exif_parser = get_exif_parser()
        gps_info = exif_parser.extract_gps(local_path)
        
        # GPS信息提取结果
        longitude = None
        latitude = None
        location_name = None  # 地点名称
        
        if gps_info:
            longitude = gps_info.get('longitude')
            latitude = gps_info.get('latitude')
            print(f"[检测] GPS信息: 经度={longitude}, 纬度={latitude}")
            
            # 调用逆地理编码API获取地点名称
            try:
                geocoding_client = get_geocoding_client()
                location_name = geocoding_client.get_location_name(longitude, latitude)
                if location_name:
                    print(f"[检测] 地点名称: {location_name}")
                else:
                    print(f"[检测] 逆地理编码API未返回地点名称")
            except Exception as e:
                print(f"[检测] 逆地理编码调用失败: {e}")
                location_name = None
        else:
            print(f"[检测] 图片无GPS信息")
        
        # 6. 调用C++推理服务
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
            conf_threshold=conf_threshold,
            longitude=longitude,        # 新增: GPS经度
            latitude=latitude,          # 新增: GPS纬度
            location_name=location_name  # 新增: 地点名称
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
        exif_parser = get_exif_parser()          # 新增: EXIF解析器
        geocoding_client = get_geocoding_client()  # 新增: 逆地理编码客户端
        
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
                
                # 解析EXIF提取GPS信息
                gps_info = exif_parser.extract_gps(local_path)
                longitude = gps_info.get('longitude') if gps_info else None
                latitude = gps_info.get('latitude') if gps_info else None
                
                # 如果有GPS信息，调用逆地理编码获取地点名称
                location_name = None
                if longitude and latitude:
                    print(f"[批量检测] {original_filename} - GPS: 经度={longitude}, 纬度={latitude}")
                    try:
                        location_name = geocoding_client.get_location_name(longitude, latitude)
                        if location_name:
                            print(f"[批量检测] {original_filename} - 地点: {location_name}")
                        else:
                            print(f"[批量检测] {original_filename} - 逆地理编码未返回结果")
                    except Exception as e:
                        print(f"[批量检测] {original_filename} - 逆地理编码失败: {e}")
                        location_name = None
                else:
                    print(f"[批量检测] {original_filename} - 无GPS信息")
                
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
                    conf_threshold=conf_threshold,
                    longitude=longitude,        # 新增: GPS经度
                    latitude=latitude,          # 新增: GPS纬度
                    location_name=location_name  # 新增: 地点名称
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


@detect_bp.route('/video', methods=['POST'])
@token_required
def detect_video(current_user):
    """
    上传并检测视频
    
    POST /api/v1/detect/video
    """
    try:
        # 1. 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'msg': '文件名为空'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'code': 400, 'msg': '不支持的文件类型'}), 400
            
        # 2. 获取参数
        model_type = request.form.get('model_type', Config.DEFAULT_MODEL_TYPE)
        conf_threshold = float(request.form.get('conf_threshold', Config.DEFAULT_CONFIDENCE_THRESHOLD))
        
        # 3. 保存视频
        original_filename = secure_filename(file.filename)
        file_ext = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        local_path = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(local_path)
        
        # 4. 准备输出路径
        result_filename = f"{uuid.uuid4().hex}_result{file_ext}"
        result_local_path = os.path.join(Config.UPLOAD_FOLDER, result_filename)
        
        # 5. 调用C++进行视频推理
        cpp_client = get_cpp_client()
        print(f"[视频检测] 开始调用C++服务: {unique_filename}")
        
        # 视频处理可能很慢，这里是同步等待
        cpp_result = cpp_client.predict_video(
            video_path=local_path,
            output_path=result_local_path,
            conf_threshold=conf_threshold,
            model_type=model_type,
            auto_convert_path=True
        )
        
        if not cpp_result:
             # 清理
            if os.path.exists(local_path): os.remove(local_path)
            return jsonify({'code': 500, 'msg': 'C++视频推理失败'}), 500
            
        # 6. 上传到 OSS
        oss_client = get_oss_client()
        # 原视频上传
        oss_url = oss_client.upload_file(local_path, prefix='videos/original')
        
        # 结果视频上传
        result_oss_url = None
        if os.path.exists(result_local_path):
            result_oss_url = oss_client.upload_file(result_local_path, prefix='videos/result')
            # 上传完删除本地结果
            os.remove(result_local_path)
        
        # 删除本地原视频
        if os.path.exists(local_path):
            os.remove(local_path)
            
        if not result_oss_url:
             return jsonify({'code': 500, 'msg': '视频上传OSS失败'}), 500
             
        # 7. 解析统计结果
        processing_info = cpp_result.get('processing', {})
        total_detections = processing_info.get('total_detections', 0)
        
        # 8. 保存记录
        record = Record(
            user_id=current_user.id,
            filename=original_filename,
            oss_url=oss_url,
            result_oss_url=result_oss_url,
            model_type=model_type,
            inference_time_ms=processing_info.get('processing_time_seconds', 0) * 1000, # 存毫秒
            conf_threshold=conf_threshold,
            defect_count=total_detections
        )
        record.defect_summary = f"视频总帧数: {processing_info.get('processed_frames')}, 检出目标: {total_detections}"
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '视频检测完成',
            'data': {
                'record_id': record.id,
                'oss_url': oss_url,
                'result_oss_url': result_oss_url,
                'processing': processing_info
            }
        })
        
    except Exception as e:
        print(f"[视频检测异常] {e}")
        return jsonify({'code': 500, 'msg': f'处理异常: {str(e)}'}), 500

