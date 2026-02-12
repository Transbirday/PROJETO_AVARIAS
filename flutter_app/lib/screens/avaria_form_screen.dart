import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/camera_service.dart';

class AvariaItemTemp {
  final int produtoId;
  final int quantidade;

  AvariaItemTemp(this.produtoId, this.quantidade);
}

class AvariaFormScreen extends StatefulWidget {
  const AvariaFormScreen({super.key});

  @override
  State<AvariaFormScreen> createState() => _AvariaFormScreenState();
}

class _AvariaFormScreenState extends State<AvariaFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _api = ApiService();
  final _cameraService = CameraService();

  // Header Controllers
  final _clienteIdController = TextEditingController();
  final _nfController = TextEditingController();

  // Item Controllers
  final _produtoIdController = TextEditingController();
  final _qtdController = TextEditingController();

  // Data
  final List<AvariaItemTemp> _items = [];
  final List<File> _imageFiles = [];
  bool _isSubmitting = false;

  Future<void> _takePhoto() async {
    final file = await _cameraService.takePhoto();
    if (file != null) {
      setState(() => _imageFiles.add(file));
    }
  }

  void _addItem() {
    final prodId = int.tryParse(_produtoIdController.text);
    final qtd = int.tryParse(_qtdController.text);

    if (prodId != null && qtd != null && prodId > 0 && qtd > 0) {
      setState(() {
        _items.add(AvariaItemTemp(prodId, qtd));
        // Reset input fields
        _produtoIdController.clear();
        _qtdController.clear();
      });
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('ID do Produto e Quantidade inválidos')),
      );
    }
  }

  void _removeItem(int index) {
    setState(() {
      _items.removeAt(index);
    });
  }

  void _submit() async {
    if (_formKey.currentState!.validate()) {
      if (_items.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Adicione pelo menos um item.')),
        );
        return;
      }

      setState(() => _isSubmitting = true);

      final data = {
        'cliente': int.tryParse(_clienteIdController.text),
        'nota_fiscal': _nfController.text,
        'itens': _items
            .map((i) => {
                  'produto': i.produtoId,
                  'quantidade': i.quantidade,
                  'lote': 'APP-MOBILE' // Default placeholder
                })
            .toList(),
      };

      try {
        final newId = await _api.createAvariaReturningId(data);

        if (newId != null) {
          // Upload Photos
          int successCount = 0;
          for (final file in _imageFiles) {
            final result = await _api.uploadPhoto(newId, file);
            if (result) successCount++;
          }

          if (mounted) {
            Navigator.pop(context);
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                  content:
                      Text('Avaria registrada! $successCount fotos enviadas.')),
            );
          }
        } else {
          throw Exception('Falha ao criar avaria (ID nulo)');
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Erro: $e')),
          );
        }
      } finally {
        if (mounted) setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nova Avaria (Multi-Item)')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              // --- Header ---
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(children: [
                    TextFormField(
                      controller: _clienteIdController,
                      decoration: const InputDecoration(
                          labelText: 'ID Cliente', hintText: 'Insira o ID'),
                      keyboardType: TextInputType.number,
                      validator: (v) => v!.isEmpty ? 'Campo obrigatório' : null,
                    ),
                    const SizedBox(height: 10),
                    TextFormField(
                      controller: _nfController,
                      decoration:
                          const InputDecoration(labelText: 'Nota Fiscal'),
                      validator: (v) => v!.isEmpty ? 'Campo obrigatório' : null,
                    ),
                  ]),
                ),
              ),
              const SizedBox(height: 16),

              // --- Items Section ---
              const Text("Itens da Avaria",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),

              // Item List
              if (_items.isNotEmpty)
                ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _items.length,
                    itemBuilder: (ctx, idx) {
                      final item = _items[idx];
                      return ListTile(
                        leading: CircleAvatar(child: Text('${idx + 1}')),
                        title: Text('Produto ID: ${item.produtoId}'),
                        subtitle: Text('Qtd: ${item.quantidade}'),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete, color: Colors.red),
                          onPressed: () => _removeItem(idx),
                        ),
                      );
                    }),
              if (_items.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Text("Nenhum item adicionado",
                      style: TextStyle(color: Colors.grey)),
                ),

              // Add Item Form
              Card(
                color: Colors.grey[100],
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _produtoIdController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'ID Produto', isDense: true),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          controller: _qtdController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Qtd', isDense: true),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.add_circle, color: Colors.blue),
                        onPressed: _addItem,
                      )
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // --- Photos ---
              const Text("Fotos",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              if (_imageFiles.isNotEmpty)
                SizedBox(
                  height: 120,
                  child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: _imageFiles.length,
                    itemBuilder: (ctx, index) {
                      return Stack(
                        alignment: Alignment.topRight,
                        children: [
                          Container(
                            margin: const EdgeInsets.only(right: 8, top: 8),
                            child: Image.file(_imageFiles[index],
                                width: 100, height: 100, fit: BoxFit.cover),
                          ),
                          InkWell(
                            onTap: () =>
                                setState(() => _imageFiles.removeAt(index)),
                            child: const CircleAvatar(
                              radius: 12,
                              backgroundColor: Colors.red,
                              child: Icon(Icons.close,
                                  size: 16, color: Colors.white),
                            ),
                          )
                        ],
                      );
                    },
                  ),
                ),

              OutlinedButton.icon(
                onPressed: _takePhoto,
                icon: const Icon(Icons.camera_alt),
                label: Text(_imageFiles.isEmpty
                    ? 'Tirar Foto'
                    : 'Adicionar Mais Fotos'),
              ),

              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _isSubmitting ? null : _submit,
                icon: const Icon(Icons.check),
                label: const Text('REGISTRAR AVARIA'),
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                  backgroundColor: Colors.blue[800],
                  foregroundColor: Colors.white,
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
}
