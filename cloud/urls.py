from django.contrib import admin
from django.urls import path

from . import views

app_name = 'cloud'
urlpatterns = [
    path('list', views.api_file_list, name="list"),
    path('delete', views.file_delete, name="delete"),
    path('status', views.file_status, name="status"),
    path('<str:uniqid>', views.download_file, name="download"),
    path('', views.index, name="index"),
    # path('advertise/<int:category_id>/', views.advertise, name="advertise"),
    # path('category/', views.category, name="category"),
    # path('search/', views.Search, name="search"),
    # path('advDetail/<int:adv_id>/', views.advDetail, name="advDetail"),
    # path('advedit/<int:adv_id>/', views.advEdit, name="advedit"),
    # path('advdelete/<int:adv_id>/', views.advDelete, name="advdelete"),
    # path('categoriesLost/<int:category_id>/', views.LostThingincatogries, name="categoriesLost"),
]
