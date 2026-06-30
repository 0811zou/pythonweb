from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Custom API endpoints (BEFORE router to avoid pk matching) ──
    path('', include('products.urls')),       # api/products/seasonal/, api/stats/, etc.
    path('', include('analysis.urls')),        # api/analysis/demand/

    # ── DRF router ──
    path('api/', include('core.api_urls')),

    # ── Page routes ──
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('', include('traceability.urls')),
    path('', include('trade.urls')),
    path('', include('marketplace.urls')),
    path('', include('knowledge.urls')),
    path('', include('preorder.urls')),
    path('', include('notifications.urls')),
    path('', include('admin_panel.urls')),

    # ── API docs ──
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
