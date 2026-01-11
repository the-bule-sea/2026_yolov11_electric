import gradio as gr
import cv2
import numpy as np
import time
import json
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# 配置与常量
# ==========================================
BACKEND_API_URL = "http://localhost:8000"  # 后端地址（预留）

# 模拟后端返回的检测类别（电力巡检相关）
# 0: 绝缘子破损, 1: 绝缘子烧蚀/闪络, 2: 鸟巢, 3: 均压环移位
CLASSES = ["insulator_broken", "insulator_burn", "nest", "ring_shifted"]
CLASSES_CN = {
    "insulator_broken": "绝缘子破损",
    "insulator_burn": "绝缘子烧蚀",
    "nest": "鸟巢",
    "ring_shifted": "均压环移位"
}

# ==========================================
# 模拟后端逻辑 (Mock Backend)
# 由于后端尚未就绪，这里模拟网络请求和处理延迟
# ==========================================

class MockBackend:
    def login(self, username, password):
        """模拟登录接口"""
        time.sleep(0.5)
        if username == "admin" and password == "123456":
            return {"status": "success", "token": "mock_token_admin", "role": "admin"}
        elif username == "user" and password == "123456":
            return {"status": "success", "token": "mock_token_user", "role": "user"}
        return {"status": "error", "message": "用户名或密码错误"}

    def predict_image(self, image):
        """
        模拟图像检测接口
        输入: numpy array (RGB)
        输出: 绘制了框的图像, 检测结果JSON
        """
        time.sleep(1.0) # 模拟推理耗时
        
        # 模拟生成一些随机检测框
        h, w, _ = image.shape
        detections = []
        
        # 复制图像用于绘制
        result_img = image.copy()
        
        # 随机生成 1-3 个目标
        for _ in range(np.random.randint(1, 4)):
            cls_id = np.random.randint(0, len(CLASSES))
            cls_name = CLASSES[cls_id]
            conf = np.random.uniform(0.7, 0.99)
            
            # 随机坐标
            x1 = np.random.randint(0, w // 2)
            y1 = np.random.randint(0, h // 2)
            x2 = np.random.randint(x1 + 50, w)
            y2 = np.random.randint(y1 + 50, h)
            
            # 记录数据
            detections.append({
                "class": CLASSES_CN[cls_name], # 使用中文显示
                "confidence": float(f"{conf:.2f}"),
                "bbox": [int(x1), int(y1), int(x2), int(y2)]
            })
            
            # 在图上画框 (模拟后端的OpenCV绘图)
            cv2.rectangle(result_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{CLASSES_CN[cls_name]} {conf:.2f}"
            # 简单处理：OpenCV默认不支持中文，这里为了演示临时用英文key或者需要加载中文字体
            # 为了避免乱码，图片上绘制仍然使用英文key，但在JSON和界面显示中使用中文
            # 如果需要图片上显示中文，需要使用 PIL 或者 freetype，这里简化处理保持图片上显示英文代号或拼音
            display_label = f"{cls_name} {conf:.2f}" 
            cv2.putText(result_img, display_label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
        return result_img, json.dumps({"timestamp": str(datetime.now()), "detections": detections}, indent=2)

    def process_video_frame(self, frame):
        """
        模拟视频流帧处理 (用于实时检测)
        """
        # 简单模拟：不做复杂处理，只为了演示流畅度，每隔几帧画个圈
        # 实际对接时，这里会发送帧给C++后端或调用C++动态库
        if frame is None:
            return None
        
        # 这里为了演示 FPS，不做 heavy sleep
        # 实际项目中，如果后端处理快(TensorRT)，这里FPS能很高
        
        h, w, _ = frame.shape
        cv2.putText(frame, f"System Status: Monitoring", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Backend: Mocking", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        return frame

mock_api = MockBackend()

# ==========================================
# 前端交互逻辑
# ==========================================

def login_handler(username, password):
    response = mock_api.login(username, password)
    if response["status"] == "success":
        role = response.get('role')
        # 根据角色决定是否显示"系统管理" Tab
        # 假设 Tab 3 是系统管理，我们在 Block 结构中需要用 visible update
        # 但 Gradio 的 TabItem 动态隐藏比较麻烦，通常是用 Group 包裹内容或者更新布局
        
        # 简单实现：如果是 user，显示“无权访问”提示；如果是 admin，显示真实内容
        is_admin = (role == "admin")
        
        return (
            gr.update(visible=False), # 隐藏登录页
            gr.update(visible=True),  # 显示主界面
            f"欢迎回来, {username} (角色: {role})",
            gr.update(visible=is_admin),      # admin_content
            gr.update(visible=not is_admin)   # user_denied_content
        )
    else:
        return (
            gr.update(visible=True), 
            gr.update(visible=False), 
            f"登录失败: {response.get('message')}",
            gr.update(visible=False), # 保持默认隐藏
            gr.update(visible=True)   # 保持默认显示拒绝
        )

def detect_image_handler(image):
    if image is None:
        return None, "请先上传图片"
    
    # 模拟调用后端 API
    # 实际代码应该是: 
    # response = requests.post(f"{BACKEND_API_URL}/predict", files={'file': image_bytes})
    
    result_img, json_result = mock_api.predict_image(image)
    return result_img, json_result

def video_stream_handler(video_frame):
    """
    处理实时视频流。
    Gradio 的 Image(source='webcam', streaming=True) 会不断调用此函数
    """
    return mock_api.process_video_frame(video_frame)

def logout_handler():
    return (
        gr.update(visible=True),  # 显示登录页
        gr.update(visible=False), # 隐藏主界面
        "已注销"
    )

# ==========================================
# UI 构建 (Gradio Blocks)
# ==========================================

with gr.Blocks(title="电力巡检图像智能检测系统") as demo:
    is_logged_in = gr.State(False)
    
    gr.Markdown("# ⚡ 电力巡检图像智能检测与分析系统")
    
    # --- 登录界面 ---
    with gr.Group(visible=True) as login_view:
        gr.Markdown("### 用户登录")
        with gr.Row():
            username_input = gr.Textbox(label="用户名", value="admin", placeholder="请输入用户名")
            password_input = gr.Textbox(label="密码", value="123456", type="password", placeholder="请输入密码")
        login_btn = gr.Button("登录", variant="primary")
        login_msg = gr.Markdown("状态: 未登录")

    # --- 主系统界面 (默认隐藏) ---
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
                
                # 示例图片
                gr.Examples(
                    examples=[["test1.jpg"], ["test2.jpg"]], # 假设目录下有这些文件，没有也没关系，只是占位
                    inputs=img_input
                )

            # Tab 2: 视频流/实时检测
            with gr.TabItem("📹 实时视频流监测"):
                gr.Markdown("模拟连接后端 C++ 推理引擎 (支持 30FPS+)")
                with gr.Row():
                    with gr.Column():
                        # source 参数已移除，sources=["webcam"] 指定来源
                        # streaming=True 开启流式传输
                        video_input = gr.Image(label="摄像头/视频源", sources=["webcam"], streaming=True, type="numpy")
                    with gr.Column():
                        video_output = gr.Image(label="实时检测结果", type="numpy")
                
                # 这里的逻辑是：前端摄像头 -> 每一帧 -> 后端处理 -> 返回帧 -> 前端显示
                # 注意：Gradio 的流式处理在 Web 上有一定延迟，C++ 本地展示才是真正的实时，但这里是 Web 界面。
                video_input.change(
                    fn=video_stream_handler,
                    inputs=video_input,
                    outputs=video_output
                )

            # Tab 3: 系统管理 (使用 state 控制可见性比较困难，Gradio 限制)
            # 改进策略：不尝试动态隐藏 TabItem 本身（因为 Gradio 很难做到），
            # 而是让普通用户看到一个“无权访问”的页面。
            # 或者，如果想完全“隐去入口”，需要使用 render() 动态渲染，但这会大幅增加代码复杂度。
            # 这里采用“无权访问占位符”策略，比空白页体验更好。
            with gr.TabItem("⚙️ 系统管理"):
                
                # 管理员看到的内容
                with gr.Group(visible=False) as admin_content:
                    gr.Markdown("### 🔧 设备与用户管理")
                    with gr.Row():
                        with gr.Column():
                            gr.Dataframe(
                                headers=["设备ID", "状态", "位置", "最后在线时间"],
                                value=[
                                    ["Cam-001", "Online", "Tower #34", "2026-01-09 10:00:00"],
                                    ["Cam-002", "Offline", "Tower #35", "2026-01-08 18:30:00"],
                                    ["Drone-01", "Charging", "Base Station", "2026-01-09 09:45:00"],
                                ],
                                label="接入设备列表"
                            )
                        with gr.Column():
                            plot_df = pd.DataFrame([
                                {"category": "绝缘子破损", "count": 12},
                                {"category": "绝缘子烧蚀", "count": 5},
                                {"category": "鸟巢", "count": 8},
                                {"category": "均压环移位", "count": 15}
                            ])
                            gr.BarPlot(
                                value=plot_df,
                                x="category",
                                y="count",
                                title="今日缺陷统计",
                                tooltip=["category", "count"]
                            )

                # 普通用户看到的内容 (默认显示)
                with gr.Group(visible=True) as user_denied_content:
                    gr.HTML(
                        """
                        <div style='text-align: center; padding: 50px;'>
                            <h2 style='color: gray;'>🚫 无权访问</h2>
                            <p>您当前的账户 (普通用户) 没有权限查看系统管理后台。</p>
                            <p>请联系管理员获取权限。</p>
                        </div>
                        """
                    )

    # --- 事件绑定 ---
    login_btn.click(
        fn=login_handler,
        inputs=[username_input, password_input],
        outputs=[login_view, main_system_view, user_info, admin_content, user_denied_content]
    )
    
    logout_btn.click(
        fn=logout_handler,
        inputs=None,
        outputs=[login_view, main_system_view, login_msg]
    )
    
    detect_btn.click(
        fn=detect_image_handler,
        inputs=img_input,
        outputs=[img_output, json_output]
    )

# 启动应用
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, theme=gr.themes.Soft())
