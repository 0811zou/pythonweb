from django.urls import path, include
from rest_framework import routers
from .views import (
    ProductViewSet, ProductBatchViewSet, OrderViewSet,
    SubsidyViewSet, TrainingViewSet,
    trace_view, home_view, product_list_view, product_detail_view,
    map_view,
    product_batches_view,
    trace_query_view, login_view, logout_view, register_view,
    dashboard_stats, dashboard_view,
    province_products, product_reviews,
    demand_analysis, market_analysis_view,
    product_filter_options,
    farmer_dashboard, farmer_product_create,
    farmer_product_edit, farmer_product_delete, farmer_product_submit,
    farmer_orders_view,
    admin_dashboard, admin_products, admin_product_review, admin_users,
    order_create_view, consumer_orders_view,
)

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'batches', ProductBatchViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'subsidies', SubsidyViewSet)
router.register(r'trainings', TrainingViewSet)

urlpatterns = [
    path('', home_view, name='home'),
    path('products/', product_list_view, name='product_list'),
    path('products/<int:pk>/', product_detail_view, name='product_detail'),
    path('products/<int:pk>/batches/', product_batches_view, name='product_batches'),
    path('trace/', trace_query_view, name='trace_query'),
    path('trace/<str:batch_code>/', trace_view, name='trace'),

    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/register/', register_view, name='register'),
    path('api/products/filter-options/', product_filter_options, name='product_filter_options'),
    path('api/', include(router.urls)),
    path('api/stats/dashboard/', dashboard_stats, name='dashboard_stats'),
    path('api/stats/province-products/', province_products, name='province_products'),
    path('api/products/<int:product_id>/reviews/', product_reviews, name='product_reviews'),
    path('api/analysis/demand/', demand_analysis, name='demand_analysis'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('map/', map_view, name='map'),
    # 消费者端
    path('order/create/', order_create_view, name='order_create'),
    path('orders/', consumer_orders_view, name='consumer_orders'),
    path('market/', market_analysis_view, name='market_analysis'),
    # 农户端
    path('farmer/', farmer_dashboard, name='farmer_dashboard'),
    path('farmer/products/create/', farmer_product_create, name='farmer_product_create'),
    path('farmer/products/<int:pk>/edit/', farmer_product_edit, name='farmer_product_edit'),
    path('farmer/products/<int:pk>/delete/', farmer_product_delete, name='farmer_product_delete'),
    path('farmer/products/<int:pk>/submit/', farmer_product_submit, name='farmer_product_submit'),
    path('farmer/orders/', farmer_orders_view, name='farmer_orders'),
    # 管理端
    path('manage/', admin_dashboard, name='admin_dashboard'),
    path('manage/products/', admin_products, name='admin_products'),
    path('manage/products/<int:pk>/<str:action>/', admin_product_review, name='admin_product_review'),
    path('manage/users/', admin_users, name='admin_users'),
]
