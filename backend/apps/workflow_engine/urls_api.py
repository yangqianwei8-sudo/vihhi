from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import AgentConversationViewSet, AgentMessageViewSet

router = DefaultRouter()
router.register(r'conversations', AgentConversationViewSet, basename='agent-conversation')
router.register(r'messages', AgentMessageViewSet, basename='agent-message')

urlpatterns = [
    path('', include(router.urls)),
]

