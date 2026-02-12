
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class Usuario(AbstractUser):
    NIVEL_ACESSO_CHOICES = (
        ('MOBILE', 'App Mobile (Operacional)'),
        ('FULL', 'Web Completo (Gestor)'),
    )
    nivel_acesso = models.CharField(max_length=10, choices=NIVEL_ACESSO_CHOICES, default='MOBILE')
    local_atuacao = models.CharField(max_length=100, blank=True, null=True, help_text="Filial ou região de atuação")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")

    def __str__(self):
        return f"{self.username} ({self.get_nivel_acesso_display()})"

    @property
    def whatsapp_url(self):
        if not self.telefone:
            return None
        # Remove non-digit characters
        clean_number = ''.join(filter(str.isdigit, self.telefone))
        return f"https://wa.me/55{clean_number}"

class Cliente(models.Model):
    razao_social = models.CharField(max_length=200, verbose_name="Razão Social")
    cnpj = models.CharField(max_length=20, unique=True, verbose_name="CNPJ")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    nome_contato = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome do Contato")
    telefone_contato = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone do Contato")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.razao_social

    @property
    def whatsapp_url(self):
        if not self.telefone_contato:
            return None
        # Remove non-digit characters
        clean_number = ''.join(filter(str.isdigit, self.telefone_contato))
        return f"https://wa.me/55{clean_number}"

class Condutor(models.Model):
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Condutores"

    def __str__(self):
        return self.nome

    @property
    def whatsapp_url(self):
        if not self.telefone:
            return None
        # Remove non-digit characters
        clean_number = ''.join(filter(str.isdigit, self.telefone))
        return f"https://wa.me/55{clean_number}"

class Veiculo(models.Model):
    TIPO_CHOICES = (
        ('PRINCIPAL', 'Veículo Principal (Cavalo/Truck)'),
        ('CARRETA', 'Carreta/Reboque'),
    )
    PROPRIEDADE_CHOICES = (
        ('FROTA', 'Frota Própria'),
        ('AGREGADO', 'Agregado'),
        ('TERCEIRO', 'Terceiro'),
    )
    placa = models.CharField(max_length=8, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PRINCIPAL')
    propriedade = models.CharField(max_length=20, choices=PROPRIEDADE_CHOICES, default='FROTA')
    modelo = models.CharField(max_length=100, blank=True, null=True)
    transportadora_nome = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome Transportadora (Parceiro)")
    transportadora_cnpj = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNPJ Transportadora")
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.placa} - {self.get_tipo_display()}"

class Produto(models.Model):
    nome = models.CharField(max_length=200)
    laboratorio = models.CharField(max_length=200, verbose_name="Laboratório")
    codigo_controle = models.CharField(max_length=20, unique=True, unique_for_date='data_criacao', blank=True, verbose_name="Cód. Controle")
    ativo = models.BooleanField(default=True)
    # Keeping internal timestamps for generation logic if needed
    data_criacao = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.codigo_controle:
            # Simple auto-generation: PROD + Timestamp Hex or similar
            import time
            import random
            ts = int(time.time())
            cnt = random.randint(100, 999)
            self.codigo_controle = f"CTL-{ts}-{cnt}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.laboratorio} ({self.codigo_controle})"

