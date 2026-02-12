import 'package:flutter/material.dart';
import '../screens/simple_crud_screen.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          const DrawerHeader(
            decoration: BoxDecoration(color: Colors.blue),
            child: Text('Avarias App',
                style: TextStyle(color: Colors.white, fontSize: 24)),
          ),
          ListTile(
            leading: const Icon(Icons.home),
            title: const Text('Avarias'),
            onTap: () => Navigator.pop(context),
          ),
          const Divider(),
          _buildMenuItem(
              context,
              'Clientes',
              'clientes',
              [
                CrudField('razao_social', 'Razão Social'),
                CrudField('cnpj', 'CNPJ', type: TextInputType.number),
                CrudField('telefone_contato', 'Telefone',
                    type: TextInputType.phone),
              ],
              'razao_social',
              'cnpj'),
          _buildMenuItem(
              context,
              'Motoristas',
              'condutores',
              [
                CrudField('nome', 'Nome'),
                CrudField('cpf', 'CPF', type: TextInputType.number),
                CrudField('telefone', 'Telefone', type: TextInputType.phone),
              ],
              'nome',
              'cpf'),
          _buildMenuItem(
              context,
              'Veículos',
              'veiculos',
              [
                CrudField('placa', 'Placa'),
                CrudField('modelo', 'Modelo'),
                // Note: 'tipo' and 'propriedade' are defaults in Model or need Select in full implementation.
                // We'll leave basic fields for quick add.
              ],
              'placa',
              'modelo'),
          _buildMenuItem(
              context,
              'Produtos',
              'produtos',
              [
                CrudField('nome', 'Nome'),
                CrudField('laboratorio', 'Laboratório'),
                CrudField('codigo_controle', 'Cód. Controle'),
              ],
              'nome',
              'laboratorio'),
        ],
      ),
    );
  }

  Widget _buildMenuItem(BuildContext context, String title, String endpoint,
      List<CrudField> fields, String displayKey, String subKey) {
    return ListTile(
      leading: const Icon(Icons.settings),
      title: Text(title),
      onTap: () {
        Navigator.pop(context);
        Navigator.push(
            context,
            MaterialPageRoute(
                builder: (ctx) => SimpleCrudScreen(
                      title: title,
                      endpoint: endpoint,
                      fields: fields,
                      titleKey: displayKey,
                      subtitleKey: subKey,
                    )));
      },
    );
  }
}
