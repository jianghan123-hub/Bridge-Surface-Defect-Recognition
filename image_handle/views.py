import os
import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from web_system.settings import admin_title, index_info
from .models import ImageCheck
from utils.image_check import check_handle
import time


def index(request):
    context = {
        'title': admin_title,
        'index_info': index_info
    }
    return render(request, 'index.html', context=context)


def intro(request):
    return render(request, 'intro.html', {'title': '系统简介'})


def treatment_guide(request):
    return render(request, 'treatment.html')


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            return redirect('image_handle:check')
        else:
            messages.error(request, '用户名或密码错误，请重试')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {
        'login_form': form,
        'register_form': UserCreationForm()
    })


def user_register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'注册成功！欢迎 {user.username}，您已自动登录')
            return redirect('image_handle:check')
        else:
            # 收集所有错误信息
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, '注册失败: ' + '; '.join(error_messages))
    else:
        form = UserCreationForm()

    return render(request, 'login.html', {
        'register_form': form,
        'login_form': AuthenticationForm()
    })


def user_logout(request):
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('image_handle:login')


@login_required
def check(request):
    # 添加用户相关信息到上下文
    context = {
        'username': request.user.username,
        'is_staff': request.user.is_staff
    }
    return render(request, 'check.html', context=context)


@csrf_exempt
def upload_image(request):
    """上传单张桥梁表面图片"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST方法'}, status=405)

    # 验证用户是否登录
    if not request.user.is_authenticated:
        return JsonResponse({'code': 403, 'message': '请先登录系统'}, status=403)

    try:
        img_file = request.FILES['img_file']
    except KeyError as e:
        return JsonResponse({'code': 400, 'message': f'缺少必要参数: {str(e)}'}, status=400)

    # 生成规范化文件名（添加用户ID前缀）
    timestamp = int(time.time())
    user_prefix = f"user_{request.user.id}_"
    img_name = f"{user_prefix}{timestamp}.{img_file.name.split('.')[-1].lower()}"

    # 保存文件
    try:
        save_path = os.path.join(settings.MEDIA_ROOT, img_name)
        with open(save_path, 'wb+') as f:
            for chunk in img_file.chunks():
                f.write(chunk)
    except IOError as e:
        return JsonResponse({'code': 500, 'message': f'文件保存失败: {str(e)}'}, status=500)

    # 创建数据库记录（关联当前用户）
    try:
        record = ImageCheck.objects.create(
            user=request.user,
            left_file_name=img_name,
            left_file_url=request.build_absolute_uri(f"{settings.MEDIA_URL}{img_name}"),
            check_result=None
        )
    except Exception as e:
        return JsonResponse({'code': 500, 'message': f'数据库操作失败: {str(e)}'}, status=500)

    return JsonResponse({
        'code': 200,
        'data': {
            'img_url': record.left_file_url,
            'record_id': record.id
        }
    })

@csrf_exempt
def check_img(request):
    """检测桥梁表面病害图片（单张）"""
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '仅支持POST方法'}, status=405)

    # 验证用户是否登录
    if not request.user.is_authenticated:
        return JsonResponse({'code': 403, 'message': '请先登录系统'}, status=403)

    try:
        data = json.loads(request.body)
        img_url = data['img_url']
    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'code': 400, 'message': '参数格式错误'}, status=400)

    # 提取文件名
    img_name = os.path.basename(img_url.split('/')[-1])
    img_path = os.path.join(settings.MEDIA_ROOT, img_name)

    # 验证文件是否存在
    if not os.path.exists(img_path):
        return JsonResponse({'code': 404, 'message': '图像文件不存在'}, status=404)

    try:
        result = check_handle(img_path)

        # 更新数据库记录
        record, created = ImageCheck.objects.update_or_create(
            left_file_name=img_name,
            defaults={
                'user': request.user,
                'left_file_url': img_url,
                'check_result': result
            }
        )

        resp = {
            'code': 200,
            'data': {
                'prediction': result.get('prediction'),
                'probabilities': result.get('probabilities'),
                'prediction_en': result.get('prediction_en'),
                'probabilities_en': result.get('probabilities_en'),
                'detections': result.get('detections', [])
            }
        }
        # 可选的调试信息
        if 'model_used' in result:
            resp['data']['model_used'] = result['model_used']
        if 'model_path' in result:
            resp['data']['model_path'] = result['model_path']
        return JsonResponse(resp)
    except Exception as e:
        return JsonResponse({
            'code': 500,
            'message': f'检测失败: {str(e)}',
            'traceback': str(e) if settings.DEBUG else None
        }, status=500)