from django.urls import path

from apps.composer.views import (
    ComposerConversationArchiveView,
    ComposerConversationDetailView,
    ComposerConversationListView,
    ComposerConversationMessageView,
    ComposeDetailView,
    ComposeView,
)

urlpatterns = [
    path("ai/compose/", ComposeView.as_view(), name="ai-compose"),
    path("ai/compose/<uuid:run_id>/", ComposeDetailView.as_view(), name="ai-compose-detail"),
    path("ai/composer/conversations/", ComposerConversationListView.as_view(), name="composer-conversation-list"),
    path("ai/composer/conversations/<uuid:conversation_id>/", ComposerConversationDetailView.as_view(), name="composer-conversation-detail"),
    path("ai/composer/conversations/<uuid:conversation_id>/messages/", ComposerConversationMessageView.as_view(), name="composer-conversation-message"),
    path("ai/composer/conversations/<uuid:conversation_id>/archive/", ComposerConversationArchiveView.as_view(), name="composer-conversation-archive"),
]
