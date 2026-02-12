from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from app_avarias.models import Avaria, Cliente, Produto, Veiculo, Condutor

User = get_user_model()

class ImprovementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        # Setup basic data
        self.cliente = Cliente.objects.create(razao_social="Cliente Teste", cnpj="11111111111111")
        self.produto = Produto.objects.create(nome="Produto Teste", codigo_controle="123")
        self.veiculo = Veiculo.objects.create(placa="ABC1234", tipo="PRINCIPAL")
        self.condutor = Condutor.objects.create(nome="Motorista Teste", cpf="11122233344")

    def test_nf_retention_flow(self):
        """Test if NF retention info is saved to observations"""
        avaria = Avaria.objects.create(
            cliente=self.cliente, produto=self.produto, nota_fiscal="333",
            veiculo=self.veiculo, motorista=self.condutor,
            status='EM_ABERTO', criado_por=self.user
        )
        url = reverse('avaria_detail', kwargs={'pk': avaria.pk})
        
        # Test case: Yes with 5 hours
        data = {
            'decisao': '1', # Trigger decision block
            'acao': 'ACEITAR', # Accept to finalize
            'nf_retida_conferencia': 'SIM',
            'horas_retencao': 5,
            'observacao': 'Test decision note'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Redirects
        
        avaria.refresh_from_db()
        self.assertIn("NF RETIDA NA CONFERÊNCIA: SIM (5h)", avaria.observacoes)
        self.assertIn("DECISÃO: ACEITAR", avaria.observacoes)
        
        # Test case: No retention
        avaria2 = Avaria.objects.create(
            cliente=self.cliente, produto=self.produto, nota_fiscal="444",
            veiculo=self.veiculo, motorista=self.condutor,
            status='EM_ABERTO', criado_por=self.user
        )
        url2 = reverse('avaria_detail', kwargs={'pk': avaria2.pk})
        data2 = {
            'decisao': '1',
            'acao': 'DEVOLVER',
            'nf_retida_conferencia': 'NAO',
            'observacao': 'Returning'
        }
        self.client.post(url2, data2)
        avaria2.refresh_from_db()
        self.assertIn("NF RETIDA NA CONFERÊNCIA: NÃO", avaria2.observacoes)

    def test_avaria_creation_logging(self):
        """Test if creation log is added to observations"""
        url = reverse('avaria_create')
        data = {
            'cliente': self.cliente.pk,
            'nota_fiscal': '9999',
            'valor_nf': '100.00',
            'veiculo': self.veiculo.pk,
            'veiculo_carreta': '',
            'motorista': self.condutor.pk,
            'produto': [self.produto.pk], # List for SelectMultiple
            'quantidade': 1,
            'observacoes': 'Initial observation',
            'local_atuacao': 'CD Teste',
            'criado_por': self.user.pk
        }
        response = self.client.post(url, data)
        # Should redirect to list or detail? CRUD View typically redirects to success_url (list)
        # But wait, my code says: return redirect(self.success_url) which is 'avaria_list'
        self.assertEqual(response.status_code, 302)
        
        # Check the created avaria
        avaria = Avaria.objects.filter(nota_fiscal='9999').first()
        self.assertIsNotNone(avaria)
        self.assertIn("[ABERTURA] Initial observation", avaria.observacoes)
        self.assertIn(self.user.username, avaria.observacoes)

    def test_avaria_finalization_logging(self):
        """Test if finalization log is added"""
        # Create avaria in EM_ROTA_DEVOLUCAO
        avaria = Avaria.objects.create(
            cliente=self.cliente, produto=self.produto, nota_fiscal="555",
            veiculo=self.veiculo, motorista=self.condutor,
            status='EM_ROTA_DEVOLUCAO', criado_por=self.user,
            observacoes="Previous logs..."
        )
        url = reverse('avaria_detail', kwargs={'pk': avaria.pk})
        
        # Prepare file for upload
        dummy_file = SimpleUploadedFile("canhoto.jpg", b"file_content", content_type="image/jpeg")
        
        data = {
            'finalizar_devolucao': '1',
            'arquivo_comprovante': dummy_file
        }
        
        self.client.post(url, data)
        avaria.refresh_from_db()
        
        self.assertEqual(avaria.status, 'FINALIZADA')
        self.assertIn("[DEVOLUÇÃO CONCLUÍDA]", avaria.observacoes)
        self.assertIn("Processo finalizado com comprovante", avaria.observacoes)

    def test_prejudice_definition_logging(self):
        """Test if prejudice definition is logged"""
        # Create finalized return without definition
        avaria = Avaria.objects.create(
            cliente=self.cliente, produto=self.produto, nota_fiscal="666",
            veiculo=self.veiculo, motorista=self.condutor,
            status='FINALIZADA', tipo_finalizacao='DEVOLUCAO_CONCLUIDA',
            data_finalizacao=timezone.now(),
            criado_por=self.user
        )
        url = reverse('avaria_definicao_prejuizo_list')
        
        data = {
            'avaria_id': avaria.pk,
            'responsavel_prejuizo': 'TRANSBIRDAY'
        }
        
        self.client.post(url, data)
        avaria.refresh_from_db()
        
        self.assertEqual(avaria.responsavel_prejuizo, 'TRANSBIRDAY')
        self.assertIn("[DEFINIÇÃO DE PREJUÍZO]", avaria.observacoes)
        self.assertIn("Responsável: TRANSBIRDAY", avaria.observacoes)

    def test_transportadora_terceira_choice(self):
        """Test if TRANSPORTADORA_TERCEIRA is accepted and saved"""
        avaria = Avaria.objects.create(
            cliente=self.cliente, produto=self.produto, nota_fiscal="777",
            veiculo=self.veiculo, motorista=self.condutor,
            status='FINALIZADA', tipo_finalizacao='DEVOLUCAO_CONCLUIDA',
            data_finalizacao=timezone.now(),
            criado_por=self.user
        )
        url = reverse('avaria_definicao_prejuizo_list')
        data = {
            'avaria_id': avaria.pk,
            'responsavel_prejuizo': 'TRANSPORTADORA_TERCEIRA'
        }
        self.client.post(url, data)
        avaria.refresh_from_db()
        
        self.assertEqual(avaria.responsavel_prejuizo, 'TRANSPORTADORA_TERCEIRA')
        self.assertIn("Responsável: TRANSPORTADORA_TERCEIRA", avaria.observacoes)

    def test_dynamic_item_creation(self):
        """Test multi-item creation with dynamic rows"""
        url = reverse('avaria_create')
        
        # Create another product
        prod2 = Produto.objects.create(nome="Second Product", codigo_controle="P2", ativo=True)
        
        data = {
            'cliente': self.cliente.pk,
            'nota_fiscal': 'MULTIGEM',
            'valor_nf': '500.00',
            'veiculo': self.veiculo.pk,
            'veiculo_carreta': '',
            'motorista': self.condutor.pk,
            'observacoes': 'Batch Obs',
            'local_atuacao': 'CD Teste',
            'criado_por': self.user.pk,
            
            # Dynamic Fields (Lists)
            'produto[]': [self.produto.pk, prod2.pk],
            'quantidade[]': ['2', '5'],
            'lote[]': ['L1', 'L2'],
            'observacao_item[]': ['Item 1 damaged', 'Item 2 broken']
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check created items
        items = Avaria.objects.filter(nota_fiscal='MULTIGEM').order_by('id')
        self.assertEqual(items.count(), 2)
        
        item1 = items[0]
        self.assertEqual(item1.produto, self.produto)
        self.assertEqual(item1.quantidade, 2)
        self.assertIn("Batch Obs", item1.observacoes)
        
        item2 = items[1]
        self.assertEqual(item2.produto, prod2)
        self.assertEqual(item2.quantidade, 5)
        self.assertIn("Batch Obs", item2.observacoes)

    def test_batch_item_observations(self):
        """Test if both items in a batch get the general observation"""
        url = reverse('avaria_create')
        prod2 = Produto.objects.create(nome="Second", codigo_controle="P2", ativo=True)
        
        data = {
            'cliente': self.cliente.pk,
            'nota_fiscal': 'OBS_TEST_NF',
            'valor_nf': '100.00',
            'veiculo': self.veiculo.pk,
            'veiculo_carreta': '',
            'motorista': self.condutor.pk,
            'observacoes': 'GeneralHeader',
            'local_atuacao': 'Matrix',
            'criado_por': self.user.pk,
            # Lists
            'produto[]': [self.produto.pk, prod2.pk],
            'quantidade[]': ['1', '1'],
            'lote[]': ['L1', 'L2'],
            # 'observacao_item[]': ['First Obs', 'Second Obs'] # Removed from form
        }
        self.client.post(url, data)
        
        items = Avaria.objects.filter(nota_fiscal='OBS_TEST_NF').order_by('id')
        self.assertEqual(items.count(), 2)
        
        # Check Item 1
        item1 = items[0]
        self.assertIn("GeneralHeader", item1.observacoes)
        # self.assertIn("ITEM: First Obs", item1.observacoes) # Removed
        
        # Check Item 2
        item2 = items[1]
        self.assertIn("GeneralHeader", item2.observacoes)
        # self.assertIn("ITEM: Second Obs", item2.observacoes) # Removed
