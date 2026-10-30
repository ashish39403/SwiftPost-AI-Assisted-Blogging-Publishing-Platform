from django.urls import path

from apps.anna.views import (
    AnnaConversationArchiveView,
    AnnaConversationDetailView,
    AnnaConversationListView,
    AnnaConversationMessageView,
    AnnaMessageHandoffView,
    ReviewView,
)

urlpatterns = [
    path("ai/reviews/", ReviewView.as_view(), name="ai-review"),
    path("ai/anna/conversations/", AnnaConversationListView.as_view(), name="anna-conversation-list"),
    path("ai/anna/conversations/<uuid:conversation_id>/", AnnaConversationDetailView.as_view(), name="anna-conversation-detail"),
    path("ai/anna/conversations/<uuid:conversation_id>/messages/", AnnaConversationMessageView.as_view(), name="anna-conversation-message"),
    path("ai/anna/conversations/<uuid:conversation_id>/archive/", AnnaConversationArchiveView.as_view(), name="anna-conversation-archive"),
    path("ai/anna/messages/<uuid:message_id>/continue-in-composer/", AnnaMessageHandoffView.as_view(), name="anna-message-handoff"),
]
