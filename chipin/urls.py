from django.urls import path
from . import views

urlpatterns = [
   path("", views.home, name="home"),
   path('create_group/', views.create_group, name='create_group'),
<<<<<<< HEAD
   path('group/<int:group_id>/', views.group_detail, name='group_detail'),
   path('group/<int:group_id>/invite/', views.invite_users, name='invite_users'),
   path('group/<int:group_id>/delete/', views.delete_group, name='delete_group'),
   path('accept-invite/<int:group_id>/', views.accept_invite, name='accept_invite'),
=======
   path('group//', views.group_detail, name='group_detail'),
   path('group//invite/', views.invite_users, name='invite_users'),
   path('group//delete/', views.delete_group, name='delete_group'),
>>>>>>> parent of 19785bb (Refactor Invitation Email Notification(Week 4))
]