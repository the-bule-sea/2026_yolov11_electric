import os
import shutil
import random

# --- 配置区域 ---
# 原始数据文件夹
source_dir = "raw_data"
# 划分比例 (0.8 意味着 80% 训练, 20% 验证)
train_ratio = 0.8

# 自动创建的目录结构
dirs = [
    "images/train", "images/val",
    "labels/train", "labels/val"
]

# 1. 创建文件夹
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"目录已就绪: {d}")

# 2. 获取所有图片文件
image_extensions = ['.jpg', '.JPG', '.png', '.bmp']
images = [f for f in os.listdir(source_dir) if os.path.splitext(f)[1].lower() in image_extensions]

# 打乱顺序，保证随机性
random.shuffle(images)

# 计算分割点
split_index = int(len(images) * train_ratio)
train_imgs = images[:split_index]
val_imgs = images[split_index:]

print(f"找到 {len(images)} 张图片。训练集: {len(train_imgs)}, 验证集: {len(val_imgs)}")

# 3. 定义移动函数
def move_files(image_list, split_type):
    for img_name in image_list:
        # 构造源文件路径
        src_img = os.path.join(source_dir, img_name)

        # 构造对应的 label 文件名 (把 .jpg 换成 .txt)
        base_name = os.path.splitext(img_name)[0]
        txt_name = base_name + ".txt"
        src_txt = os.path.join(source_dir, txt_name)

        # 移动图片
        dst_img = os.path.join("images", split_type, img_name)
        shutil.copy(src_img, dst_img)

        # 移动标签 (如果存在)
        if os.path.exists(src_txt):
            dst_txt = os.path.join("labels", split_type, txt_name)
            shutil.copy(src_txt, dst_txt)
        else:
            print(f"⚠️ 警告: 图片 {img_name} 没有对应的 txt 标签文件！")


# 4. 执行移动
print("正在处理训练集...")
move_files(train_imgs, "train")
print("正在处理验证集...")
move_files(val_imgs, "val")

print("✅ 数据集划分完成！请检查 images 和 labels 文件夹。")