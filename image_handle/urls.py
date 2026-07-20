# -*- coding: utf-8 -*-
# FileName  : urls.py

from django.urls import path
from . import views

app_name = 'image_handle'

urlpatterns = [
    # 基础页面路由
    path('', views.index, name='index'),
    path('check/', views.check, name='check'),
    path('intro/', views.intro, name='intro'),
    path('treatment/', views.treatment_guide, name='treatment'),

    # 图片上传路由（兼容旧单图+新双图）
    path('upload_image/', views.upload_image, name='upload_image'),  # 旧单图上传
    #path('upload_pair/', views.upload_pair, name='upload_pair'),  # 新双图上传

    # 图片检测路由
    path('check_img/', views.check_img, name='check_img'),  # 自动适配新旧模式

    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
]