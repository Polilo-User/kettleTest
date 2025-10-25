from django.urls import path
from . import views

urlpatterns = [
    path('', views.test_home, name='test_home'),
    # path('create', views.test_create, name='test_create'),
    path('<int:pk>', views.test_detail, name='test_detail'), 
    path('<int:pk>/result/<int:atId>', views.test_result, name='test_result'),
    path('my_results', views.results_list, name='results_list'),
    path("send_result/email/", views.send_result_email, name="send_result_email"),
    path("send_result/telegram/", views.send_result_telegram, name="send_result_telegram"),

    # path('<int:pk>/update', views.TestUpdateView, name='test-update'),
]
 