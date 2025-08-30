from django.urls import path
from . import views

app_name = 'issues'

urlpatterns = [
    path('', views.user_login, name='user_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('issues/', views.issue_list, name='issue_list'),
    path('reports/', views.reports, name='reports'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/picture/', views.update_profile_picture, name='update_profile_picture'),
    path('change-password/', views.change_password, name='change_password'),
    path('my-issues/', views.my_issues, name='my_issues'),
    path('issue/new/', views.issue_create, name='issue_create'),
    path('create/', views.create_issue, name='create_issue'),
    path('issue/<int:pk>/', views.issue_detail, name='issue_detail'),
    path('issue/<int:pk>/comment/', views.post_comment, name='post_comment'),
    path('issue/<int:pk>/update/', views.issue_update_status, name='issue_update'),
    path('issue/<int:pk>/claim/', views.claim_issue, name='claim_issue'),
    path('issue/<int:pk>/resolve/', views.resolve_issue, name='resolve_issue'),
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'), 
    path('download/csv/', views.download_csv, name='download_csv'),
    path('download/pdf/', views.download_pdf, name='download_pdf'),
    path('download/<str:format_type>/', views.download_report, name='download_report'), 
]
