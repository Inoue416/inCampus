from django.urls import path
from . import views

app_name='incampusApp'

urlpatterns = [
    path('incampus_admin/', views.incampusAdminView.as_view(), name='incampus_admin'),
    path('admin_home/', views.adminHomeView.as_view(), name='admin_home'),
    path('admin_auto_register/', views.adminAutoRegisterView.as_view(), name='admin_auto_register'),
    path('admin_manual_register/', views.adminManualRegisterView.as_view(), name='admin_manual_register'),
    path('admin_edit_infomation/', views.adminEditInfomationView.as_view(), name='admin_edit_infomation'),
    path('<str:kind>/<str:user_id>/admin_edit_each_infomation/', views.adminEditEachInfomationView.as_view(), name='admin_edit_each_infomation'),
    path('<int:kind>/login/', views.LoginView.as_view(), name='login'),
    path('', views.HomeView.as_view(), name='home'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('<int:r_id>/student_data_detail/', views.StudentDateDetailView.as_view(), name='student_date_detail'),
    path('<str:u_id>/each_student_data/', views.EachStudetnDataView.as_view(), name='each_student_data'),
    path('laboratory_infomation/', views.LaboratoryInfomationView.as_view(), name='laboratory_infomation')
    #path('set_admin/', views.setAdminView.as_view(), name='set_admin')
]
