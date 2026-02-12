

from django import forms
from .models import Avaria, AvariaFoto, Veiculo, CentroDistribuicao, Produto

class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class AvariaForm(forms.ModelForm):
    class Meta:
        model = Avaria
        fields = ['cliente', 'nota_fiscal', 'produto', 'quantidade', 'motorista', 'veiculo']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'nota_fiscal': forms.TextInput(attrs={'class': 'form-control'}),
            'produto': forms.Select(attrs={'class': 'form-select select2'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'motorista': forms.Select(attrs={'class': 'form-select select2'}),
            'veiculo': forms.Select(attrs={'class': 'form-select select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter main form vehicle to show only PRINCIPAL
        if 'veiculo' in self.fields:
             self.fields['veiculo'].queryset = Veiculo.objects.filter(tipo='PRINCIPAL', ativo=True)
        # Allow multiple selection for batch creation
        self.fields['produto'] = forms.ModelMultipleChoiceField(
            queryset=Produto.objects.all(), # Should filter active?
            widget=forms.SelectMultiple(attrs={'class': 'form-select select2', 'multiple': 'multiple'}),
            help_text="Selecione um ou mais produtos para criar avarias em lote."
        )
        # Just to be safe with queryset if needed (e.g. active only)
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True)

class AvariaDecisaoForm(forms.Form):
    acao = forms.ChoiceField(choices=[('ACEITAR', 'Aceitar (Finalizar)'), ('DEVOLVER', 'Iniciar Devolução')], widget=forms.RadioSelect, label="Decisão")
    nf_retida_conferencia = forms.ChoiceField(
        choices=[('NAO', 'Não'), ('SIM', 'Sim')],
        widget=forms.RadioSelect(attrs={'class': 'btn-check-group'}), # Custom class for JS hook or styling
        label="A NF ficou retida na conferência?",
        initial='NAO'
    )
    horas_retencao = forms.IntegerField(
        required=False,
        label="Quantas horas de retenção?",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2'})
    )
    # New fields for when DEVOLVER is selected
    nf_devolucao = forms.CharField(
        required=False,
        label="NFD (Nota Fiscal de Devolução)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12345'})
    )
    cd_armazenagem_reversa = forms.ModelChoiceField(
        queryset=CentroDistribuicao.objects.filter(ativo=True),
        required=False,
        label="CD que ficará armazenado para Logística reversa",
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        empty_label="Selecione um CD..."
    )
    observacao = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label="Observação da Decisão")

class AvariaDevolucaoForm(forms.ModelForm):
    class Meta:
        model = Avaria
        fields = ['motorista_devolucao', 'veiculo_devolucao', 'veiculo_devolucao_carreta']
        widgets = {
            'motorista_devolucao': forms.Select(attrs={'class': 'form-select select2'}),
            'veiculo_devolucao': forms.Select(attrs={'class': 'form-select select2'}),
            'veiculo_devolucao_carreta': forms.Select(attrs={'class': 'form-select select2'}),
        }
        labels = {
            'motorista_devolucao': 'MOTORISTA RETORNO',
            'veiculo_devolucao': 'VEÍCULO PRINCIPAL RETORNO (OBRIGATÓRIO)',
            'veiculo_devolucao_carreta': 'CARRETA/REBOQUE RETORNO',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['veiculo_devolucao'].required = True
        
        # Filters for Return Flow
        if 'veiculo_devolucao' in self.fields:
            self.fields['veiculo_devolucao'].queryset = Veiculo.objects.filter(tipo='PRINCIPAL', ativo=True)
            
        if 'veiculo_devolucao_carreta' in self.fields:
            self.fields['veiculo_devolucao_carreta'].queryset = Veiculo.objects.filter(tipo='CARRETA', ativo=True)

    observacao_extra = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, label="OBS. SAÍDA")


class AvariaFinalizacaoDevolucaoForm(forms.Form):
    arquivo_comprovante = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}), required=True, label="Foto do Canhoto/Entrega (Obrigatório)")

class AvariaDefinicaoPrejuizoForm(forms.ModelForm):
    class Meta:
        model = Avaria
        fields = ['responsavel_prejuizo']
        widgets = {
            'responsavel_prejuizo': forms.Select(attrs={'class': 'form-select'}),
        }

class AvariaObservacaoForm(forms.Form):
    texto = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Adicionar nova observação...'}),
        label="Nova Observação"
    )

class AvariaFotoForm(forms.ModelForm):
    class Meta:
        model = AvariaFoto
        fields = ['arquivo']
    
    # Keeping this custom widget for multiple file handling if needed in list view or specific upload Logic
    # But sticking to standard ModelForm for consistency in other views if possible.
    # Reverting to use ModelForm structure as base.
    # The previous definition used forms.Form with custom widget.
    # Let's support both or just clean it up.
    
    # We will overwrite the widget to support multiple in the template logic or here:
    arquivo = forms.FileField(
        widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True, 'accept': 'image/*'}),
        label="Selecionar Fotos",
        required=False
    )

class CentroDistribuicaoForm(forms.Form):
    """Quick form to add a new CD from the avaria detail page"""
    nome = forms.CharField(
        max_length=200,
        label="Nome do CD",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CD S\u00e3o Paulo'})
    )
    codigo = forms.CharField(
        max_length=50,
        label="C\u00f3digo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: CD-SP-01'})
    )
    cidade = forms.CharField(
        max_length=100,
        required=False,
        label="Cidade",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    estado = forms.CharField(
        max_length=2,
        required=False,
        label="Estado (UF)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: SP'})
    )

class AvariaEdicaoItensForm(forms.Form):
    """Form for editing items and total value for return"""
    valor_nf = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Valor Total da NF",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'R$ 0.00'})
    )

class AvariaTransferenciaCDForm(forms.Form):
    """Form to transfer Avaria to another CD"""
    cd_armazenagem_reversa = forms.ModelChoiceField(
        queryset=CentroDistribuicao.objects.filter(ativo=True),
        required=True,
        label="Novo CD de Destino",
        widget=forms.Select(attrs={'class': 'form-select select2'}),
        empty_label="Selecione o novo CD..."
    )
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3, 
            'placeholder': 'insira dados como placa do veículo e motorista que fará a transferência'
        }),
        required=False,
        label="Observações Adicionais"
    )

