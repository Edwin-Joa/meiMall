from django.urls import path
from . import views



urlpatterns = [
    path('qq/authorization/',views.QQFirstView.as_view()),
    path('oauth_callback/',views.QQUserView.as_view()),
]

