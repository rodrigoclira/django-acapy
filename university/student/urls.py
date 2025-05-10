from django.urls import path

from . import views

# https://docs.djangoproject.com/en/3.2/topics/http/urls/
app_name = "student"
urlpatterns = [
    path("", views.home, name="home"),
    # path("", views.redirecionar, name="redirect"),
    path("register/", views.register, name="register"),
    path("issue-badge/", views.issue_badge, name="issue-badge"),
]
