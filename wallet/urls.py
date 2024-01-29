from . import views
from django.urls import path, re_path

urlpatterns = [
    
    path('login/',views.login, name='login'),
    path('movimientos/<type>/',views.movimientos,name='movimientos'), #type puede ser 'Ingresos' o 'Gastos'
    path('newMovimiento/<type>/',views.newMovimiento, name='newMovimiento'),
    path('modifyMovimiento/<type>/<int:id>/', views.modifyMovimiento, name='modifyMovimiento'),
    path('recordatorios/',views.recordatorios, name='recordatorios'),
    path('home/', views.home ,name= 'home'),
    path('register/',views.register, name='register'),
    path('logout/',views.logout, name='logout'),
    path('changePassword/',views.changePassword,name='changePassword'),
    path('userPage/',views.userPage,name='userPage'),
    path('changePassword/',views.changePassword,name='changePassword'),
    path('deleteAccount/',views.deleteAccount,name='deleteAccount'),
    path('balance/',views.balance,name='balance'),
    path('recordatorios/',views.recordatorios, name='recordatorios'),
    path('eliminarMovimiento/<type>/<int:id>/<int:all>/<int:mother>/',views.eliminarMovimiento,name="eliminarMovimiento"),
    path('eliminarRecordatorio/<int:id>/',views.eliminarRecordatorio,name="eliminarRecordatorio"),
    path('forgotPassword/', views.forgotPassword, name='forgotPasword'),
    path('calendario/', views.calendario, name='calendario'),
    path('generarReporte/', views.reporte, name='generarReporte'),
    re_path(r'^.*$', views.custom_page_not_found),
    
]

