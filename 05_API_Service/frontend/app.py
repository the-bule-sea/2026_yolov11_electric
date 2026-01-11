import gradio as gr
import cv2
import numpy as np
import requests
import pandas as pd
import json
from datetime import datetime
from PIL import Image
from io import BytesIO

# ==========================================
# 配置与常量
# ==========================================
# 后端地址 (根据 README.md 默认为 5000)
BACKEND_API_URL = "http://localhost:5000/api/v1"

# 类别映射 (用于显示中文)
CLASSES_CN = {
    "insulator_broken": "绝缘子破损",
    "insulator_burn": "绝缘子烧蚀",
    "nest": "鸟巢",
    "ring_shifted": "均压环移位",
    "unknown": "未知"
}

# ==========================================
# 后端交互逻辑
# ==========================================

def api_login(username, password):
    """调用后端登录接口"""
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json().get('data', {})
            return {
                "status": "success",
                "token": data.get('token'),
                "role": data.get('role', 'user') # 假设后端返回role，如果没有则默认为user
            }
        else:
            msg = response.json().get('msg', '登录失败')
            return {"status": "error", "message": msg}
    except Exception as e:
        return {"status": "error", "message": f"连接后端失败: {str(e)}"}

def api_detect(image, token, conf=0.25):
    """调用后端检测接口"""
    if image is None:
        return None, {"error": "未上传图片"}
    
    try:
        # 转换图像为字节流
        # Gradio image is RGB numpy array, cv2 uses BGR
        img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        success, encoded_img = cv2.imencode('.jpg', img_bgr)
        if not success:
            return None, {"error": "图片编码错误"}
        img_bytes = encoded_img.tobytes()
        
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("upload.jpg", img_bytes, "image/jpeg")}
        data = {"conf_threshold": conf}
        
        response = requests.post(
            f"{BACKEND_API_URL}/detect/image",
            headers=headers,
            files=files,
            data=data,
            timeout=30 # 推理可能需要较长时间
        )
        
        if response.status_code == 200:
            res_json = response.json()
            data = res_json.get('data', {})
            result_url = data.get('result_oss_url')
            objects = data.get('objects', [])
            
            # 翻译类别名称
            for obj in objects:
                if 'label' in obj:
                    obj['label_cn'] = CLASSES_CN.get(obj['label'], obj['label'])
            
            # 获取结果图片
            # 如果是 http URL，下载显示
            result_image = image
            if result_url:
                try:
                    img_resp = requests.get(result_url, timeout=10)
                    if img_resp.status_code == 200:
                        result_image = np.array(Image.open(BytesIO(img_resp.content)))
                except Exception as e:
                    # 获取图片失败，但返回原始图片和错误信息
                    objects.append({"warning": f"获取结果图失败: {str(e)}"})
            
            # 返回字典对象，Gradio 会自动将其转换为 JSON 显示
            return result_image, objects
            
        else:
            try:
                err_msg = response.json().get('msg', '未知错误')
            except:
                err_msg = f"HTTP {response.status_code}"
            return image, {"status": "failed", "message": err_msg}
            
    except Exception as e:
        return image, {"status": "error", "message": f"请求异常: {str(e)}"}

