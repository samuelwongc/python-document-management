from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework_jwt.views import (obtain_jwt_token, refresh_jwt_token)

from . import views


router = DefaultRouter()
router.register(r'document', views.DocumentViewSet, base_name='document')
router.register(r'lenderdocument', views.LenderDocumentViewSet, base_name='lenderdocument')

urlpatterns = [
    url(r'^test/$', views.test),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-refresh/', refresh_jwt_token),
    url(r'^', include(router.urls))
]
