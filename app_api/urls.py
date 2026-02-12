
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clientes', views.ClienteViewSet)
router.register(r'condutores', views.CondutorViewSet)
router.register(r'veiculos', views.VeiculoViewSet)
router.register(r'produtos', views.ProdutoViewSet)
router.register(r'avarias', views.AvariaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
