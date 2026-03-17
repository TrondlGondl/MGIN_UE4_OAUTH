"""
URL configuration for PatientPortal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from PatientPortalApp import views
from PatientPortalApp.api.views import api_patient_detail, api_medication_detail, api_medication_list,api_practitioner_detail, api_practitioner_list, api_plandefinition_detail, api_plandefinition_list, api_patient_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', views.perform_register),
    path('login/', views.perform_login),
    path('logout/', views.perform_logout),
    path('dashboard/', views.dashboard, name="dashboard"),
    path("register/practitioner/", views.perform_register_practitioner),
    path("questionaire/", views.fill_questionaire, name="fill_questionaire"),
    path("", views.home_redirect),
    path("edit/", views.edit_patient, name="edit_patient"),


    #API
    path("api/patient/", api_patient_list, name="api_patient_list"),
    path("api/patient/<int:id>/", api_patient_detail, name="api_patient_detail"),



    path("api/medication/", api_medication_list, name="api_medication_list"),
    path("api/medication/<int:id>/", api_medication_detail, name="api_medication_detail"),

    path("api/practitioner/", api_practitioner_list),
    path("api/practitioner/<int:id>/", api_practitioner_detail),

    path("api/plandefinition/", api_plandefinition_list, name="api_plandefinition_list"),
    path("api/plandefinition/<int:id>/", api_plandefinition_detail, name="api_plandefinition_detail"),

    path("accounts/", include("allauth.urls")),



    
]