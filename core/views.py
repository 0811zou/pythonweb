from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
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