class CentroDistribuicao(models.Model):
    """Centro de Distribuição para armazenagem de logística reversa"""
    nome = models.CharField(max_length=200, verbose_name="Nome do CD")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    responsavel = models.CharField(max_length=200, blank=True, null=True, verbose_name="Responsável")
    telefone = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro de Distribuição"
        verbose_name_plural = "Centros de Distribuição"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Avaria(models.Model):
    STATUS_CHOICES = (
        ('EM_ABERTO', 'Em Aberto'),
        ('DECISAO', 'Em Decisão'), # Moment of decision: Keep or Return?
            # Actually, user said:
            # 1. Em Aberto
            # 2. Decisão (Aceita -> Final; Devolução -> Aguardando Devolução)
            # So "Decisão" might be a transient state or the state while waiting for decision.
            # Let's interpret: Created -> Em Aberto. Then someone decides.
            # If Accepted -> Status FINALIZED (Finalizada - Aceite)
            # If Return -> Status AGUARDANDO_DEVOLUCAO
            # So "Decisão" is the act, or maybe a status "Under Review".
            # The user listed "2. Decisão" as a step. Let's make it a status if it holds time.
            # But the user said "Aceita pelo cliente: status final".
            # "Encaminhada para Devolucao: Vai para status Aguardando Devolucao".
            # So "Decisao" could be "Aguardando Decisão".
        ('AGUARDANDO_DEVOLUCAO', 'Aguardando Devolução'),
        ('EM_ROTA_DEVOLUCAO', 'Em Rota de Devolução'),
        ('FINALIZADA', 'Finalizada'), # Can be by Accept or Return Completed
    )
    
    TIPO_FINALIZACAO_CHOICES = (
        ('ACEITE', 'Aceita pelo Cliente'),
        ('DEVOLUCAO_CONCLUIDA', 'Devolução Concluída'),
    )

    RESPONSAVEL_PREJUIZO_CHOICES = (
        ('TRANSBIRDAY', 'Transbirday'),
        ('CLIENTE', 'Cliente'),
        ('TRANSPORTADORA_TERCEIRA', 'Transportadora Terceira'),
    )

    # Core Data
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    nota_fiscal = models.CharField(max_length=50)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, blank=True, null=True) # Deprecated (moved to items)
    quantidade = models.IntegerField(default=1, blank=True, null=True) # Deprecated
    
    # Context of Incident
    motorista = models.ForeignKey(Condutor, on_delete=models.PROTECT, blank=True, null=True)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, blank=True, null=True)
    
    # State Machine
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='EM_ABERTO')
    
    # Decisions / Actions
    acao = models.CharField(max_length=20, choices=[('ACEITAR', 'Aceitar (Finalizar)'), ('DEVOLVER', 'Iniciar Devolução')], blank=True, null=True)
    nf_retida_conferencia = models.CharField(max_length=3, choices=[('SIM', 'Sim'), ('NAO', 'Não')], default='NAO')
    horas_retencao = models.IntegerField(blank=True, null=True, verbose_name="Horas de Retenção")

    tipo_finalizacao = models.CharField(max_length=30, choices=TIPO_FINALIZACAO_CHOICES, blank=True, null=True)
    responsavel_prejuizo = models.CharField(max_length=50, choices=RESPONSAVEL_PREJUIZO_CHOICES, blank=True, null=True, verbose_name="Responsável pelo Prejuízo")
    
    # Dates for KPI
    data_criacao = models.DateTimeField(auto_now_add=True) # Start of "Em Aberto"
    data_decisao = models.DateTimeField(blank=True, null=True) # When it moved from Open to Return OR Finalized(Aceite)
    data_inicio_devolucao = models.DateTimeField(blank=True, null=True) # When it moved to "Em Rota"
    data_finalizacao = models.DateTimeField(blank=True, null=True) # End of lifecycle
    
    # Devolucao Details
    nf_devolucao = models.CharField(max_length=50, blank=True, null=True)
    motorista_devolucao = models.ForeignKey(Condutor, related_name='avarias_devolucao', on_delete=models.SET_NULL, blank=True, null=True)
    veiculo_devolucao = models.ForeignKey(Veiculo, related_name='avarias_devolucao', on_delete=models.SET_NULL, blank=True, null=True)
    veiculo_devolucao_carreta = models.ForeignKey(Veiculo, related_name='avarias_devolucao_carreta', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Carreta Devolução")
    cd_armazenagem_reversa = models.ForeignKey('CentroDistribuicao', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="CD de Armazenagem (Logística Reversa)")

    criado_por = models.ForeignKey(Usuario, related_name='avarias_criadas', on_delete=models.PROTECT)
    local_atuacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Local de Atuação")
    
    # New Fields requested
    lote = models.CharField(max_length=50, blank=True, null=True) # Deprecated
    valor_nf = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Valor da NF")
    veiculo_carreta = models.ForeignKey(Veiculo, related_name='avarias_carreta', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Carreta (Opcional)")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    @property
    def dias_em_aberto(self):
        end_date = self.data_decisao if self.data_decisao else timezone.now()
        if self.data_criacao:
            return (end_date - self.data_criacao).days
        return 0

    @property
    def dias_aguardando_devolucao(self):
        if self.status in ['AGUARDANDO_DEVOLUCAO', 'EM_ROTA_DEVOLUCAO', 'FINALIZADA'] and self.data_decisao:
             # If it moved to next stage, use that date, else use now
             end_date = self.data_inicio_devolucao if self.data_inicio_devolucao else timezone.now()
             # If finalized without going through devolucao (e.g. Aceite), this metric might not apply, but here we assume path
             return (end_date - self.data_decisao).days
        return 0

    @property
    def dias_em_rota(self):
        if self.status in ['EM_ROTA_DEVOLUCAO', 'FINALIZADA'] and self.data_inicio_devolucao:
            end_date = self.data_finalizacao if self.data_finalizacao else timezone.now()
            return (end_date - self.data_inicio_devolucao).days
        return 0

    def __str__(self):
        return f"Avaria {self.id} - {self.cliente}"

class AvariaItem(models.Model):
    avaria = models.ForeignKey(Avaria, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade = models.IntegerField(default=1)
    lote = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.produto.nome} (Qtd: {self.quantidade})"

class AvariaFoto(models.Model):
    avaria = models.ForeignKey(Avaria, related_name='fotos', on_delete=models.CASCADE)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='fotos_enviadas', on_delete=models.SET_NULL, null=True, blank=True)
    arquivo = models.ImageField(upload_to='avarias_fotos/%Y/%m/%d/')
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto {self.id} - Avaria {self.avaria.id}"
