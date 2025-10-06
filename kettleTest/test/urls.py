from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_home, name='test_home'),
    # path('create', views.test_create, name='test_create'),
    path('<int:pk>', views.test_detail, name='test_detail'), 
    path('<int:pk>/result', views.test_result, name='test_result'),
    # path('<int:pk>/update', views.TestUpdateView, name='test-update'),
]
 