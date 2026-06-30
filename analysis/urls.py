from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('market/', views.market_analysis_view, name='market_analysis'),
    path('api/analysis/demand/', views.demand_analysis, name='demand_analysis'),
    path('ai-assistant/', views.ai_assistant_view, name='ai_assistant'),
    path('api/ai/chat/', views.ai_chat_api, name='ai_chat_api'),
]