def api_stats(token):
    """获取仪表盘统计数据"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_API_URL}/stats/dashboard", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json().get('data', {})
            return data
        return None
    except:
        return None

# ==========================================
# 前端事件处理
# ==========================================

def login_handler(username, password):
    result = api_login(username, password)
    
    if result["status"] == "success":
        token = result["token"]
        role = result["role"]
        
        # 登录成功，如果是管理员，获取统计数据
        plot_df = pd.DataFrame(columns=["category", "count"])
        
        if role == 'admin':
            stats_data = api_stats(token)
            if stats_data:
                dist = stats_data.get('defect_distribution', {})
                # 转换分布数据为 DataFrame
                data_list = []
                for k, v in dist.items():
                    cn_name = CLASSES_CN.get(k, k)
                    data_list.append({"category": cn_name, "count": v})
                
                if data_list:
                    plot_df = pd.DataFrame(data_list)
        
        is_admin = (role == "admin")
        
        return (
            token, # 更新 state
            gr.update(visible=False), # 隐藏登录页
            gr.update(visible=True),  # 显示主界面
            f"欢迎回来, {username} (角色: {role})",
            gr.update(visible=is_admin),      # admin_content
            gr.update(visible=not is_admin),   # user_denied_content
            # 修复：必须提供 x 和 y 参数
            gr.BarPlot.update(
                value=plot_df,
                x="category",
                y="count",
                title="今日缺陷统计",
                tooltip=["category", "count"]
            ) 
        )
    else:
        return (
            "", # token置空
            gr.update(visible=True), 
            gr.update(visible=False), 
            f"登录失败: {result.get('message')}",
            gr.update(visible=False),
            gr.update(visible=True),
            gr.BarPlot.update(value=None) # 清空图表
        )

def detect_image_handler(image, token):
    if not token:
        return None, "请先登录"
    return api_detect(image, token)

def logout_handler():
    return (
        "", # token 清空
        gr.update(visible=True),  # 显示登录页
        gr.update(visible=False), # 隐藏主界面
        "已注销"
    )

# ==========================================
# UI 构建
# ==========================================

with gr.Blocks(title="电力巡检图像智能检测系统", theme=gr.themes.Soft()) as demo:
    # 全局状态
    token_state = gr.State("")
    
    gr.Markdown("# ⚡ 电力巡检图像智能检测与分析系统")
    
    # --- 登录界面 ---
    with gr.Group(visible=True) as login_view:
        gr.Markdown("### 用户登录")
        with gr.Row():
            username_input = gr.Textbox(label="用户名", value="admin", placeholder="请输入用户名")
            password_input = gr.Textbox(label="密码", value="admin123", type="password", placeholder="请输入密码")
        login_btn = gr.Button("登录", variant="primary")
        login_msg = gr.Markdown("状态: 未登录 (默认账号: admin / admin123)")

    # --- 主系统界面 ---
    with gr.Group(visible=False) as main_system_view:
        with gr.Row():
            user_info = gr.Markdown("欢迎回来")
            logout_btn = gr.Button("注销", size="sm", variant="secondary")

        with gr.Tabs():
            # Tab 1: 图像检测
            with gr.TabItem("🖼️ 单帧图像检测"):
                with gr.Row():
                    with gr.Column(scale=1):
                        img_input = gr.Image(label="上传巡检图像", type="numpy", height=400)
                        detect_btn = gr.Button("开始分析", variant="primary")
                    
                    with gr.Column(scale=1):
                        img_output = gr.Image(label="检测结果可视化", type="numpy", height=400)
                        json_output = gr.JSON(label="详细检测数据 (JSON)")
                
                # 示例 (如果没有实际图片文件，请注释掉)
                # gr.Examples(
                #     examples=[["test1.jpg"], ["test2.jpg"]],
                #     inputs=img_input
                # )

            # Tab 2: 视频流 (暂时保留占位，后端暂无直接流接口)
            with gr.TabItem("📹 实时视频流监测"):
                gr.Markdown("⚠️ 当前后端版本仅支持单帧图片检测 API，实时流功能待接入 WebSocket 服务。")
                # Gradio 3.x 兼容写法: source="webcam"
                video_input = gr.Image(label="摄像头/视频源", source="webcam", streaming=True, type="numpy")
                video_output = gr.Image(label="实时检测结果", type="numpy")

            # Tab 3: 系统管理
            with gr.TabItem("⚙️ 系统管理"):
                # 管理员视图
                with gr.Group(visible=False) as admin_content:
                    gr.Markdown("### 🔧 仪表盘数据")
                    with gr.Row():
                        # 这里简单展示一个统计图，设备列表后端暂无接口
                        stats_plot = gr.BarPlot(
                            x="category",
                            y="count",
                            title="今日缺陷统计",
                            tooltip=["category", "count"],
                            y_lim=[0, None]
                        )

                # 普通用户视图
                with gr.Group(visible=True) as user_denied_content:
                    gr.HTML(
                        """
                        <div style='text-align: center; padding: 50px;'>
                            <h2 style='color: gray;'>🚫 无权访问</h2>
                            <p>您当前的账户 (普通用户) 没有权限查看系统管理后台。</p>
                        </div>
                        """
                    )

    # --- 事件绑定 ---
    login_btn.click(
        fn=login_handler,
        inputs=[username_input, password_input],
        outputs=[token_state, login_view, main_system_view, user_info, admin_content, user_denied_content, stats_plot]
    )
    
    logout_btn.click(
        fn=logout_handler,
        inputs=None,
        outputs=[token_state, login_view, main_system_view, login_msg]
    )
    
    detect_btn.click(
        fn=detect_image_handler,
        inputs=[img_input, token_state],
        outputs=[img_output, json_output]
    )

if __name__ == "__main__":
    # Gradio 3.x 不支持 launch(theme=...)，theme 已在 Blocks() 中定义
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
