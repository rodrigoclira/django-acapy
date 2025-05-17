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
    # Webhook endpoints
    path("topic/connections/", views.webhook_connections, name="webhook_connections"),
    path(
        "topic/issue_credential/",
        views.webhook_issue_credential,
        name="webhook_issue_credential",
    ),
    path(
        "topic/present_proof/",
        views.webhook_present_proof,
        name="webhook_present_proof",
    ),
]
