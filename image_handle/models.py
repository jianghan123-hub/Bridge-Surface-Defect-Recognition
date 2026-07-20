from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class ImageCheck(models.Model):
    # 添加用户关联字段
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='关联用户',
        null=True,  # 允许null以便旧记录可以保留
        blank=True
    )

    # 原单图字段（保留但标记为可选）
    file_name = models.CharField(
        max_length=200,
        verbose_name='图片名',
        null=True,
        blank=True
    )
    file_url = models.CharField(
        max_length=250,
        verbose_name='图片URL',
        null=True,
        blank=True
    )

    # 新增双图字段
    left_file_name = models.CharField(
        max_length=200,
        verbose_name='左眼图片名',
        null=True,
        blank=True
    )
    right_file_name = models.CharField(
        max_length=200,
        verbose_name='右眼图片名',
        null=True,
        blank=True
    )
    left_file_url = models.URLField(
        verbose_name='左眼图片URL',
        max_length=250,
        null=True,
        blank=True
    )
    right_file_url = models.URLField(
        verbose_name='右眼图片URL',
        max_length=250,
        null=True,
        blank=True
    )

    # 修改结果字段为JSON格式
    check_result = models.JSONField(
        verbose_name='识别结果',
        null=True,
        blank=True,
        encoder=json.JSONEncoder  # 指定JSON编码器
    )

    check_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='检测时间'
    )

    class Meta:
        db_table = 'image_check'
        verbose_name = '图片检测'
        verbose_name_plural = verbose_name
        ordering = ['-check_time']  # 默认按检测时间倒序

    def __str__(self):
        return self.left_file_name or self.file_name or '未命名记录'

    # 实用方法：判断是否是双图检测
    def is_pair_check(self):
        return bool(self.left_file_name and self.right_file_name)

    # 实用方法：获取主要显示名称
    def get_display_name(self):
        if self.is_pair_check():
            return f"双眼检测-{self.check_time.strftime('%Y%m%d')}"
        return self.file_name