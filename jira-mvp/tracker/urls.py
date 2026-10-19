from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/login/', views.LoginView.as_view()),
    path('users/', views.UserListView.as_view()),
    path('projects/', views.ProjectListCreateView.as_view()),
    path('projects/<str:key>/', views.ProjectDetailView.as_view()),
    path('projects/<str:key>/members/', views.MemberView.as_view()),
    path('projects/<str:key>/issues/', views.IssueListCreateView.as_view()),
    path('projects/<str:key>/issues/<int:number>/', views.IssueDetailView.as_view()),
    path('projects/<str:key>/issues/<int:number>/comments/', views.CommentListCreateView.as_view()),
    path('projects/<str:key>/issues/<int:number>/activity/', views.ActivityListView.as_view()),
]
