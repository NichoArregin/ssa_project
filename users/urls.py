from django.urls import path
from . import views

urlpatterns = [
    path("", views.user, name="user"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path('register/', views.register, name='register'),
    path('topup/', views.top_up_balance, name='topup'),
    path("group/<int:group_id>/event/<int:event_id>/transfer_funds/", views.transfer_funds, name="transfer_funds"),
]