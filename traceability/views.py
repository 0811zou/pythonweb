from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from products.models import ProductBatch


# 溯源页面
def trace_view(request, batch_code):
    batch = get_object_or_404(
        ProductBatch.objects.select_related('product__farmer__user').prefetch_related('events'),
        batch_code=batch_code,
    )
    batch.ensure_qr_code()
    return render(request, 'trace.html', {'batch': batch, 'events': batch.events.all()})


def trace_query_view(request):
    """溯源查询页面 - 手动输入批次号"""
    batch = None
    code = request.GET.get('code', '')
    if code:
        try:
            batch = ProductBatch.objects.select_related('product').get(batch_code=code)
            return redirect('traceability:trace', batch_code=code)
        except ProductBatch.DoesNotExist:
            messages.error(request, f'未找到批次编号：{code}')
    return render(request, 'trace_query.html')
