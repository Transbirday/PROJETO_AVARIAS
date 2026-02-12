
import os
import django
import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
import string

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app_avarias.models import Usuario, Cliente, Condutor, Veiculo, Produto, Avaria, AvariaItem, CentroDistribuicao

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    if int_delta <= 0: return start
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

def populate_avarias(n=350):
    print(f"⌛ Iniciando geração de {n} Avarias históricas...")
    
    users = list(Usuario.objects.all())
    clientes = list(Cliente.objects.all())
    produtos = list(Produto.objects.all())
    condutores = list(Condutor.objects.filter(ativo=True))
    veiculos_principais = list(Veiculo.objects.filter(tipo='PRINCIPAL', ativo=True))
    veiculos_carreta = list(Veiculo.objects.filter(tipo='CARRETA', ativo=True))
    cds = list(CentroDistribuicao.objects.filter(ativo=True))
    
    if not all([users, clientes, produtos, condutores, veiculos_principais]):
        print("❌ Erro: Certifique-se de que Usuários, Clientes, Produtos, Condutores e Veículos existem no banco.")
        return

    # Data inicial: 1º de Janeiro de 2020
    start_date = timezone.make_aware(timezone.datetime(2020, 1, 1))
    end_date = timezone.now()
    
    locais = ['SP - Matriz', 'RJ - Filial', 'MG - Filial', 'PR - Distribuição', 'Porto Seco', 'CD Cliente']
    created_count = 0
    
    for i in range(n):
        dt_criacao = random_date(start_date, end_date)
        user = random.choice(users)
        client = random.choice(clientes)
        driver = random.choice(condutores)
        vehicle = random.choice(veiculos_principais)
        
        avaria = Avaria(
            cliente=client,
            nota_fiscal=f"{random.randint(100000, 999999)}",
            motorista=driver,
            veiculo=vehicle,
            criado_por=user,
            local_atuacao=random.choice(locais),
            observacoes="Registro histórico gerado automaticamente para testes.",
            status='EM_ABERTO'
        )
        avaria.save() # Need ID for items
        avaria.data_criacao = dt_criacao # Overwrite auto_now_add
        avaria.save()

        # Decide o destino da avaria
        # 5% Em Aberto, 5% Aguardando Devolução, 5% Em Rota, 85% Finalizada
        prob = random.random()
        
        if prob < 0.05:
            avaria.status = 'EM_ABERTO'
        elif prob < 0.10:
            avaria.status = 'AGUARDANDO_DEVOLUCAO'
            avaria.data_decisao = dt_criacao + timedelta(hours=random.randint(2, 48))
            avaria.acao = 'DEVOLVER'
            if cds: avaria.cd_armazenagem_reversa = random.choice(cds)
            avaria.nf_devolucao = f"NFD-{random.randint(1000, 9000)}"
        elif prob < 0.15:
            avaria.status = 'EM_ROTA_DEVOLUCAO'
            avaria.data_decisao = dt_criacao + timedelta(hours=random.randint(2, 24))
            avaria.data_inicio_devolucao = avaria.data_decisao + timedelta(days=random.randint(1, 3))
            avaria.acao = 'DEVOLVER'
            avaria.motorista_devolucao = random.choice(condutores)
            avaria.veiculo_devolucao = random.choice(veiculos_principais)
            if cds: avaria.cd_armazenagem_reversa = random.choice(cds)
        else:
            # FINALIZADA
            avaria.status = 'FINALIZADA'
            dt_decision = dt_criacao + timedelta(hours=random.randint(4, 72))
            avaria.data_decisao = dt_decision
            
            # Sub-tipo: Aceite (60%) vs Devolução Concluída (40%)
            if random.random() < 0.6:
                avaria.tipo_finalizacao = 'ACEITE'
                avaria.acao = 'ACEITAR'
                avaria.data_finalizacao = dt_decision
                # Responsabilidade Financeira
                avaria.responsavel_prejuizo = random.choice(['TRANSBIRDAY', 'CLIENTE', 'TRANSPORTADORA_TERCEIRA'])
                avaria.valor_nf = Decimal(random.uniform(100, 8000)).quantize(Decimal('0.01'))
            else:
                avaria.tipo_finalizacao = 'DEVOLUCAO_CONCLUIDA'
                avaria.acao = 'DEVOLVER'
                avaria.data_inicio_devolucao = dt_decision + timedelta(days=random.randint(1, 2))
                avaria.data_finalizacao = avaria.data_inicio_devolucao + timedelta(days=random.randint(1, 4))
                avaria.nf_devolucao = f"NFD-{random.randint(1000, 9000)}"
                if cds: avaria.cd_armazenagem_reversa = random.choice(cds)

        # Dados Adicionais aleatórios
        avaria.nf_retida_conferencia = random.choice(['SIM', 'NAO'])
        if avaria.nf_retida_conferencia == 'SIM':
            avaria.horas_retencao = random.randint(1, 12)
        
        if random.random() < 0.3 and veiculos_carreta:
            avaria.veiculo_carreta = random.choice(veiculos_carreta)

        avaria.save()

        # Add Items to Avaria
        for _ in range(random.randint(1, 4)):
            AvariaItem.objects.create(
                avaria=avaria,
                produto=random.choice(produtos),
                quantidade=random.randint(1, 20),
                lote=f"LOT-{random.randint(100, 999)}"
            )
            
        created_count += 1
        if created_count % 50 == 0:
            print(f"✅ {created_count} avarias geradas...")

    print(f"✨ Sucesso! {created_count} Avarias criadas desde 2020.")

if __name__ == '__main__':
    populate_avarias(400)

if __name__ == '__main__':
    populate_avarias(350)
