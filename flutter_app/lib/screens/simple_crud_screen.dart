import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CrudField {
  final String key;
  final String label;
  final TextInputType type;

  CrudField(this.key, this.label, {this.type = TextInputType.text});
}

class SimpleCrudScreen extends StatefulWidget {
  final String title;
  final String endpoint;
  final List<CrudField> fields;
  final String titleKey; // Key to display in list tile
  final String? subtitleKey;

  const SimpleCrudScreen({
    super.key,
    required this.title,
    required this.endpoint,
    required this.fields,
    required this.titleKey,
    this.subtitleKey,
  });

  @override
  State<SimpleCrudScreen> createState() => _SimpleCrudScreenState();
}

class _SimpleCrudScreenState extends State<SimpleCrudScreen> {
  final _api = ApiService();
  late Future<List<dynamic>> _dataFuture;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  void _loadData() {
    setState(() {
      _dataFuture = _api.getList(widget.endpoint);
    });
  }

  void _showAddDialog() {
    final Map<String, TextEditingController> controllers = {};
    for (var f in widget.fields) {
      controllers[f.key] = TextEditingController();
    }

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Novo ${widget.title}'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: widget.fields.map((f) {
              return TextField(
                controller: controllers[f.key],
                decoration: InputDecoration(labelText: f.label),
                keyboardType: f.type,
              );
            }).toList(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              final Map<String, dynamic> data = {};
              controllers.forEach((key, controller) {
                // Simple assumption: all generic fields are strings for now, or naive parsing
                // For a robust app, we'd handle types better.
                data[key] = controller.text;
              });

              final success = await _api.createItem(widget.endpoint, data);
              if (success) {
                if (mounted) {
                  Navigator.pop(ctx);
                  _loadData();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Salvo com sucesso!')),
                  );
                }
              } else {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Erro ao salvar.')),
                  );
                }
              }
            },
            child: const Text('Salvar'),
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddDialog,
        child: const Icon(Icons.add),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Erro: ${snapshot.error}'));
          }
          final list = snapshot.data ?? [];
          if (list.isEmpty) {
            return const Center(child: Text('Nenhum registro.'));
          }

          return ListView.builder(
            itemCount: list.length,
            itemBuilder: (context, index) {
              final item = list[index];
              return Card(
                child: ListTile(
                  title: Text(item[widget.titleKey]?.toString() ?? '-'),
                  subtitle: widget.subtitleKey != null
                      ? Text(item[widget.subtitleKey]?.toString() ?? '')
                      : null,
                ),
              );
            },
          );
        },
      ),
    );
  }
}
