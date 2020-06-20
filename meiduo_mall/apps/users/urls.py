from django.urls import path
from . import views


urlpatterns = [
    path('usernames/<username:username>/count/',views.UsernameCountView.as_view()),
]


