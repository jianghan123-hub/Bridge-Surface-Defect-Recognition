# -*- coding: utf-8 -*-
# FileName  : conf.py
import os
from pathlib import Path

# 本文件位置
my_path = Path(__file__).resolve()

# 项目根目录（方便搜索训练输出等）
# 注意：当前仓库在子目录下，实际数据/输出路径在上层目录，因此这里取 parents[3]
PROJECT_ROOT = my_path.parents[3]

# 传统分类模型文件位置（旧模型，保留兼容）
model_path = os.path.join(my_path.parent, 'train_model', '玉米病虫害识别最优模型.pth')


def _find_yolo_best_model() -> Path:
    """搜索 YOLOv8 best.pt 模型文件路径。

    训练输出路径可能不同（例如 notebook 训练会产生 runs/detect/...），
    所以这里会尝试常见路径，并自动搜索最近的 best.pt。
    """
    candidates = [
        PROJECT_ROOT / 'runs' / 'detect' / 'bridge_damage_output' / 'runs' / 'bridge_damage_det' / 'weights' / 'best.pt',
        PROJECT_ROOT / 'runs' / 'bridge_damage_det' / 'weights' / 'best.pt',
        PROJECT_ROOT / 'runs' / 'detect' / 'bridge_damage_output' / 'weights' / 'best.pt',
        PROJECT_ROOT / 'runs' / 'detect' / 'bridge_damage_det' / 'weights' / 'best.pt',
        PROJECT_ROOT / 'runs' / 'detect' / 'bridge_damage_output' / 'runs' / 'bridge_damage_det2' / 'weights' / 'best.pt',
    ]

    for p in candidates:
        if p.exists():
            return p

    # 如果上述路径都不存在，尝试搜索最近的 best.pt
    best_files = list(PROJECT_ROOT.glob('**/best.pt'))
    if best_files:
        # 按修改时间选择最近的一个
        best_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return best_files[0]

    # 如果还找不到，则返回一个可能的默认位置
    return PROJECT_ROOT / 'runs' / 'bridge_damage_det' / 'weights' / 'best.pt'


def get_yolo_model_path() -> str:
    """返回可用的 YOLOv8 best.pt 路径字符串。"""
    return str(_find_yolo_best_model())
