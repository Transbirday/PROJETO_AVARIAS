
from rest_framework import serializers
from app_avarias.models import Usuario, Cliente, Condutor, Veiculo, Produto, Avaria, AvariaFoto, AvariaItem

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'nivel_acesso', 'local_atuacao']

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class CondutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condutor
        fields = '__all__'

class VeiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = '__all__'

class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = '__all__'

class AvariaItemSerializer(serializers.ModelSerializer):
    produto_nome = serializers.ReadOnlyField(source='produto.nome')
    
    class Meta:
        model = AvariaItem
        fields = ['id', 'produto', 'produto_nome', 'quantidade', 'lote']

class AvariaFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvariaFoto
        fields = ['id', 'avaria', 'arquivo', 'data_upload']
        read_only_fields = ['data_upload']

class AvariaSerializer(serializers.ModelSerializer):
    # Nested representation for reading
    cliente_nome = serializers.ReadOnlyField(source='cliente.razao_social')
    status_display = serializers.SerializerMethodField()
    
    # Nested serializers
    itens = AvariaItemSerializer(many=True)
    fotos = AvariaFotoSerializer(many=True, read_only=True)

    class Meta:
        model = Avaria
        fields = [
            'id', 'cliente', 'cliente_nome', 'nota_fiscal', 
            'itens',
            'motorista', 'veiculo', 'status', 'status_display', 'data_criacao', 
            'motorista_devolucao', 'veiculo_devolucao', 'nf_devolucao',
            'fotos', 'observacoes'
        ]
        read_only_fields = ['status', 'data_criacao', 'data_decisao', 'data_inicio_devolucao', 'data_finalizacao', 'criado_por']

    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def create(self, validated_data):
        items_data = validated_data.pop('itens')
        
        # Auto-assign User from context
        user = self.context['request'].user
        validated_data['criado_por'] = user
        
        avaria = Avaria.objects.create(**validated_data)
        
        for item_data in items_data:
            AvariaItem.objects.create(avaria=avaria, **item_data)
            
        return avaria
