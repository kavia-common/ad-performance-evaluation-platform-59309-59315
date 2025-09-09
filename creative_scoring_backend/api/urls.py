from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='Health'),
    path('upload/', views.upload, name='upload'),
    path('creatives/', views.list_creatives, name='list_creatives'),
    path('audience/', views.audience, name='audience'),
    path('score/', views.score, name='score'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('comparative_test/', views.comparative_test, name='comparative_test'),
    path('export/', views.export, name='export'),
    path('admin/weightings', views.admin_weightings, name='admin_weightings'),
]
