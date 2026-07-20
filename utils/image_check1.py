# -*- coding: utf-8 -*-
"""
文件名：image_check.py
功能：桥梁表观病害智能检测（支持 YOLOv8 目标检测）
输入：桥梁表面图像路径
输出：病害检测结果（类别+置信度+定位信息）
"""

import os
import torch
from PIL import Image

from utils.conf import model_path, get_yolo_model_path

# YOLOv8 依赖（可选）
try:
    from ultralytics import YOLO
    _HAS_YOLO = True
except ImportError:
    _HAS_YOLO = False


class Config:
    # 旧分类模型标签（保留兼容）
    label_columns = ['Cercospora_leaf_spot', 'Common_rust', 'Northern_Leaf_Blight', 'healthy']
    label_columns_cn = ['尾孢菌叶斑病', '普通锈病', '大斑病', '健康叶片']
    img_size = 224

    # 桥梁病害类别映射（YOLO模型中 class_name -> 中文）
    # 若数据集类别不同，请根据实际类别名称调整
    label_map_cn = {
        'Crack': '裂缝',
        'Breakage': '剥落/破损',
        'Comb': '蜂窝状破损',
        'Hole': '孔洞',
        'Reinforcement': '钢筋暴露/锈蚀',
        'Seepage': '渗漏',
        'crack': '裂缝',
        'corrosion': '锈蚀',
        'spalling': '剥落',
        'other': '其他'
    }


# 旧分类模型（EfficientNetV2）
clas_model = None


def load_classification_model(model_path):
    import torch
    from torchvision import models
    from torch import nn

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = models.efficientnet_v2_s(weights=None)
    num_ftrs = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(num_ftrs, len(Config.label_columns))
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint)
    model = model.to(device)
    model.eval()
    return model


def get_transforms():
    from torchvision import transforms
    return transforms.Compose([
        transforms.Resize((Config.img_size, Config.img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])


def classification_detect(image_path):
    global clas_model
    if clas_model is None:
        if not os.path.exists(model_path):
            raise ValueError(f"模型文件不存在: {model_path}")
        clas_model = load_classification_model(model_path)

    try:
        img = Image.open(image_path).convert('RGB')
        transform = get_transforms()
        img_tensor = transform(img).unsqueeze(0)
        device = next(clas_model.parameters()).device
        with torch.no_grad():
            outputs = clas_model(img_tensor.to(device))
            probs = torch.softmax(outputs, dim=1).cpu().numpy()[0]
            pred_idx = int(probs.argmax())
        return {
            'model_used': 'classification',
            'model_path': model_path,
            'probabilities': {name: float(prob) for name, prob in zip(Config.label_columns_cn, probs)},
            'prediction': Config.label_columns_cn[pred_idx],
            'probabilities_en': {name: float(prob) for name, prob in zip(Config.label_columns, probs)},
            'prediction_en': Config.label_columns[pred_idx]
        }
    except Exception as e:
        raise ValueError(f"图像处理失败: {str(e)}")


# YOLOv8 模型
yolo_model = None


def load_yolo_model(model_path):
    """加载 YOLOv8 模型（仅在 ultralytics 可用时）。"""
    global yolo_model

    if not _HAS_YOLO:
        raise ImportError('未安装 ultralytics，请通过 pip install ultralytics 安装后重试')

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"YOLOv8 模型文件不存在: {model_path}")

    if yolo_model is None:
        yolo_model = YOLO(str(model_path))

    return yolo_model


def yolo_detect(image_path, conf_threshold=0.25, iou_threshold=0.45, max_det=100):
    """使用 YOLOv8 进行目标检测，并返回预测结果。"""
    model_path = get_yolo_model_path()
    model = load_yolo_model(model_path)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    results = model.predict(
        source=str(image_path),
        imgsz=640,
        conf=conf_threshold,
        iou=iou_threshold,
        device=device,
        max_det=max_det,
        verbose=False
    )

    if len(results) == 0:
        return {
            'prediction': '未检测到病害',
            'probabilities': {},
            'prediction_en': 'none',
            'probabilities_en': {},
            'detections': []
        }

    res = results[0]
    names = getattr(model, 'names', {}) or {}

    # 初始化每个类别的最大置信度
    probs = {names.get(i, str(i)): 0.0 for i in range(len(names))}

    detections = []
    try:
        boxes = getattr(res, 'boxes', None)
        if boxes is not None:
            for box in boxes:
                cls_idx = int(box.cls.cpu().numpy()[0]) if hasattr(box, 'cls') else int(box.cls)
                conf = float(box.conf.cpu().numpy()[0]) if hasattr(box, 'conf') else float(box.conf)
                xyxy = box.xyxy.cpu().numpy()[0].tolist() if hasattr(box, 'xyxy') else []
                cls_name = names.get(cls_idx, str(cls_idx))
                probs[cls_name] = max(probs.get(cls_name, 0.0), conf)
                detections.append({
                    'class': cls_name,
                    'confidence': conf,
                    'bbox': xyxy
                })
    except Exception:
        # 如果无法使用 boxes API，则忽略
        pass

    best_pred = max(detections, key=lambda x: x['confidence']) if detections else None
    if best_pred:
        prediction = best_pred['class']
    else:
        prediction = '未检测到病害'

    probabilities_cn = {Config.label_map_cn.get(k, k): v for k, v in probs.items()}

    return {
        'model_used': 'yolov8',
        'model_path': model_path,
        'prediction': Config.label_map_cn.get(prediction, prediction),
        'probabilities': probabilities_cn,
        'prediction_en': prediction,
        'probabilities_en': probs,
        'detections': detections
    }


def check_handle(image_path):
    """对外调用接口，优先使用 YOLOv8 检测；若不可用则回退到旧分类模型。"""
    model_path = get_yolo_model_path()
    if _HAS_YOLO and os.path.exists(model_path):
        try:
            return yolo_detect(image_path)
        except Exception as e:
            print(f"YOLO检测失败（{model_path}），回退到分类模型：{e}")
    # 无法使用 YOLO 时回退到旧分类模型
    return classification_detect(image_path)
