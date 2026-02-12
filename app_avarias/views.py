from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DurationField, Avg, Min, Max
from .models import Avaria, AvariaFoto, Produto
from .forms import (
    AvariaForm, AvariaDecisaoForm, AvariaDevolucaoForm, AvariaObservacaoForm, 
    AvariaFotoForm, AvariaFinalizacaoDevolucaoForm, AvariaDefinicaoPrejuizoForm,
    CentroDistribuicaoForm, AvariaEdicaoItensForm, AvariaTransferenciaCDForm
)
from .decorators import group_required

from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
import json
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def welcome(request):
    return render(request, 'app_avarias/welcome.html')

@login_required
@group_required("Gestor")
def dashboard(request):
    """
    Dashboard Home View with Advanced KPIs, Financials, Charts and SLAs
    """
    qs_all = Avaria.objects.all()

    # --- FILTER LOGIC ---
    now = timezone.now()
    month_filter = request.GET.get('month')
    year_filter = request.GET.get('year')

    try:
        current_month = int(month_filter) if month_filter else now.month
        current_year = int(year_filter) if year_filter else now.year
    except ValueError:
        current_month = now.month
        current_year = now.year

    qs_created = qs_all.filter(data_criacao__year=current_year, data_criacao__month=current_month)
    qs_finalized_in_period = qs_all.filter(status='FINALIZADA', data_finalizacao__year=current_year, data_finalizacao__month=current_month)

    # GLOBAL COUNTERS (Unfiltered)
    qs_open = qs_all.filter(status='EM_ABERTO')
    qs_waiting = qs_all.filter(status='AGUARDANDO_DEVOLUCAO')
    qs_finalized = qs_all.filter(status='FINALIZADA')
    
    count_open = qs_open.count()
    count_ready_return = qs_waiting.count()
    
    count_monthly_returns = qs_all.filter(
        tipo_finalizacao='DEVOLUCAO_CONCLUIDA',
        data_finalizacao__month=current_month,
        data_finalizacao__year=current_year
    ).count()
    
    # Financials (Sum of valor_nf)
    from decimal import Decimal

    val_open = qs_open.aggregate(total=Sum('valor_nf'))['total'] or 0
    if isinstance(val_open, (int, float, Decimal)):
        val_open = Decimal(str(val_open)).quantize(Decimal('0.01'))
    
    val_returned = qs_finalized.filter(tipo_finalizacao='DEVOLUCAO_CONCLUIDA').aggregate(total=Sum('valor_nf'))['total'] or 0
    if isinstance(val_returned, (int, float, Decimal)):
        val_returned = Decimal(str(val_returned)).quantize(Decimal('0.01'))
    
    val_accepted = qs_finalized.filter(tipo_finalizacao='ACEITE').aggregate(total=Sum('valor_nf'))['total'] or 0
    if isinstance(val_accepted, (int, float, Decimal)):
        val_accepted = Decimal(str(val_accepted)).quantize(Decimal('0.01'))
    
    total_finished_decided = qs_finalized.filter(tipo_finalizacao__in=['ACEITE', 'DEVOLUCAO_CONCLUIDA']).count()
    count_accepted = qs_finalized.filter(tipo_finalizacao='ACEITE').count()
    
    acceptance_rate = 0
    if total_finished_decided > 0:
        acceptance_rate = (count_accepted / total_finished_decided) * 100

    # 2. CHARTS DATA
    
    # A. Monthly Evolution (Created vs Finalized)
    evolution_data = (
        qs_all
        .annotate(month=TruncMonth('data_criacao'))
        .values('month')
        .annotate(total_created=Count('id'))
        .order_by('month')
    )
    evolution_data = list(evolution_data)
    for d in evolution_data:
        if d['month']:
            d['month'] = d['month'].strftime('%Y-%m-%d')
    
    # Evolution: Returns (By Finalization Date)
    evolution_returns = (
        qs_finalized
        .filter(tipo_finalizacao='DEVOLUCAO_CONCLUIDA')
        .annotate(month=TruncMonth('data_finalizacao'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    evolution_returns = list(evolution_returns)
    for d in evolution_returns:
        if d['month']:
            d['month'] = d['month'].strftime('%Y-%m-%d')

    # Evolution: Accepted (By Finalization Date)
    evolution_accepted = (
        qs_finalized
        .filter(tipo_finalizacao='ACEITE')
        .annotate(month=TruncMonth('data_finalizacao'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )
    evolution_accepted = list(evolution_accepted)
    for d in evolution_accepted:
        if d['month']:
            d['month'] = d['month'].strftime('%Y-%m-%d')

    # B. Client Acceptance vs Rejection (Global)
    client_stats = (
        qs_finalized
        .values('cliente__razao_social')
        .annotate(
            accepted=Count('id', filter=Q(tipo_finalizacao='ACEITE')),
            returned=Count('id', filter=Q(tipo_finalizacao='DEVOLUCAO_CONCLUIDA'))
        )
        .order_by('-accepted')[:10]
    )
    
    # D. Heatmap (Global)
    raw_locations = list(qs_all
        .exclude(local_atuacao__isnull=True)
        .values('local_atuacao')
        .annotate(total=Count('id')))
        
    # Map to BR states
    import re
    state_counts = {}
    valid_states = [
        'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms', 'mg', 
        'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc', 'sp', 'se', 'to'
    ]
    
    for item in raw_locations:
        loc_str = (item['local_atuacao'] or "").lower()
        cnt = item['total']
        match = re.search(r'\b(' + '|'.join(valid_states) + r')\b', loc_str)
        if match:
            state_code = match.group(1)
            key = f"br-{state_code}"
            state_counts[key] = state_counts.get(key, 0) + cnt
    
    heatmap_data = [[k, v] for k, v in state_counts.items()]
    heatmap_list = []
    
    STATE_MAP = {
        'ac': 'Acre', 'al': 'Alagoas', 'ap': 'Amapá', 'am': 'Amazonas', 'ba': 'Bahia',
        'ce': 'Ceará', 'df': 'Distrito Federal', 'es': 'Espírito Santo', 'go': 'Goiás',
        'ma': 'Maranhão', 'mt': 'Mato Grosso', 'ms': 'Mato Grosso do Sul', 'mg': 'Minas Gerais',
        'pa': 'Pará', 'pb': 'Paraíba', 'pr': 'Paraná', 'pe': 'Pernambuco', 'pi': 'Piauí',
        'rj': 'Rio de Janeiro', 'rn': 'Rio Grande do Norte', 'rs': 'Rio Grande do Sul',
        'ro': 'Rondônia', 'rr': 'Roraima', 'sc': 'Santa Catarina', 'sp': 'São Paulo',
        'se': 'Sergipe', 'to': 'Tocantins'
    }

    for k, v in state_counts.items():
        state_code = k.replace('br-', '')
        state_name = STATE_MAP.get(state_code, state_code.upper())
        heatmap_list.append({'state': state_name, 'count': v})
    
    heatmap_list.sort(key=lambda x: x['count'], reverse=True)

    # 3. TOP OFENDERS
    top_drivers = (
        qs_all
        .values('motorista__nome', 'motorista__cpf')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    
    top_products_total = (
        qs_all
        .values('produto__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    
    top_products_returned = (
        qs_finalized
        .filter(tipo_finalizacao='DEVOLUCAO_CONCLUIDA')
        .values('produto__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    
    top_products_accepted = (
        qs_finalized
        .filter(tipo_finalizacao='ACEITE')
        .values('produto__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    # 4. SLAs
    def calc_sla(queryset, start_field, end_field):
        qs = queryset.filter(**{f"{start_field}__isnull": False, f"{end_field}__isnull": False})
        if not qs.exists():
            return {'min_time': None, 'avg_time': None, 'max_time': None}
        stats = qs.aggregate(
            min_time=Min(ExpressionWrapper(F(end_field) - F(start_field), output_field=DurationField())),
            avg_time=Avg(ExpressionWrapper(F(end_field) - F(start_field), output_field=DurationField())),
            max_time=Max(ExpressionWrapper(F(end_field) - F(start_field), output_field=DurationField()))
        )
        return stats

    def format_duration(value):
        if not value: return "-"
        days = value.days
        seconds = value.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{days} Dias e {hours:02}:{minutes:02} Horas"

    def format_sla_dict(stats):
        return {
            'min_time': format_duration(stats['min_time']),
            'avg_time': format_duration(stats['avg_time']),
            'max_time': format_duration(stats['max_time'])
        }

    sla_decision = format_sla_dict(calc_sla(qs_all, 'data_criacao', 'data_decisao'))
    sla_waiting_return = format_sla_dict(calc_sla(qs_all, 'data_decisao', 'data_inicio_devolucao'))
    sla_transport = format_sla_dict(calc_sla(qs_finalized.filter(tipo_finalizacao='DEVOLUCAO_CONCLUIDA'), 'data_inicio_devolucao', 'data_finalizacao'))
    
    # -------------------------------------------------------------
    # NEW LISTS: Monthly (12 months) and Annual (5 years) Financials
    # -------------------------------------------------------------
    # Helper to get financial breakdown
    def get_financial_history(trunc_func, limit):
         history = (qs_finalized
            .annotate(period=trunc_func('data_finalizacao'))
            .values('period')
            .annotate(
                val_devolvido=Sum('valor_nf', filter=Q(tipo_finalizacao='DEVOLUCAO_CONCLUIDA')),
                val_aceitas=Sum('valor_nf', filter=Q(tipo_finalizacao='ACEITE')),
                val_prejuizo=Sum('valor_nf', filter=Q(responsavel_prejuizo='TRANSBIRDAY'))
            )
            .order_by('-period')[:limit]
         )
         return list(history)
         
    history_monthly = get_financial_history(TruncMonth, 12)
    history_yearly = get_financial_history(ExtractYear, 5)

    # C. Financial Breakdown Lists (Monthly & Yearly)
    
    # 1. Last 12 Months
    from datetime import timedelta
    last_12_months = now - timedelta(days=365)
    financial_12m = (
        qs_finalized
        .filter(data_finalizacao__gte=last_12_months)
        .annotate(month=TruncMonth('data_finalizacao'))
        .values('month')
        .annotate(
            total_cliente=Sum('valor_nf', filter=Q(responsavel_prejuizo='CLIENTE')),
            total_transbirday=Sum('valor_nf', filter=Q(responsavel_prejuizo='TRANSBIRDAY')),
            total_terceiro=Sum('valor_nf', filter=Q(responsavel_prejuizo='TRANSPORTADORA_TERCEIRA')),
        )
        .order_by('-month')
    )
    
    # 2. Last 5 Years
    last_5_years = now - timedelta(days=365*5)
    financial_5y = (
        qs_finalized
        .filter(data_finalizacao__gte=last_5_years)
        .annotate(year=ExtractYear('data_finalizacao'))
        .values('year')
        .annotate(
            total_cliente=Sum('valor_nf', filter=Q(responsavel_prejuizo='CLIENTE')),
            total_transbirday=Sum('valor_nf', filter=Q(responsavel_prejuizo='TRANSBIRDAY')),
            total_terceiro=Sum('valor_nf', filter=Q(responsavel_prejuizo='TRANSPORTADORA_TERCEIRA')),
        )
        .order_by('-year')
    )

    context = {
        'count_open': count_open,
        'count_ready_return': count_ready_return,
        'count_monthly_returns': count_monthly_returns,
        'val_open': val_open,
        'val_returned': val_returned,
        'val_accepted': val_accepted,
        'acceptance_rate': round(acceptance_rate, 1),
        
        'evolution_data': json.dumps(evolution_data, cls=DjangoJSONEncoder), 
        'evolution_returns': json.dumps(evolution_returns, cls=DjangoJSONEncoder),
        'evolution_accepted': json.dumps(evolution_accepted, cls=DjangoJSONEncoder),
        'client_stats': list(client_stats),
        'heatmap_data': json.dumps(heatmap_data, cls=DjangoJSONEncoder),
        'heatmap_list': heatmap_list,
        
        'top_drivers': top_drivers,
        'top_products_total': top_products_total,
        'top_products_returned': top_products_returned,
        'top_products_accepted': top_products_accepted,
        
        'sla_decision': sla_decision,
        'sla_waiting_return': sla_waiting_return,
        'sla_transport': sla_transport,
        
        'history_monthly': history_monthly,
        'history_yearly': history_yearly,
        
        # New Financial Lists
        'financial_12m': financial_12m,
        'financial_5y': financial_5y,

        'month_options': [{'value': m, 'selected': m == current_month} for m in range(1, 13)],
        'year_options': [{'value': y, 'selected': y == current_year} for y in range(2024, 2030)],
    }
    return render(request, 'app_avarias/dashboard.html', context)

@login_required
@group_required("Gestor")
def avaria_search(request):
    import logging
    logger = logging.getLogger(__name__)
    
    # Get Params
    q = request.GET.get('q') # Termo geral (optional)
    status = request.GET.get('status')
    data_ini = request.GET.get('data_ini')
    data_fim = request.GET.get('data_fim')
    
    # Specific Filters
    nf = request.GET.get('nf')
    nfd = request.GET.get('nfd') # NF Devolucao
    placa = request.GET.get('placa')
    cpf = request.GET.get('cpf')
    motorista = request.GET.get('motorista')
    local = request.GET.get('local')
    
    avarias = Avaria.objects.all().prefetch_related('itens__produto', 'cliente', 'veiculo', 'motorista').order_by('-data_criacao')
    
    # Generic Search
    if q:
        avarias = avarias.filter(
            Q(nota_fiscal__icontains=q) |
            Q(cliente__razao_social__icontains=q) |
            Q(itens__produto__nome__icontains=q) |
            Q(veiculo__placa__icontains=q) |
            Q(motorista__nome__icontains=q)
        ).distinct()
    
    # Specific Filters
    if status:
        avarias = avarias.filter(status=status)
    if data_ini:
        avarias = avarias.filter(data_criacao__date__gte=data_ini)
    if data_fim:
        avarias = avarias.filter(data_criacao__date__lte=data_fim)
        
    if nf:
        avarias = avarias.filter(nota_fiscal__icontains=nf)
    if nfd:
        avarias = avarias.filter(nf_devolucao__icontains=nfd)
    if placa:
        avarias = avarias.filter(
            Q(veiculo__placa__icontains=placa) | 
            Q(veiculo_carreta__placa__icontains=placa)
        )
    if cpf:
        avarias = avarias.filter(motorista__cpf__icontains=cpf)
    if motorista:
        avarias = avarias.filter(motorista__nome__icontains=motorista)
    if local:
        avarias = avarias.filter(local_atuacao__icontains=local)
        
    if request.GET.get('print'):
        from django.utils import timezone
        return render(request, 'app_avarias/avaria_search_print.html', {
            'avarias': avarias,
            'now': timezone.now()
        })
        
    return render(request, 'app_avarias/avaria_search.html', {'avarias': avarias})

@login_required
@group_required(["Gestor", "Operacional"])
def avaria_list(request):
    status_filter = request.GET.get('status', 'EM_ABERTO')
    cd_filter = request.GET.get('cd_id')
    
    avarias = Avaria.objects.all().prefetch_related('itens__produto').order_by('-data_criacao')
    
    dashboard_cds = None
    selected_cd_id = None
    
    if status_filter and status_filter != 'TODAS':
        avarias = avarias.filter(status=status_filter)
        
        # Dashboard logic for Aguardando Devolução
        if status_filter == 'AGUARDANDO_DEVOLUCAO':
            # Count Avarias per CD
            from .models import CentroDistribuicao
            dashboard_cds = (
                Avaria.objects.filter(status='AGUARDANDO_DEVOLUCAO', cd_armazenagem_reversa__isnull=False)
                .values('cd_armazenagem_reversa__id', 'cd_armazenagem_reversa__nome', 'cd_armazenagem_reversa__codigo')
                .annotate(total=Count('id'))
                .order_by('cd_armazenagem_reversa__nome')
            )
            
            # Apply CD filter if selected
            if cd_filter:
                try:
                    selected_cd_id = int(cd_filter)
                    avarias = avarias.filter(cd_armazenagem_reversa_id=selected_cd_id)
                except ValueError:
                    pass
        
    context = {
        'avarias': avarias,
        'current_filter': status_filter,
        'dashboard_cds': dashboard_cds,
        'selected_cd_id': selected_cd_id
    }
    return render(request, 'app_avarias/avaria_list.html', context)

# @login_required
# def avaria_create(request):
#     # This view is deprecated in favor of Class Based View, but kept for legacy reference or fallback
#     if request.method == 'POST':
#         form = AvariaForm(request.POST)
#         if form.is_valid():
#             avaria = form.save(commit=False)
#             avaria.criado_por = request.user
#             avaria.save()
#             messages.success(request, 'Avaria registrada com sucesso!')
#             return redirect('avaria_detail', pk=avaria.pk)
#     else:
#         form = AvariaForm()
#     
#     return render(request, 'app_avarias/avaria_form.html', {'form': form, 'title': 'Nova Avaria'})

@login_required
@group_required(["Gestor", "Operacional"])
def avaria_detail(request, pk):
    avaria = get_object_or_404(Avaria, pk=pk)
    fotos_ordenadas = avaria.fotos.select_related('criado_por').order_by('criado_por', '-data_upload')
    
    obs_form = AvariaObservacaoForm()
    
    # Forms for actions
    decisao_form = AvariaDecisaoForm()
    devolucao_form = AvariaDevolucaoForm(instance=avaria)
    photo_form = AvariaFotoForm()
    finalizacao_form = AvariaFinalizacaoDevolucaoForm() # New form
    
    if request.method == 'POST':
        if 'add_observacao' in request.POST:
            obs_form = AvariaObservacaoForm(request.POST)
            if obs_form.is_valid():
                texto = obs_form.cleaned_data['texto']
                timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
                new_entry = f"[{timestamp} - {request.user.username}] {texto}\n"
                if avaria.observacoes:
                    avaria.observacoes += "\n" + new_entry
                else:
                    avaria.observacoes = new_entry
                avaria.save()
                messages.success(request, 'Observação adicionada.')
                return redirect('avaria_detail', pk=pk)
        
        elif 'decisao' in request.POST:
            decisao_form = AvariaDecisaoForm(request.POST)
            if decisao_form.is_valid():
                acao = decisao_form.cleaned_data['acao']
                obs_text = decisao_form.cleaned_data.get('observacao', '')
                
                # NF Retention Info
                nf_retida = decisao_form.cleaned_data.get('nf_retida_conferencia')
                horas = decisao_form.cleaned_data.get('horas_retencao')
                
                retencao_str = ""
                if nf_retida == 'SIM':
                    retencao_str = f" | [NF RETIDA NA CONFERÊNCIA: SIM ({horas}h)]"
                else:
                    retencao_str = " | [NF RETIDA NA CONFERÊNCIA: NÃO]"
                
                # New fields for DEVOLVER
                nfd = decisao_form.cleaned_data.get('nf_devolucao', '')
                cd = decisao_form.cleaned_data.get('cd_armazenagem_reversa')
                
                # VALIDATION: NFD is mandatory for DEVOLVER
                if acao == 'DEVOLVER' and not nfd:
                    messages.error(request, 'Para encaminhar para devolução, é obrigatório informar a Nota Fiscal de Devolução (NFD).')
                    return redirect('avaria_detail', pk=pk)
                
                # Build comprehensive history entry
                cd_str = ""
                if acao == 'DEVOLVER' and cd:
                    cd_str = f" | [CD ARMAZENAGEM: {cd.codigo} - {cd.nome}]"
                
                nfd_str = ""
                if acao == 'DEVOLVER' and nfd:
                    nfd_str = f" | [NFD: {nfd}]"
                
                timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
                new_entry = f"[{timestamp} - {request.user.username}] [DECISÃO: {acao}]{retencao_str}{nfd_str}{cd_str} {obs_text}\n"

                if avaria.observacoes:
                    avaria.observacoes += "\n" + new_entry
                else:
                    avaria.observacoes = new_entry
                
                if acao == 'ACEITAR':
                    avaria.status = 'FINALIZADA'
                    avaria.tipo_finalizacao = 'ACEITE'
                    avaria.data_decisao = timezone.now()
                    avaria.data_finalizacao = timezone.now()
                    avaria.save()
                    messages.success(request, 'Avaria aceita e finalizada!')
                else: # DEVOLVER
                    avaria.status = 'AGUARDANDO_DEVOLUCAO'
                    avaria.data_decisao = timezone.now()
                    # Save NFD and CD here
                    if nfd:
                        avaria.nf_devolucao = nfd
                    if cd:
                        avaria.cd_armazenagem_reversa = cd
                    avaria.save()
                    messages.info(request, 'Avaria encaminhada para devolução. Aguardando dados de saída.')
                return redirect('avaria_detail', pk=pk)

        elif 'iniciar_devolucao' in request.POST:
            devolucao_form = AvariaDevolucaoForm(request.POST, request.FILES, instance=avaria)
            if devolucao_form.is_valid():
                avaria = devolucao_form.save(commit=False)
                
                avaria.status = 'EM_ROTA_DEVOLUCAO'
                avaria.data_inicio_devolucao = timezone.now()
                
                # History / Observation Log
                obs_text = devolucao_form.cleaned_data.get('observacao_extra') or ""
                timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
                new_entry = f"[{timestamp} - {request.user.username}] [SAÍDA DEVOLUÇÃO] {obs_text}\n"
                
                if avaria.observacoes:
                    avaria.observacoes += "\n" + new_entry
                else:
                    avaria.observacoes = new_entry
                        
                avaria.save()
                messages.success(request, 'Devolução iniciada! Avaria em Rota.')
                return redirect('avaria_detail', pk=pk)
            else:
                 messages.error(request, 'Erro ao iniciar devolução. Verifique o formulário e a foto obrigatória.')

        elif 'finalizar_devolucao' in request.POST:
            finalizacao_form = AvariaFinalizacaoDevolucaoForm(request.POST, request.FILES)
            if finalizacao_form.is_valid():
                comprovante = finalizacao_form.cleaned_data.get('arquivo_comprovante')
                if comprovante:
                    AvariaFoto.objects.create(avaria=avaria, arquivo=comprovante, criado_por=request.user)
                
                avaria.status = 'FINALIZADA'
                avaria.tipo_finalizacao = 'DEVOLUCAO_CONCLUIDA'
                avaria.data_finalizacao = timezone.now()
                
                # History Log
                timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
                new_entry = f"[{timestamp} - {request.user.username}] [DEVOLUÇÃO CONCLUÍDA] Processo finalizado com comprovante.\n"
                
                if avaria.observacoes:
                    avaria.observacoes += "\n" + new_entry
                else:
                    avaria.observacoes = new_entry
                    
                avaria.save()
                messages.success(request, 'Devolução concluída e finalizada!')
                return redirect('avaria_detail', pk=pk)
            else:
                messages.error(request, 'Foto do canhoto/entrega é obrigatória para finalizar.')

        elif 'upload_foto' in request.POST:
            files = request.FILES.getlist('arquivo')
            if files:
                for f in files:
                    AvariaFoto.objects.create(
                        avaria=avaria,
                        arquivo=f,
                        criado_por=request.user
                    )
                messages.success(request, f'{len(files)} foto(s) enviada(s) com sucesso!')
            else:
                messages.warning(request, 'Nenhum arquivo capturado. Tente novamente.')
            return redirect('avaria_detail', pk=pk)
        
        elif 'update_itens' in request.POST:
            # Handle items update
            from .models import AvariaItem
            
            # 1. Update Existing Items and Handle Deletions
            submitted_item_ids = request.POST.getlist('item_id[]')
            submitted_lotes = request.POST.getlist('lote[]')
            submitted_quantidades = request.POST.getlist('quantidade[]')
            
            # Delete items that are in DB but were not submitted (removed from DOM)
            # Filter submitted_ids to ensure they are valid integers
            valid_submitted_ids = []
            for mid in submitted_item_ids:
                try:
                    valid_submitted_ids.append(int(mid))
                except (ValueError, TypeError):
                    pass
            
            # Delete items belonging to this avaria that are NOT in the submitted list
            avaria.itens.exclude(id__in=valid_submitted_ids).delete()
            
            # Update values for submitted existing items
            for i, item_id in enumerate(submitted_item_ids):
                try:
                    item = AvariaItem.objects.get(id=item_id, avaria=avaria)
                    if i < len(submitted_lotes):
                        item.lote = submitted_lotes[i]
                    if i < len(submitted_quantidades):
                        try:
                            qtd = int(submitted_quantidades[i])
                            item.quantidade = max(0, qtd) # Ensure non-negative
                        except ValueError:
                            pass
                    item.save()
                except (AvariaItem.DoesNotExist, ValueError):
                    pass

            # 2. Handle New Items
            novos_produtos = request.POST.getlist('novo_produto_id[]')
            novos_lotes = request.POST.getlist('novo_lote[]')
            novas_quantidades = request.POST.getlist('novo_quantidade[]')
            
            for i, produto_id in enumerate(novos_produtos):
                if produto_id: # Ensure product ID is present
                    try:
                        qtd = 1
                        if i < len(novas_quantidades) and novas_quantidades[i]:
                            qtd = int(novas_quantidades[i])
                        
                        lote = ""
                        if i < len(novos_lotes):
                            lote = novos_lotes[i]
                            
                        AvariaItem.objects.create(
                            avaria=avaria,
                            produto_id=produto_id,
                            lote=lote,
                            quantidade=max(1, qtd)
                        )
                    except (ValueError, Exception) as e:
                        print(f"Erro ao criar novo item: {e}")
            
            # Log the change
            timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
            new_entry = f"[{timestamp} - {request.user.username}] [EDIÇÃO DE ITENS] Lista de produtos atualizada.\n"
            if avaria.observacoes:
                avaria.observacoes += "\n" + new_entry
            else:
                avaria.observacoes = new_entry
            avaria.save()
            
            messages.success(request, 'Alteraçoes salvas com sucesso!')
            return redirect('avaria_detail', pk=pk)
        
        elif 'update_valor' in request.POST:
            # Handle value update
            novo_valor = request.POST.get('novo_valor')
            motivo = request.POST.get('motivo_ajuste', '')
            
            if novo_valor:
                from decimal import Decimal
                try:
                    valor_anterior = avaria.valor_nf or Decimal('0')
                    avaria.valor_nf = Decimal(novo_valor)
                    
                    # Log the change
                    timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
                    new_entry = f"[{timestamp} - {request.user.username}] [AJUSTE DE VALOR] R$ {valor_anterior} → R$ {novo_valor} | Motivo: {motivo}\n"
                    if avaria.observacoes:
                        avaria.observacoes += "\n" + new_entry
                    else:
                        avaria.observacoes = new_entry
                        
                    avaria.save()
                    messages.success(request, 'Valor atualizado com sucesso!')
                except Exception as e:
                     messages.error(request, f'Erro ao atualizar valor: {e}')
            return redirect('avaria_detail', pk=pk)

        elif 'transferir_cd' in request.POST:
            transferencia_form = AvariaTransferenciaCDForm(request.POST)
            if transferencia_form.is_valid():
                novo_cd = transferencia_form.cleaned_data['cd_armazenagem_reversa']
                obs_transferencia = transferencia_form.cleaned_data.get('observacoes', '').strip()
                cd_antigo = avaria.cd_armazenagem_reversa
                
                if cd_antigo != novo_cd:
                    avaria.cd_armazenagem_reversa = novo_cd
                    
                    # History Log
                    timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
                    nome_antigo = f"{cd_antigo.codigo} - {cd_antigo.nome}" if cd_antigo else "Nenhum"
                    nome_novo = f"{novo_cd.codigo} - {novo_cd.nome}"
                    
                    new_entry = (
                        f"[{timestamp} - {request.user.username}] [TRANSFERÊNCIA CD]\n"
                        f"CD de Origem: {nome_antigo}\n"
                        f"CD de Destino: {nome_novo}\n"
                        f"Observação adicional:\n{obs_transferencia}\n"
                    )
                    
                    if avaria.observacoes:
                        avaria.observacoes += "\n" + new_entry
                    else:
                        avaria.observacoes = new_entry
                        
                    avaria.save()
                    messages.success(request, f'Avaria transferida com sucesso para {novo_cd.nome}!')
                else:
                    messages.warning(request, 'O CD de destino é o mesmo do atual.')
            else:
                messages.error(request, 'Erro ao transferir CD. Verifique os dados.')
            return redirect('avaria_detail', pk=pk)

    else:
        # GET request
        form = AvariaForm(instance=avaria)
        decisao_form = AvariaDecisaoForm(initial={
            'acao': avaria.acao,
            'nf_retida_conferencia': avaria.nf_retida_conferencia,
            'horas_retencao': avaria.horas_retencao,
            'nf_devolucao': avaria.nf_devolucao,
            'cd_armazenagem_reversa': avaria.cd_armazenagem_reversa,
        })
        devolucao_form = AvariaDevolucaoForm(instance=avaria)
        finalizacao_form = AvariaFinalizacaoDevolucaoForm()
        definicao_prejuizo_form = AvariaDefinicaoPrejuizoForm(instance=avaria)
        observacao_form = AvariaObservacaoForm()
        foto_form = AvariaFotoForm()
        cd_form = CentroDistribuicaoForm()
        edicao_itens_form = AvariaEdicaoItensForm(initial={'valor_nf': avaria.valor_nf})
        transferencia_cd_form = AvariaTransferenciaCDForm(initial={'cd_armazenagem_reversa': avaria.cd_armazenagem_reversa})
        fotos = avaria.fotos.all().order_by('-data_upload')

    context = {
        'avaria': avaria,
        'form': form,
        'decisao_form': decisao_form,
        'devolucao_form': devolucao_form,
        'finalizacao_form': finalizacao_form,
        'definicao_prejuizo_form': definicao_prejuizo_form,
        'observacao_form': observacao_form,
        'foto_form': foto_form,
        'fotos': fotos,
        'fotos_ordenadas': fotos_ordenadas,
        'cd_form': cd_form,
        'edicao_itens_form': edicao_itens_form,
        'transferencia_cd_form': transferencia_cd_form,
        'produtos': Produto.objects.all().order_by('nome'),
    }
    response = render(request, 'app_avarias/avaria_detail.html', context)
    # Force browser to not cache this page
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
@group_required("Gestor")
def avaria_definicao_prejuizo_list(request):
    """
    List of finalized avarias (Devolucao Return) that need prejudice responsibility definition.
    """
    # Only show items that are Finalized (Returned or maybe Accepted?) and have no definition yet
    # Assuming only DEVOLUCAO_CONCLUIDA requires this step per request instructions ("Depois de finalizada (Devolução entregue)")
    qs = Avaria.objects.filter(
        status='FINALIZADA',
        tipo_finalizacao='DEVOLUCAO_CONCLUIDA',
        responsavel_prejuizo__isnull=True
    ).order_by('-data_finalizacao')
    
    if request.method == 'POST':
        avaria_pk = request.POST.get('avaria_id')
        avaria = get_object_or_404(Avaria, pk=avaria_pk)
        form = AvariaDefinicaoPrejuizoForm(request.POST, instance=avaria)
        if form.is_valid():
            # Before saving, capture the responsibility for logging
            responsavel = form.cleaned_data.get('responsavel_prejuizo')
            
            # History Log
            timestamp = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
            
            # Detailed text construction
            detalhes_responsavel = ""
            if responsavel == 'TRANSBIRDAY':
                detalhes_responsavel = "TRANSPORTES BIRDAY COMERCIO LTDA (00.343.915/0001-08)"
            elif responsavel == 'CLIENTE':
                detalhes_responsavel = f"{avaria.cliente.razao_social} ({avaria.cliente.cnpj})"
            elif responsavel == 'TRANSPORTADORA_TERCEIRA':
                if avaria.veiculo.propriedade == 'TERCEIRO':
                    detalhes_responsavel = f"{avaria.veiculo.transportadora_nome} ({avaria.veiculo.transportadora_cnpj})"
                else:
                    # Fallback if selected transport service but it's not registered as third party (unlikely but safe)
                    detalhes_responsavel = "Transportadora Terceira (Dados não vinculados ao veículo)"
            
            new_entry = f"[{timestamp} - {request.user.username}] [DEFINIÇÃO DE PREJUÍZO] Responsável: {avaria.get_responsavel_prejuizo_display()} - {detalhes_responsavel}\n"
            
            # We need to manually update observations since form only updates responsavel_prejuizo
            # But wait, form.save() saves the instance. If we modify instance before save, it works.
            avaria = form.save(commit=False)
            
            if avaria.observacoes:
                avaria.observacoes += "\n" + new_entry
            else:
                avaria.observacoes = new_entry
            
            avaria.save()
            messages.success(request, f'Responsabilidade definida para Avaria #{avaria.id}')
            return redirect('avaria_definicao_prejuizo_list')
    
    return render(request, 'app_avarias/avaria_prejuizo_list.html', {'avarias': qs})

@login_required
def avaria_print(request, pk):
    avaria = get_object_or_404(Avaria, pk=pk)
    show_photos = request.GET.get('fotos') == '1'
    
    fotos = []
    if show_photos:
        fotos = avaria.fotos.all().order_by('criado_por', '-data_upload')
        
    context = {
        'avaria': avaria,
        'show_photos': show_photos,
        'fotos': fotos
    }
    return render(request, 'app_avarias/avaria_print.html', context)

def offline_view(request):
    return render(request, 'app_avarias/offline.html')
