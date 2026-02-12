
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from app_avarias.models import Usuario, Cliente, Condutor, Veiculo, Produto, Avaria, AvariaFoto
from .serializers import (
    UsuarioSerializer, ClienteSerializer, CondutorSerializer, VeiculoSerializer, 
    ProdutoSerializer, AvariaSerializer, AvariaFotoSerializer
)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.filter(ativo=True)
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

class CondutorViewSet(viewsets.ModelViewSet):
    queryset = Condutor.objects.filter(ativo=True)
    serializer_class = CondutorSerializer
    permission_classes = [permissions.IsAuthenticated]

class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.all()
    serializer_class = VeiculoSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProdutoViewSet(viewsets.ModelViewSet):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    permission_classes = [permissions.IsAuthenticated]

class AvariaViewSet(viewsets.ModelViewSet):
    """
    Main ViewSet for Mobile App interaction.
    Allows listing, creating, and adding photos/notes.
    """
    queryset = Avaria.objects.all().order_by('-data_criacao')
    serializer_class = AvariaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Mobile users might only see Open ones in a real scenario, but let's return all for now
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=True, methods=['post'])
    def upload_foto(self, request, pk=None):
        avaria = self.get_object()
        serializer = AvariaFotoSerializer(data=request.data)
        if serializer.is_valid():
            # 'enviado_por' removed from model
            serializer.save(avaria=avaria)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_observacao(self, request, pk=None):
        avaria = self.get_object()
        texto = request.data.get('texto')
        
        if texto:
             from django.utils import timezone
             timestamp = timezone.now().strftime("%d/%m/%Y %H:%M")
             new_entry = f"[{timestamp} - {request.user.username}] {texto}\n"
             
             if avaria.observacoes:
                 avaria.observacoes += "\n" + new_entry
             else:
                 avaria.observacoes = new_entry
             
             avaria.save()
             return Response({'status': 'Observação adicionada', 'observacoes': avaria.observacoes}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Campo "texto" obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
