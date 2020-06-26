from django.urls import path
from . import views

urlpatterns = [
    path('areas/',views.ProvinceAreaView.as_view()),
    path('areas/<area:pk>/',views.SubAreaView.as_view()),
    path('addresses/create/',views.CreateAddressView.as_view()),
    path('addresses/',views.GetAddressView.as_view()),
    path('addresses/<int:address_id>/', views.UpdateDestroyAddressView.as_view()),
    path('addresses/<int:address_id>/title/', views.UpdateTitleAddressView.as_view()),
    path('addresses/<int:address_id>/default/', views.UpdateDestroyAddressView.as_view()),
    path('password/',views.ChangePasswordView.as_view()),
    path('password/',views.ChangePasswordView.as_view()),
]