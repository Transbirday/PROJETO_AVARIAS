

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cliente, Condutor, Veiculo, Produto, Avaria, AvariaFoto, CentroDistribuicao


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('nivel_acesso', 'local_atuacao')}),
    )
    list_display = ('username', 'email', 'nivel_acesso', 'local_atuacao', 'is_staff')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'ativo')
    search_fields = ('razao_social', 'cnpj')

@admin.register(Condutor)
class CondutorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'ativo')
    search_fields = ('nome', 'cpf')

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'tipo', 'propriedade', 'modelo')
    list_filter = ('tipo', 'propriedade')
    search_fields = ('placa',)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'laboratorio', 'codigo_controle', 'ativo')
    search_fields = ('nome', 'laboratorio', 'codigo_controle')

class AvariaFotoInline(admin.TabularInline):
    model = AvariaFoto
    extra = 1

@admin.register(Avaria)
class AvariaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'status', 'data_criacao', 'dias_em_aberto', 'criado_por')
    list_filter = ('status', 'data_criacao', 'cliente')
    inlines = [AvariaFotoInline]
    date_hierarchy = 'data_criacao'

@admin.register(CentroDistribuicao)
class CentroDistribuicaoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'cidade', 'estado', 'ativo')
    search_fields = ('codigo', 'nome', 'cidade')
    list_filter = ('ativo', 'estado')

