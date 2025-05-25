from django.urls import path

from . import views

# https://docs.djangoproject.com/en/3.2/topics/http/urls/
app_name = "student"
urlpatterns = [
    path("", views.home, name="home"),
    # path("", views.redirecionar, name="redirect"),
    path("register/", views.register, name="register"),
    #
    path("credential/", views.issue_credential, name="issue-badge"),
    #
    path(
        "presentation_request/", views.presentation_request, name="presentation-request"
    ),
    path(
        "topic/<str:topic>/",
        views.handle_topic,
        name="handle-topic",
    ),
    # Webhook endpoints
    #     path("topic/connections/", views.webhook_connections, name="webhook_connections"),
    #     path(
    #         "topic/issue_credential_v2_0/",
    #         views.webhook_issue_credential,
    #         name="webhook_issue_credential",
    #     ),
    #     path(
    #         "topic/present_proof_v2_0/",
    #         views.webhook_present_proof,
    #         name="webhook_present_proof",
    #     ),
    #     path(
    #         "topic/endorse_transaction/",
    #         views.webhook_endorse_transaction,
    #         name="webhook_endorse_transaction",
    #     ),
    #     path("topic/ping/", views.webhook_ping, name="webhook_ping"),
    #
]
