from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import PreOrderCampaign, PreOrder, FarmerProfile


def preorder_list(request):
    """预售活动列表"""
    campaigns = PreOrderCampaign.objects.filter(status='active').select_related(
        'farmer__user'
    ).order_by('-created_at')
    return render(request, 'preorder.html', {'campaigns': campaigns})


def preorder_detail(request, pk):
    """预售活动详情 + 消费者下单"""
    campaign = get_object_or_404(
        PreOrderCampaign.objects.select_related('farmer__user'), pk=pk
    )
    # 检查当前用户是否已参与
    already_ordered = False
    if request.user.is_authenticated:
        already_ordered = PreOrder.objects.filter(
            campaign=campaign, buyer=request.user
        ).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        if hasattr(request.user, 'farmerprofile'):
            messages.error(request, '农户不能参与预售')
        elif already_ordered:
            messages.error(request, '您已参与该预售活动')
        else:
            try:
                quantity = int(request.POST.get('quantity', 1))
                address = request.POST.get('address', '').strip()
            except (TypeError, ValueError):
                messages.error(request, '请输入有效数量')
                return redirect('preorder:detail', pk=pk)

            if not address:
                messages.error(request, '请填写收货地址')
            elif quantity > campaign.remaining:
                messages.error(request, '预售库存不足')
            else:
                PreOrder.objects.create(
                    campaign=campaign,
                    buyer=request.user,
                    quantity=quantity,
                    total_amount=campaign.discount_price * quantity,
                    address=address,
                )
                campaign.current_quantity += quantity
                campaign.save(update_fields=['current_quantity'])
                messages.success(request, '预订成功！')
                return redirect('preorder:detail', pk=pk)

    return render(request, 'preorder_detail.html', {
        'campaign': campaign,
        'already_ordered': already_ordered,
    })


@login_required
def preorder_create(request):
    """创建预售活动（仅农户）"""
    try:
        profile = request.user.farmerprofile
    except FarmerProfile.DoesNotExist:
        messages.error(request, '只有农户可以创建预售活动')
        return redirect('preorder:list')

    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        description = request.POST.get('description', '').strip()
        try:
            target_qty = int(request.POST.get('target_quantity', 0))
            unit_price = Decimal(request.POST.get('unit_price', '0'))
            discount_price = Decimal(request.POST.get('discount_price', '0'))
        except (TypeError, ValueError, InvalidOperation):
            messages.error(request, '请输入有效的价格和数量')
            return render(request, 'preorder_create.html')

        if not product_name or target_qty <= 0:
            messages.error(request, '请填写产品名称和有效数量')
        elif discount_price <= 0 or unit_price <= 0:
            messages.error(request, '请输入有效价格')
        elif discount_price >= unit_price:
            messages.error(request, '预售价应低于原价')
        else:
            end_date = request.POST.get('end_date')
            harvest_date = request.POST.get('harvest_date') or None
            campaign = PreOrderCampaign.objects.create(
                farmer=profile,
                product_name=product_name,
                description=description,
                target_quantity=target_qty,
                unit_price=unit_price,
                discount_price=discount_price,
                unit=request.POST.get('unit', 'kg'),
                start_date=timezone.now(),
                end_date=end_date or (timezone.now() + timezone.timedelta(days=30)),
                harvest_date=harvest_date,
            )
            messages.success(request, '预售活动已创建！')
            return redirect('preorder:detail', pk=campaign.pk)

    return render(request, 'preorder_create.html')
