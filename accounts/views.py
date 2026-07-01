from functools import wraps
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Avg
from core.models import FarmerProfile, Product, ProductBatch, Review, SubsidyApplication, FarmerPaymentMethod


# ===== 装饰器 =====

def farmer_required(view_func):
    """装饰器：检查用户是否为农户且已通过审核"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        try:
            request.farmer_profile = request.user.farmerprofile
        except FarmerProfile.DoesNotExist:
            messages.error(request, '请先注册为农户并提交入驻申请')
            return redirect('core:apply_join')
        if not request.farmer_profile.verified:
            # 检查是否已提交申请
            from core.models import JoinApplication
            app = JoinApplication.objects.filter(user=request.user, status='pending').first()
            if app:
                messages.warning(request, '您的入驻申请正在审核中，审核通过后即可使用农户功能。')
            else:
                messages.warning(request, '请先提交入驻申请，上传相关证件材料。')
            return redirect('core:apply_join')
        return view_func(request, *args, **kwargs)
    return wrapper


# ===== 认证视图 =====

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            # 根据角色跳转
            if user.is_staff:
                return redirect('admin_panel:dashboard')
            try:
                user.farmerprofile
                return redirect('products:farmer_dashboard')
            except FarmerProfile.DoesNotExist:
                return redirect('products:list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, '已成功退出登录')
    return redirect('/')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        role = request.POST.get('role', 'consumer')
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'注册成功，欢迎 {user.username}！')
            # 农户注册后需提交入驻申请，审核通过后才能使用农户功能
            if role == 'farmer':
                messages.info(request, '请先提交入驻申请，上传相关证件材料，审核通过后即可上架产品。')
                return redirect('core:apply_join')
            return redirect('products:list')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


# ===== 农户店铺 =====

def farmer_shop_view(request, farmer_id):
    """农户公开店铺页 — 增强版：含故事、照片、评价，未通过审核不对外可见"""
    profile = get_object_or_404(FarmerProfile.objects.select_related('user'), pk=farmer_id)

    # 未通过审核的农户：本人引导去申请页，其他人 404
    if not profile.verified:
        if request.user.is_authenticated and request.user == profile.user:
            from core.models import JoinApplication
            app = JoinApplication.objects.filter(user=request.user, status='pending').first()
            if app:
                messages.info(request, '您的入驻申请正在审核中，审核通过后即可开启店铺。请勿重复提交。')
            else:
                messages.warning(request, '您的入驻申请尚未通过或已被拒绝，请重新提交申请。')
            return redirect('core:apply_join')
        raise Http404('店铺不存在')
    products = Product.objects.filter(farmer=profile, status='approved').order_by('-created_at')
    batches = ProductBatch.objects.filter(
        product__farmer=profile, status='approved'
    ).select_related('product').order_by('-created_at')[:10]

    # 获取该农户的评价
    reviews = Review.objects.filter(farmer=profile).select_related('buyer', 'product').order_by('-created_at')[:20]
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    review_count = reviews.count()

    return render(request, 'farmer/shop.html', {
        'farmer': profile,
        'products': products,
        'batches': batches,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
    })


@farmer_required
def farmer_shop_settings(request):
    """编辑店铺信息 — 增加农场故事和照片"""
    profile = request.farmer_profile
    if request.method == 'POST':
        profile.shop_description = request.POST.get('shop_description', '').strip()
        profile.address = request.POST.get('address', '').strip()
        profile.phone = request.POST.get('phone', '').strip()
        profile.farm_story = request.POST.get('farm_story', '').strip()
        # 处理照片URL（可追加最多5张）
        farm_photo_urls = request.POST.getlist('farm_photo_urls')
        valid_urls = [url.strip() for url in farm_photo_urls if url.strip()]
        if valid_urls:
            existing = profile.farm_photos or []
            existing.extend(valid_urls)
            profile.farm_photos = existing[:5]  # 最多5张
        if request.FILES.get('shop_avatar'):
            profile.shop_avatar = request.FILES['shop_avatar']
        profile.save()
        messages.success(request, '店铺信息已保存')
        return redirect('accounts:farmer_shop_settings')
    return render(request, 'farmer/shop_settings.html', {'profile': profile})


# ===== 补贴申请 =====

@farmer_required
def subsidy_list(request):
    """农户补贴申请列表"""
    subsidies = SubsidyApplication.objects.filter(
        farmer=request.farmer_profile
    ).order_by('-submitted_at')
    return render(request, 'farmer/subsidy_list.html', {
        'subsidies': subsidies,
    })


@farmer_required
def subsidy_create(request):
    """农户提交补贴申请"""
    if request.method == 'POST':
        subsidy_type = request.POST.get('type', '').strip()
        amount = request.POST.get('amount', '').strip()
        documents = request.POST.getlist('document_urls')

        if not subsidy_type or not amount:
            messages.error(request, '请填写补贴类型和申请金额')
            return render(request, 'farmer/subsidy_create.html', {'prefill': request.POST})

        try:
            from decimal import Decimal
            amount_dec = Decimal(amount)
            if amount_dec <= 0:
                raise ValueError
        except Exception:
            messages.error(request, '请输入有效的申请金额')
            return render(request, 'farmer/subsidy_create.html', {'prefill': request.POST})

        valid_urls = [url.strip() for url in documents if url.strip()]
        SubsidyApplication.objects.create(
            farmer=request.farmer_profile,
            type=subsidy_type,
            amount_requested=amount_dec,
            documents=valid_urls,
        )
        messages.success(request, '补贴申请已提交，请等待审核')
        return redirect('accounts:subsidy_list')

    return render(request, 'farmer/subsidy_create.html')


# ===== 收款方式管理 =====

@farmer_required
def farmer_payment_methods(request):
    """农户管理收款方式"""
    try:
        farmer = request.user.farmerprofile
    except FarmerProfile.DoesNotExist:
        messages.error(request, '请先注册为农户')
        return redirect('core:home')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'add':
            method_type = request.POST.get('method_type', '')
            account_name = request.POST.get('account_name', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            if not account_name or not account_number:
                messages.error(request, '请填写收款人和账号')
            else:
                pm = FarmerPaymentMethod.objects.create(
                    farmer=farmer,
                    method_type=method_type,
                    account_name=account_name,
                    account_number=account_number,
                )
                if request.FILES.get('qr_code'):
                    pm.qr_code = request.FILES['qr_code']
                    pm.save(update_fields=['qr_code'])
                messages.success(request, '收款方式添加成功')
        elif action == 'toggle':
            method_id = request.POST.get('method_id')
            method = get_object_or_404(FarmerPaymentMethod, id=method_id, farmer=farmer)
            method.is_active = not method.is_active
            method.save(update_fields=['is_active'])
            messages.success(request, '状态已更新')
        elif action == 'delete':
            method_id = request.POST.get('method_id')
            method = get_object_or_404(FarmerPaymentMethod, id=method_id, farmer=farmer)
            method.delete()
            messages.success(request, '收款方式已删除')
        return redirect('accounts:farmer_payment_methods')

    methods = FarmerPaymentMethod.objects.filter(farmer=farmer).order_by('-is_active', '-created_at')
    return render(request, 'farmer/payment_methods.html', {
        'farmer': farmer,
        'payment_methods': methods,
    })
