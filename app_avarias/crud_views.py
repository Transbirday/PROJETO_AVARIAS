from django.db import models
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django import forms
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import Condutor, Veiculo, Produto, Cliente, Usuario, Avaria, AvariaFoto, AvariaItem
from .mixins import GroupRequiredMixin, SuperUserRequiredMixin
from .decorators import superuser_required, group_required

# --- FORMS ---
class CondutorForm(forms.ModelForm):
    class Meta:
        model = Condutor
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control cpf-mask', 'placeholder': '000.000.000-00'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control phone-mask', 'placeholder': '(00) 00000-0000'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        existing = Condutor.objects.filter(cpf=cpf).first()
        
        if existing and existing.pk != self.instance.pk:
            if existing.ativo:
                raise forms.ValidationError("Este CPF já está cadastrado e ativo.")
            else:
                url = reverse('condutor_reactivate', args=[existing.pk])
                msg = mark_safe(f'Este CPF consta como inativo. <a href="{url}" class="alert-link">Clique aqui para reativar o cadastro de {existing.nome}</a>.')
                raise forms.ValidationError(msg)
        return cpf

class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = '__all__'
        widgets = {
            'placa': forms.TextInput(attrs={'class': 'form-control placa-input', 'placeholder': 'ABC1D23'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'propriedade': forms.Select(attrs={'class': 'form-select', 'id': 'id_propriedade'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'transportadora_nome': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_transportadora_nome'}),
            'transportadora_cnpj': forms.TextInput(attrs={'class': 'form-control cnpj-mask', 'id': 'id_transportadora_cnpj', 'placeholder': 'CNPJ da Transportadora'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        existing = Veiculo.objects.filter(placa=placa).first()
        if existing and existing.pk != self.instance.pk:
            if existing.ativo:
                raise forms.ValidationError("Veículo já cadastrado e ativo.")
            else:
                url = reverse('veiculo_reactivate', args=[existing.pk])
                msg = mark_safe(f'Veículo inativo. <a href="{url}" class="alert-link">Clique reativar {existing.placa}</a>.')
                raise forms.ValidationError(msg)
        return placa

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'laboratorio', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'laboratorio': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        # codigo_controle is auto-generated, not in form

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['cnpj', 'razao_social', 'endereco', 'nome_contato', 'telefone_contato', 'ativo']
        widgets = {
            'razao_social': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_razao_social'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control cnpj-mask', 'id': 'id_cnpj'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'id_endereco'}),
            'nome_contato': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone_contato': forms.TextInput(attrs={'class': 'form-control phone-mask'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UsuarioForm(forms.ModelForm):
    # Field specifically for setting password (only required on creation)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, label="Senha")
    
    class Meta:
        model = Usuario
        # Fields requested: Local de Atuação, Nome completo (first_name), User, Telefone, Tipo de usuário
        fields = ['local_atuacao', 'first_name', 'username', 'telefone', 'nivel_acesso', 'password', 'is_active']
        labels = {
            'first_name': 'Nome Completo',
            'username': 'Usuário (Login)',
            'is_active': 'Ativo'
        }
        widgets = {
            'local_atuacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite a Matriz ou Ponto PA'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control phone-mask'}),
            'nivel_acesso': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
            
        if commit:
            user.save()
            
            # Auto-assign Group based on Nivel Acesso
            from django.contrib.auth.models import Group
            try:
                gestor_group = Group.objects.get(name='Gestor')
                operacional_group = Group.objects.get(name='Operacional')
                
                if user.nivel_acesso == 'FULL':
                    user.groups.add(gestor_group)
                    user.groups.remove(operacional_group)
                elif user.nivel_acesso == 'MOBILE':
                    user.groups.add(operacional_group)
                    user.groups.remove(gestor_group)
            except Group.DoesNotExist:
                pass # Should not happen if migration/setup run
                
        return user

# Avaria Forms
class AvariaForm(forms.ModelForm):
    class Meta:
        model = Avaria
        fields = ['cliente', 'nota_fiscal', 'valor_nf', 'veiculo', 'veiculo_carreta', 'motorista', 'produto', 'lote', 'quantidade', 'observacoes', 'local_atuacao', 'criado_por']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'veiculo': forms.Select(attrs={'class': 'form-select select2'}),
            'veiculo_carreta': forms.Select(attrs={'class': 'form-select select2'}),
            'motorista': forms.Select(attrs={'class': 'form-select select2'}),
            'produto': forms.Select(attrs={'class': 'form-select select2'}),
            'nota_fiscal': forms.TextInput(attrs={'class': 'form-control'}),
            'valor_nf': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lote': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'local_atuacao': forms.HiddenInput(),
            'criado_por': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['veiculo'].queryset = Veiculo.objects.filter(ativo=True, tipo='PRINCIPAL')
        self.fields['veiculo_carreta'].queryset = Veiculo.objects.filter(ativo=True, tipo='CARRETA')
        
        # Make item fields optional/not-required in the Form validation 
        # (because we handle them manually as lists from request.POST)
        self.fields['produto'].required = False
        self.fields['quantidade'].required = False
        self.fields['lote'].required = False
        
        # Ensure products are loaded and active
        self.fields['produto'].queryset = Produto.objects.filter(ativo=True).order_by('nome')

class AvariaFotoForm(forms.ModelForm):
    class Meta:
        model = AvariaFoto
        fields = ['arquivo']

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        existing = Cliente.objects.filter(cnpj=cnpj).first()
        if existing and existing.pk != self.instance.pk:
            if existing.ativo:
                raise forms.ValidationError("CNPJ já cadastrado e ativo.")
            else:
                url = reverse('cliente_reactivate', args=[existing.pk])
                msg = mark_safe(f'Cliente inativo. <a href="{url}" class="alert-link">Clique reativar {existing.razao_social}</a>.')
                raise forms.ValidationError(msg)
        return cnpj

# --- MIXINS ---
# --- MIXINS ---
class SimpleListCreateView(GroupRequiredMixin, LoginRequiredMixin, ListView):
    template_name = 'app_avarias/simple_crud.html'
    form_class = None # Define in subclass
    
    def get_queryset(self):
        # Default behavior: show only active records
        qs = super().get_queryset()
        if hasattr(self.model, 'ativo'):
            return qs.filter(ativo=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page_title
        if 'form' not in context:
            context['form'] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'{self.page_title} cadastrado com sucesso!')
            return redirect(request.path)
        else:
            self.object_list = self.get_queryset()
            context = self.get_context_data(form=form)
            return self.render_to_response(context)

class BaseUpdateView(GroupRequiredMixin, LoginRequiredMixin, UpdateView):
    template_name = 'app_avarias/generic_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Editar {self.model._meta.verbose_name}"
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        messages.success(self.request, "Registro atualizado com sucesso!")
        return super().form_valid(form)

class BaseDeleteView(GroupRequiredMixin, LoginRequiredMixin, DeleteView):
    template_name = 'app_avarias/generic_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_url'] = self.success_url
        return context

    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Soft Delete strategy
        if hasattr(self.object, 'ativo'):
            self.object.ativo = False
            self.object.save()
            messages.success(self.request, "Registro excluído (desativado) com sucesso!")
        else:
            # Fallback for models without 'ativo' or real delete
            try:
                self.object.delete()
                messages.success(self.request, "Registro excluído com sucesso!")
            except Exception as e:
                messages.error(self.request, f"Erro ao excluir: {e}")
                return redirect(success_url)
                
        return redirect(success_url)

# --- VIEWS ---

# Condutor
class CondutorListView(SimpleListCreateView):
    model = Condutor
    page_title = 'Condutores'
    form_class = CondutorForm
    group_required = ["Gestor", "Operacional"]

class CondutorUpdateView(BaseUpdateView):
    model = Condutor
    form_class = CondutorForm
    success_url = reverse_lazy('condutor_list')
    group_required = ["Gestor", "Operacional"]

class CondutorDeleteView(BaseDeleteView):
    model = Condutor
    success_url = reverse_lazy('condutor_list')
    group_required = ["Gestor", "Operacional"]

# Veiculo
class VeiculoListView(SimpleListCreateView):
    model = Veiculo
    page_title = 'Veículos'
    form_class = VeiculoForm
    group_required = ["Gestor", "Operacional"]

class VeiculoUpdateView(BaseUpdateView):
    model = Veiculo
    form_class = VeiculoForm
    success_url = reverse_lazy('veiculo_list')
    group_required = ["Gestor", "Operacional"]

class VeiculoDeleteView(BaseDeleteView):
    model = Veiculo
    success_url = reverse_lazy('veiculo_list')
    group_required = ["Gestor", "Operacional"]

# Produto
class ProdutoListView(SimpleListCreateView):
    model = Produto
    page_title = 'Produtos'
    form_class = ProdutoForm
    group_required = ["Gestor", "Operacional"]

class ProdutoUpdateView(BaseUpdateView):
    model = Produto
    form_class = ProdutoForm
    success_url = reverse_lazy('produto_list')
    group_required = ["Gestor", "Operacional"]

class ProdutoDeleteView(BaseDeleteView):
    model = Produto
    success_url = reverse_lazy('produto_list')
    group_required = ["Gestor", "Operacional"]

# Cliente
class ClienteListView(SimpleListCreateView):
    model = Cliente
    page_title = 'Clientes'
    form_class = ClienteForm
    group_required = ["Gestor", "Operacional"]

class ClienteUpdateView(BaseUpdateView):
    model = Cliente
    form_class = ClienteForm
    success_url = reverse_lazy('cliente_list')
    group_required = ["Gestor", "Operacional"]

class ClienteDeleteView(BaseDeleteView):
    model = Cliente
    success_url = reverse_lazy('cliente_list')
    group_required = ["Gestor", "Operacional"]

from django.views.generic import DetailView
class ClienteDetailView(GroupRequiredMixin, LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'app_avarias/cliente_detail.html'
    group_required = ["Gestor", "Operacional"]

# Usuario
class UsuarioListView(SuperUserRequiredMixin, SimpleListCreateView):
    model = Usuario
    page_title = 'Usuários do Sistema'
    form_class = UsuarioForm
    
    def get_queryset(self):
        # Exclude superusers to focus on system users
        return Usuario.objects.filter(is_superuser=False)

class UsuarioDetailView(SuperUserRequiredMixin, LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'app_avarias/usuario_detail.html'

class UsuarioUpdateView(SuperUserRequiredMixin, BaseUpdateView):
    model = Usuario
    form_class = UsuarioForm
    success_url = reverse_lazy('usuario_list')
    
class AvariaCreateView(GroupRequiredMixin, LoginRequiredMixin, CreateView):
    model = Avaria
    form_class = AvariaForm
    template_name = 'app_avarias/avaria_form.html'
    success_url = reverse_lazy('avaria_list')
    group_required = ["Gestor", "Operacional"]

    def get_initial(self):
        initial = super().get_initial()
        # Auto-fill local from user
        initial['local_atuacao'] = self.request.user.local_atuacao
        initial['criado_por'] = self.request.user
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass active products explicitly for the dynamic rows
        context['produtos_list'] = Produto.objects.filter(ativo=True).order_by('nome')
        return context

    def form_valid(self, form):
        # Enforce user and local in backend
        form.instance.criado_por = self.request.user
        if self.request.user.local_atuacao:
            form.instance.local_atuacao = self.request.user.local_atuacao
            
        # Format Initial Observation
        obs_initial = form.cleaned_data.get('observacoes', '').strip()
        if obs_initial:
            timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
            user_str = self.request.user.username
            # Check if not already formatted (in case of re-submission or edit, though this is CreateView)
            if not obs_initial.startswith('['):
                form.instance.observacoes = f"[{timestamp} - {user_str}] [ABERTURA] {obs_initial}"

        # Save Header (Avaria)
        self.object = form.save()
        
        # Process Items (Products)
        produtos = self.request.POST.getlist('produto[]')
        quantidades = self.request.POST.getlist('quantidade[]')
        lotes = self.request.POST.getlist('lote[]')
        
        # Iterate and create items
        for i, produto_id in enumerate(produtos):
            if produto_id:
                try:
                    product = Produto.objects.get(id=produto_id)
                    qty = int(quantidades[i]) if i < len(quantidades) else 1
                    lote = lotes[i] if i < len(lotes) else ''
                    
                    AvariaItem.objects.create(
                        avaria=self.object,
                        produto=product,
                        quantidade=qty,
                        lote=lote
                    )
                except (Produto.DoesNotExist, ValueError):
                    continue
        
        # Handle Photos (Custom logic if not handled by form)
        files = self.request.FILES.getlist('fotos')
        for f in files:
            AvariaFoto.objects.create(avaria=self.object, arquivo=f, criado_por=self.request.user)

        messages.success(self.request, 'Avaria registrada com sucesso!')
        return redirect(self.success_url)
        
        # Actually, let's look at the implementation:
        # If 'produtos' is a list/queryset, we loop.
        
        # Since I cannot easily change the Form Field type in __init__ just by widget (it needs to be ModelMultipleChoiceField),
        # I will handle 'produto' manually from POST data if needed, or rely on the fact I should have updated the form field definition.
        
        # Let's assume for this specific task I'm overriding the saving logic.
        # But wait, form.save() will try to assign the list to the ForeignKey and fail.
        # So commit=False is essential, and we must check basic validation manually or ignore the 'produto' field error if we hack it.
        
        # BETTER APPROACH:
        # The form validation will fail if I send multiple values to a ModelChoiceField.
        # I should have updated the Form Field to ModelMultipleChoiceField in forms.py.
        # I did: "self.fields['produto'].widget = ..." in __init__. 
        # I should have also redundant the field definition or changed the class.
        # But let's fix it here by grabbing raw POST data if needed or trust the previous step did it right (I only saw widget change).
        
        # To be safe, I will grab the list from the form if valid, or request.POST.
        # But if the form is invalid because of this, form_valid won't be called.
        # I'll rely on the user having approved the implementation where I said I'd handle it.
        # If I missed the Field Class change in forms.py, I should fix it there. 
        # But let's write the logic here assuming `form.cleaned_data['produto']` gives me a list (if I fix the form correctly).
        
        # Wait, I only changed widget in forms.py! I need to ensure it's ModelMultipleChoiceField.
        # I can do that in __init__ too.
        
        # Moving on to the logic here:
        
        # Handle Dynamic Item Rows
        # We expect input arrays: produto[], lote[], quantidade[], observacao_item[]
        
        produtos = self.request.POST.getlist('produto[]')
        lotes = self.request.POST.getlist('lote[]')
        quantidades = self.request.POST.getlist('quantidade[]')
        
        if not produtos or len(produtos) == 0:
             # Try standard field fallback if JS failed
             if form.cleaned_data.get('produto'):
                 produtos = [form.cleaned_data.get('produto')]
                 lotes = [form.cleaned_data.get('lote')]
                 quantidades = [form.cleaned_data.get('quantidade')]
             else:
                 messages.error(self.request, "Nenhum produto selecionado.")
                 return self.form_invalid(form)

        context_data = form.cleaned_data
        
        # Prepare formatted observation (General Header Observation)
        user_obs_general = context_data.get('observacoes') or ""
        timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
        
        saved_count = 0
        
        for i, prod_id in enumerate(produtos):
            if not prod_id: continue
            
            # Get Item specific data
            if isinstance(prod_id, Produto):
                prod_obj = prod_id
            else:
                try:
                    prod_obj = Produto.objects.get(pk=prod_id)
                except Produto.DoesNotExist:
                    continue

            try:
                qty = float(quantidades[i]) if i < len(quantidades) and quantidades[i] else 1
            except ValueError:
                qty = 1
                
            lote_val = lotes[i] if i < len(lotes) else ""
            
            # Combine General Obs Only (Removed Item Obs per user request)
            full_obs = f"[{timestamp} - {self.request.user.username}] [ABERTURA] {user_obs_general}\n"

            # Create Instance
            instance = Avaria(
                 cliente=context_data['cliente'],
                 nota_fiscal=context_data['nota_fiscal'],
                 valor_nf=context_data.get('valor_nf'),
                 veiculo=context_data['veiculo'],
                 veiculo_carreta=context_data['veiculo_carreta'],
                 motorista=context_data['motorista'],
                 produto=prod_obj,
                 lote=lote_val,
                 quantidade=qty,
                 observacoes=full_obs,
                 local_atuacao=form.instance.local_atuacao,
                 criado_por=self.request.user
            )
            instance.save()
            saved_count += 1
            
            # Photos (Applied to all items)
            fotos = self.request.FILES.getlist('fotos')
            for f in fotos:
                # We need to seek(0) if reusing file? 
                # Django UploadedFile might need it if read. But creating model handles safely usually.
                # However, InMemoryUploadedFile is a stream. If read once, pointer moves.
                f.seek(0) 
                AvariaFoto.objects.create(avaria=instance, arquivo=f, criado_por=self.request.user)
        
        if saved_count > 0:
            messages.success(self.request, f"{saved_count} item(ns) de avaria registrado(s) com sucesso!")
            return redirect(self.success_url)
        else:
            messages.error(self.request, "Erro ao registrar itens.")
            return self.form_invalid(form)

class UsuarioDeleteView(SuperUserRequiredMixin, BaseDeleteView):
    model = Usuario
    success_url = reverse_lazy('usuario_list')
    
    def delete(self, request, *args, **kwargs):
        # Soft delete or deactivation strategy
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        messages.success(request, f'Usuário "{self.object.username}" desativado com sucesso!')
        return redirect(self.success_url)

@login_required
@superuser_required
def reactivate_usuario(request, pk):
    obj = get_object_or_404(Usuario, pk=pk)
    obj.is_active = True
    obj.save()
    messages.success(request, f'Usuário "{obj.username}" reativado com sucesso!')
    return redirect('usuario_list')

# --- ACTIONS ---
def reactivate_condutor(request, pk):
    obj = get_object_or_404(Condutor, pk=pk)
    obj.ativo = True
    obj.save()
    messages.success(request, f'Condutor "{obj.nome}" reativado com sucesso!')
    return redirect('condutor_list')

def reactivate_veiculo(request, pk):
    obj = get_object_or_404(Veiculo, pk=pk)
    obj.ativo = True
    obj.save()
    messages.success(request, f'Veículo "{obj.placa}" reativado com sucesso!')
    return redirect('veiculo_list')

def reactivate_produto(request, pk):
    obj = get_object_or_404(Produto, pk=pk)
    obj.ativo = True
    obj.save()
    messages.success(request, f'Produto "{obj.nome}" reativado com sucesso!')
    return redirect('produto_list')

def reactivate_cliente(request, pk):
    obj = get_object_or_404(Cliente, pk=pk)
    obj.ativo = True
    obj.save()
    messages.success(request, f'Cliente "{obj.razao_social}" reativado com sucesso!')
    return redirect('cliente_list')

from django.http import JsonResponse

def check_availability_api(request):
    """
    Generic API to check field uniqueness.
    Params: type (condutor, veiculo, produto, cliente), value (cpf, placa, sku, cnpj)
    """
    entity_type = request.GET.get('type')
    value = request.GET.get('value')
    
    if not entity_type or not value:
        return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)
    
    obj = None
    if entity_type == 'condutor':
        obj = Condutor.objects.filter(cpf=value).first()
    elif entity_type == 'veiculo':
        obj = Veiculo.objects.filter(placa=value).first()
    elif entity_type == 'produto':
        obj = Produto.objects.filter(codigo_controle=value).first()
    elif entity_type == 'cliente':
        obj = Cliente.objects.filter(cnpj=value).first()
    
    if obj:
        identifier = str(obj)
        # Try to guess a friendly name
        if hasattr(obj, 'nome'): name = obj.nome
        elif hasattr(obj, 'razao_social'): name = obj.razao_social
        elif hasattr(obj, 'placa'): name = obj.placa
        else: name = identifier

        return JsonResponse({
            'exists': True,
            'active': getattr(obj, 'ativo', True),
            'id': obj.id,
            'nome': name
        })
    
    return JsonResponse({'exists': False})
