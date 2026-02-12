
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import crud_views

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboard
    # Dashboard & Welcome
    path('', views.welcome, name='welcome'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Avarias Management
    path('avarias/', views.avaria_list, name='avaria_list'),
    path('avarias/nova/', crud_views.AvariaCreateView.as_view(), name='avaria_create'), # CBV for Create
    path('avarias/pesquisa/', views.avaria_search, name='avaria_search'),
    path('avarias/<int:pk>/', views.avaria_detail, name='avaria_detail'),
    path('avarias/<int:pk>/print/', views.avaria_print, name='avaria_print'),
    path('avarias/definicao-prejuizo/', views.avaria_definicao_prejuizo_list, name='avaria_definicao_prejuizo_list'),

    # Cadastros CRUDs
    # Condutores
    path('condutores/', crud_views.CondutorListView.as_view(), name='condutor_list'),
    path('condutores/<int:pk>/editar/', crud_views.CondutorUpdateView.as_view(), name='condutor_update'),
    path('condutores/<int:pk>/excluir/', crud_views.CondutorDeleteView.as_view(), name='condutor_delete'),
    path('condutores/<int:pk>/reativar/', crud_views.reactivate_condutor, name='condutor_reactivate'),
    path('api/check-availability/', crud_views.check_availability_api, name='check_availability_api'),
    
    # Veiculos
    path('veiculos/', crud_views.VeiculoListView.as_view(), name='veiculo_list'),
    path('veiculos/<int:pk>/editar/', crud_views.VeiculoUpdateView.as_view(), name='veiculo_update'),
    path('veiculos/<int:pk>/excluir/', crud_views.VeiculoDeleteView.as_view(), name='veiculo_delete'),
    path('veiculos/<int:pk>/reativar/', crud_views.reactivate_veiculo, name='veiculo_reactivate'),

    # Produtos
    path('produtos/', crud_views.ProdutoListView.as_view(), name='produto_list'),
    path('produtos/<int:pk>/editar/', crud_views.ProdutoUpdateView.as_view(), name='produto_update'),
    path('produtos/<int:pk>/excluir/', crud_views.ProdutoDeleteView.as_view(), name='produto_delete'),
    path('produtos/<int:pk>/reativar/', crud_views.reactivate_produto, name='produto_reactivate'),

    # Clientes
    path('clientes/', crud_views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/<int:pk>/', crud_views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', crud_views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/excluir/', crud_views.ClienteDeleteView.as_view(), name='cliente_delete'),
    path('clientes/<int:pk>/reativar/', crud_views.reactivate_cliente, name='cliente_reactivate'),

    # Usuarios
    path('usuarios/', crud_views.UsuarioListView.as_view(), name='usuario_list'),
    path('usuarios/<int:pk>/', crud_views.UsuarioDetailView.as_view(), name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', crud_views.UsuarioUpdateView.as_view(), name='usuario_update'),
    path('usuarios/<int:pk>/excluir/', crud_views.UsuarioDeleteView.as_view(), name='usuario_delete'),
    path('usuarios/<int:pk>/reativar/', crud_views.reactivate_usuario, name='usuario_reactivate'),
    
    # PWA
    path('offline/', views.offline_view, name='offline'),
]
