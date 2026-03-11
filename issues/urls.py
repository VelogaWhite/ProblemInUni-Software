from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('profile/', views.profile, name='profile'),
    path('report/', views.report_issue, name='report_issue'),
    path('issue/<int:issue_id>/', views.issue_detail, name='issue_detail'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Staff URLs
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/update/<int:issue_id>/', views.update_issue_status, name='update_issue_status'),
]