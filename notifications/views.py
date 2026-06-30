from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from core.models import Notification


@login_required
def notifications_view(request):
    """通知列表 — 支持分页 + 类型筛选"""
    type_filter = request.GET.get('type', '')
    notifs = Notification.objects.filter(recipient=request.user)

    if type_filter and type_filter in ('order', 'batch', 'product', 'system'):
        notifs = notifs.filter(notification_type=type_filter)

    # 标记全部已读
    if request.GET.get('mark_read') == 'all':
        notifs.filter(is_read=False).update(is_read=True)
        return redirect('notifications:list')

    # 清除全部已读通知
    if request.GET.get('clear_read') == 'all':
        notifs.filter(is_read=True).delete()
        return redirect('notifications:list')

    # 分页
    paginator = Paginator(notifs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications.html', {
        'notifications': page_obj,
        'type_filter': type_filter,
    })


@login_required
def notifications_unread_count(request):
    """未读通知数（JSON API）"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notifications_mark_read(request, pk):
    """标记单条已读"""
    Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))


@login_required
def notifications_delete(request, pk):
    """删除单条通知"""
    Notification.objects.filter(pk=pk, recipient=request.user).delete()
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))
