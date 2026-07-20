# -*- coding: utf-8 -*-
"""
本脚本用于训练 YOLOv8 桥梁表观病害检测模型。

使用方法（从项目根目录运行）:
    python image_handle/train_yolov8.py --data data/bridge_damage.yaml --epochs 20

说明:
- 需要提前准备好用于训练的 YAML 数据配置文件（包含 train/val 路径和类别信息）。
- 可通过 `--weights` 指定预训练模型（如 yolov8s.pt）。
- 训练完成后，最佳模型会保存在 runs/train/<name>/weights/best.pt。
"""

import argparse
from pathlib import Path
import os

try:
    from ultralytics import YOLO
except ImportError as e:
    raise ImportError('请先安装 ultralytics (pip install ultralytics) 后再运行训练脚本') from e


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = BASE_DIR / 'runs'
# 如果本地有 yolov8s.pt 可指定，否则使用 ultralytics 自动下载的模型
DEFAULT_WEIGHTS = 'yolov8s.pt'


def train_yolov8(
    data_yaml: Path,
    weights: str = DEFAULT_WEIGHTS,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    name: str = 'bridge_damage_det',
    epochs: int = 20,
    imgsz: int = 640,
    batch: int = 4,
    device: str = '0',
    workers: int = 0,
    conf: float = 0.25,
    iou: float = 0.45,
    mosaic: float = 0.5,
    mixup: float = 0.0,
):
    """启动 YOLOv8 训练流程。"""
    # 设置 Ultralytics 缓存目录
    os.environ.setdefault('ULTRALYTICS_CACHE_DIR', str(BASE_DIR / 'UltralyticsCache'))

    # 确保训练输出目录存在
    (output_root / name).mkdir(parents=True, exist_ok=True)

    weights_str = str(weights)
    print(f"使用权重: {weights_str}")

    model = YOLO(weights_str)
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        workers=workers,
        device=device,
        half=True,
        project=str(output_root),
        name=name,
        pretrained=True,
        optimizer='auto',
        mosaic=mosaic,
        mixup=mixup,
        save=True,
        conf=conf,
        iou=iou,
    )

    best_path = output_root / name / 'weights' / 'best.pt'
    print(f"训练完成，最佳模型已保存到: {best_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description='训练YOLOv8桥梁病害检测模型')
    parser.add_argument('--data', type=Path, required=True, help='训练数据的 YAML 配置文件路径')
    parser.add_argument('--weights', type=str, default=DEFAULT_WEIGHTS, help='预训练权重路径（默认为 yolov8s.pt，可为本地文件或模型名称）')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT_ROOT, help='训练输出目录')
    parser.add_argument('--name', type=str, default='bridge_damage_det', help='训练任务名称')
    parser.add_argument('--epochs', type=int, default=20, help='训练轮数')
    parser.add_argument('--imgsz', type=int, default=640, help='输入图像大小')
    parser.add_argument('--batch', type=int, default=4, help='批量大小')
    parser.add_argument('--device', type=str, default='0', help='训练设备 (0 或 cpu)')
    parser.add_argument('--conf', type=float, default=0.25, help='置信度阈值')
    parser.add_argument('--iou', type=float, default=0.45, help='IOU 阈值')
    args = parser.parse_args()

    print('开始训练：')
    print(f'  数据配置: {args.data}')
    print(f'  预训练权重: {args.weights}')
    print(f'  输出目录: {args.output / args.name}')

    train_yolov8(
        data_yaml=args.data,
        weights=args.weights,
        output_root=args.output,
        name=args.name,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        conf=args.conf,
        iou=args.iou,
    )


if __name__ == '__main__':
    main()
