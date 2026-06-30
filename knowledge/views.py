from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from core.models import FarmingGuide, Product, FarmerProfile


def guide_list(request):
    """农技知识库列表"""
    category = request.GET.get('category', '')
    crop = request.GET.get('crop', '')
    search = request.GET.get('search', '')

    guides = FarmingGuide.objects.filter(is_published=True).order_by('-created_at')
    if category:
        guides = guides.filter(category=category)
    if crop:
        guides = guides.filter(crop_type=crop)
    if search:
        guides = guides.filter(Q(title__icontains=search) | Q(content__icontains=search))

    # 农户专属：按产品分类推荐相关指南
    relevant_guides = None
    if request.user.is_authenticated:
        try:
            profile = request.user.farmerprofile
            farmer_cats = Product.objects.filter(farmer=profile, status='approved').values_list('category', flat=True).distinct()
            crop_map = {
                '水稻': 'rice', '小麦': 'wheat', '玉米': 'corn',
                '水果': 'fruit', '蔬菜': 'vegetable', '茶叶': 'tea',
                '中药材': 'herb', '畜禽': 'livestock', '水产': 'aquatic',
            }
            matched_crops = set()
            for cat in farmer_cats:
                crop_key = crop_map.get(cat)
                if crop_key:
                    matched_crops.add(crop_key)
            if matched_crops:
                relevant_guides = FarmingGuide.objects.filter(
                    is_published=True, crop_type__in=matched_crops
                ).order_by('-created_at')[:6]
        except FarmerProfile.DoesNotExist:
            pass

    return render(request, 'guides.html', {
        'guides': guides,
        'current_category': category,
        'current_crop': crop,
        'current_search': search,
        'relevant_guides': relevant_guides,
    })


def guide_detail(request, pk):
    """农技知识详情"""
    guide = get_object_or_404(FarmingGuide, pk=pk, is_published=True)
    related = FarmingGuide.objects.filter(
        is_published=True, category=guide.category
    ).exclude(pk=guide.pk).order_by('-created_at')[:4]
    return render(request, 'guide_detail.html', {
        'guide': guide,
        'related_guides': related,
    })
