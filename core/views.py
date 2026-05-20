from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Sum
from .models import Product, ProductBatch, Order, SubsidyApplication, Training
from .serializers import ProductSerializer, ProductBatchSerializer, OrderSerializer, SubsidyApplicationSerializer, TrainingSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('farmer').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class ProductBatchViewSet(viewsets.ModelViewSet):
    queryset = ProductBatch.objects.select_related('product').all()
    serializer_class = ProductBatchSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def upload_payment(self, request, pk=None):
        order = self.get_object()
        proof = request.data.get('payment_proof')
        if not proof:
            return Response({'detail':'请上传付款凭证'}, status=status.HTTP_400_BAD_REQUEST)
        order.payment_proof = proof
        order.status = 'paid_offline'
        order.save()
        return Response({'detail':'已上传，等待后台确认'})

class SubsidyViewSet(viewsets.ModelViewSet):
    queryset = SubsidyApplication.objects.all()
    serializer_class = SubsidyApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer

# 溯源页面
def trace_view(request, batch_code):
    batch = get_object_or_404(ProductBatch, batch_code=batch_code)
    return render(request, 'trace.html', {'batch': batch})

# ===== 前端页面 =====
def home_view(request):
    return render(request, 'index.html')

def product_list_view(request):
    return render(request, 'products.html')

def product_detail_view(request, pk):
    product = get_object_or_404(Product.objects.select_related('farmer__user', 'farmer__cooperative'), pk=pk)
    return render(request, 'product_detail.html', {'product': product})

def trace_query_view(request):
    """溯源查询页面 - 手动输入批次号"""
    batch = None
    code = request.GET.get('code', '')
    if code:
        try:
            batch = ProductBatch.objects.select_related('product').get(batch_code=code)
            return redirect('trace', batch_code=code)
        except ProductBatch.DoesNotExist:
            messages.error(request, f'未找到批次编号：{code}')
    return render(request, 'trace_query.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
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
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'注册成功，欢迎 {user.username}！')
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})
