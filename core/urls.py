from django.urls import path, include
from rest_framework import routers
from .views import (
    ProductViewSet, ProductBatchViewSet, OrderViewSet,
    SubsidyViewSet, TrainingViewSet,
    trace_view, home_view, product_list_view, product_detail_view,
    map_view, product_batches_view,
    trace_query_view, login_view, logout_view, register_view,
    dashboard_stats, dashboard_view,
    province_products, product_reviews,
    demand_analysis, market_analysis_view,
    product_filter_options,
    province_products, province_map_view,
    farmer_dashboard, farmer_product_create,
    farmer_product_edit, farmer_product_delete, farmer_product_submit,
    farmer_orders_view,
    farmer_batch_list, farmer_batch_create, farmer_batch_detail,
    farmer_shop_view, download_qr,
    farmer_set_tracking,
    export_orders_csv, export_products_csv,
    admin_dashboard, admin_products, admin_product_review, admin_users, admin_batches, admin_batch_review,
    order_create_view, consumer_orders_view,
    cart_view, cart_add, cart_remove, cart_checkout,
    favorites_view, favorite_toggle,
    farmer_shop_settings,
    notifications_view, notifications_unread_count, notifications_mark_read,
    rankings_view, cart_batch_checkout,
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
    path('api/products/<int:pk>/reviews/', product_reviews, name='product_reviews'),
    path('api/products/filter-options/', product_filter_options, name='product_filter_options'),
    path('api/', include(router.urls)),
    path('api/stats/dashboard/', dashboard_stats, name='dashboard_stats'),
    path('api/stats/province-products/', province_products, name='province_products'),
    path('api/analysis/demand/', demand_analysis, name='demand_analysis'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('map/', province_map_view, name='province_map'),
    # 消费者端
    path('order/create/', order_create_view, name='order_create'),
    path('orders/', consumer_orders_view, name='consumer_orders'),
    path('market/', market_analysis_view, name='market_analysis'),
    # 购物车
    path('cart/', cart_view, name='cart_view'),
    path('cart/add/<int:pk>/', cart_add, name='cart_add'),
    path('cart/remove/<int:pk>/', cart_remove, name='cart_remove'),
    path('cart/checkout/', cart_checkout, name='cart_checkout'),
    # 收藏
    path('favorites/', favorites_view, name='favorites'),
    path('favorite/toggle/<int:pk>/', favorite_toggle, name='favorite_toggle'),
    # 农户端
    path('farmer/', farmer_dashboard, name='farmer_dashboard'),
    path('farmer/products/create/', farmer_product_create, name='farmer_product_create'),
    path('farmer/products/<int:pk>/edit/', farmer_product_edit, name='farmer_product_edit'),
    path('farmer/products/<int:pk>/delete/', farmer_product_delete, name='farmer_product_delete'),
    path('farmer/products/<int:pk>/submit/', farmer_product_submit, name='farmer_product_submit'),
    path('farmer/orders/', farmer_orders_view, name='farmer_orders'),
    path('farmer/batches/', farmer_batch_list, name='farmer_batch_list'),
    path('farmer/batches/create/', farmer_batch_create, name='farmer_batch_create'),
    path('farmer/batches/<int:pk>/', farmer_batch_detail, name='farmer_batch_detail'),
    path('farmer/batches/<int:pk>/qr/', download_qr, name='download_qr'),
    path('farmer/orders/<int:order_id>/tracking/', farmer_set_tracking, name='farmer_set_tracking'),
    path('farmer/<int:farmer_id>/shop/', farmer_shop_view, name='farmer_shop'),
    path('farmer/shop/settings/', farmer_shop_settings, name='farmer_shop_settings'),
    # 管理端
    path('manage/', admin_dashboard, name='admin_dashboard'),
    path('manage/products/', admin_products, name='admin_products'),
    path('manage/products/<int:pk>/<str:action>/', admin_product_review, name='admin_product_review'),
    path('manage/users/', admin_users, name='admin_users'),
    path('manage/batches/', admin_batches, name='admin_batches'),
    path('manage/batches/<int:pk>/<str:action>/', admin_batch_review, name='admin_batch_review'),
    path('manage/export/orders/', export_orders_csv, name='export_orders'),
    path('manage/export/products/', export_products_csv, name='export_products'),
    # 通知
    path('notifications/', notifications_view, name='notifications'),
    path('notifications/unread-count/', notifications_unread_count, name='notifications_unread'),
    path('notifications/mark-read/<int:pk>/', notifications_mark_read, name='notifications_mark_read'),
    # 排行榜
    path('rankings/', rankings_view, name='rankings'),
    # 购物车批量下单
    path('cart/batch-checkout/', cart_batch_checkout, name='cart_batch_checkout'),
]
