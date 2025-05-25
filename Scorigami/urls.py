"""
URL configuration for Scorigami project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path
from games import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('view_scores/<int:higher_score>/<int:lower_score>/', views.view_scores, name='view_scores'),
    path('home/', views.home, name='Home'),
    path('', RedirectView.as_view(url='/home/')),
    path('grid/', views.grid, name='Grid'),
    path('score_lookup/', views.research_scores, name='Score Researcher')
]