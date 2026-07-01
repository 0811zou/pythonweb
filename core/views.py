from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Announcement, Training, SubsidyApplication
from .serializers import TrainingSerializer
from .permissions import IsAdminOrReadOnly, IsSubsidyOwnerOrAdmin, get_farmer_profile
from accounts.serializers import SubsidyApplicationSerializer


from marketplace.models import SupplyDemandPost
from knowledge.models import FarmingGuide


# ── Home ──

def home_view(request):
    announcements = Announcement.objects.filter(is_active=True)[:5]
    marketplace_posts = SupplyDemandPost.objects.filter(status='active').order_by('-created_at')[:4]
    guides = FarmingGuide.objects.filter(is_published=True).order_by('-created_at')[:4]
    return render(request, 'index.html', {
        'announcements': announcements,
        'marketplace_posts': marketplace_posts,
        'guides': guides,
    })


def map_view(request):
    """中国地图 — 各省产品分布"""
    return render(request, 'map.html')


def seasonal_products_page(request):
    """时令推荐页面"""
    return render(request, 'seasonal.html')


def training_list(request):
    """培训课程列表"""
    trainings = Training.objects.all().order_by('-created_at')
    return render(request, 'training_list.html', {'trainings': trainings})


def training_detail(request, pk):
    """培训课程详情"""
    training = get_object_or_404(Training, pk=pk)
    return render(request, 'training_detail.html', {'training': training})


# ── DRF ViewSets (models still in core) ──

class SubsidyViewSet(viewsets.ModelViewSet):
    queryset = SubsidyApplication.objects.all()
    serializer_class = SubsidyApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().order_by('-submitted_at')
        if self.request.user.is_staff:
            return qs
        farmer = get_farmer_profile(self.request.user)
        if farmer:
            return qs.filter(farmer=farmer)
        return SubsidyApplication.objects.none()

    def get_permissions(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsSubsidyOwnerOrAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        farmer = get_farmer_profile(self.request.user)
        if not farmer:
            raise PermissionDenied('只有农户可以申请补贴')
        serializer.save(farmer=farmer)


class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [IsAdminOrReadOnly]


# ===== 平台入驻申请 =====

@login_required
def apply_join(request):
    """农户/合作社入驻申请页面（需上传证件材料）"""
    from django.shortcuts import redirect
    from django.contrib import messages
    from .models import JoinApplication
    from accounts.models import FarmerProfile

    # 检查是否已有申请记录
    existing = JoinApplication.objects.filter(
        user=request.user,
    ).order_by('-created_at').first()

    # 有 pending 申请 → 展示状态页（不直接跳首页）
    if existing and existing.status == 'pending':
        return render(request, 'apply_status.html', {
            'application': existing,
            'status_type': 'pending',
        })

    # 已通过 → 提示并跳转工作台
    if existing and existing.status == 'approved':
        messages.info(request, '您的入驻申请已通过审核，欢迎使用农户功能。')
        return redirect('products:farmer_dashboard')

    if request.method == 'POST':
        apply_type = request.POST.get('apply_type', 'farmer')
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        region = request.POST.get('region', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not phone or not region:
            messages.error(request, '请填写姓名/名称、联系电话和所在地区')
            return render(request, 'apply_join.html', {'prefill': request.POST})

        app = JoinApplication.objects.create(
            user=request.user, apply_type=apply_type,
            name=name, phone=phone, region=region, description=description,
        )
        # 处理文件上传
        if request.FILES.get('id_document'):
            app.id_document = request.FILES['id_document']
        if request.FILES.get('license_document'):
            app.license_document = request.FILES['license_document']
        if request.FILES.get('farm_photo1'):
            app.farm_photos = [request.FILES['farm_photo1'].name]
        app.save()

        # 确保农户资料存在（但未验证）
        if not hasattr(request.user, 'farmerprofile'):
            FarmerProfile.objects.create(user=request.user, phone=phone, address=region, verified=False)

        messages.success(request, '申请已提交！我们会尽快审核，审核结果会通过站内通知发送。')
        return redirect('core:home')

    # 预填：从现有 FarmerProfile 或最近被拒申请中获取
    prefill = {}
    try:
        fp = request.user.farmerprofile
        prefill = {'name': request.user.username, 'phone': fp.phone or '', 'region': fp.address or ''}
    except FarmerProfile.DoesNotExist:
        prefill = {'name': request.user.username, 'phone': '', 'region': ''}

    # 如有被拒绝的申请，传入拒绝原因供表单展示
    rejected_app = None
    if existing and existing.status == 'rejected':
        rejected_app = existing
        if not prefill.get('phone'):
            prefill['phone'] = existing.phone
        if not prefill.get('region'):
            prefill['region'] = existing.region

    return render(request, 'apply_join.html', {
        'prefill': prefill,
        'rejected_app': rejected_app,
    })
