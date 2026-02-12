
import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/camera_service.dart';

class AvariaDetailsScreen extends StatefulWidget {
  final Map<String, dynamic> avaria;

  const AvariaDetailsScreen({super.key, required this.avaria});

  @override
  State<AvariaDetailsScreen> createState() => _AvariaDetailsScreenState();
}

class _AvariaDetailsScreenState extends State<AvariaDetailsScreen> {
  final _api = ApiService();
  final _cameraService = CameraService();
  
  final List<File> _newPhotos = [];
  bool _isUploading = false;

  Future<void> _takePhoto() async {
    final file = await _cameraService.takePhoto();
    if (file != null) {
      setState(() => _newPhotos.add(file));
    }
  }

  Future<void> _uploadPhotos() async {
    if (_newPhotos.isEmpty) return;
    
    setState(() => _isUploading = true);
    final id = widget.avaria['id'];
    
    int successCount = 0;
    for (final file in _newPhotos) {
        final success = await _api.uploadPhoto(id, file);
        if (success) successCount++;
    }
    
    setState(() => _isUploading = false);
    
    if (mounted) {
      if (successCount > 0) {
        setState(() => _newPhotos.clear());
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$successCount fotos enviadas com sucesso!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Erro ao enviar fotos.')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final item = widget.avaria;
    
    return Scaffold(
      appBar: AppBar(title: Text('Avaria #${item['id']}')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Info
            _buildInfoRow('Cliente', item['cliente_nome']),
            _buildInfoRow('Produto', item['produto_nome']),
            _buildInfoRow('Nota Fiscal', item['nota_fiscal']),
            _buildInfoRow('Quantidade', '${item['quantidade']}'),
            _buildInfoRow('Status', item['status_display'] ?? item['status']),
            
            const Divider(height: 32),
            
            const Text('Adicionar Foto', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            
            if (_newPhotos.isNotEmpty)
              Column(
                children: [
                   SizedBox(
                    height: 120,
                    child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _newPhotos.length,
                        itemBuilder: (ctx, index) {
                        return Stack(
                            alignment: Alignment.topRight,
                            children: [
                            Container(
                                margin: const EdgeInsets.only(right: 8),
                                child: Image.file(_newPhotos[index], width: 100, height: 100, fit: BoxFit.cover),
                            ),
                            InkWell(
                                onTap: () => setState(() => _newPhotos.removeAt(index)),
                                child: const CircleAvatar(
                                radius: 12,
                                backgroundColor: Colors.red,
                                child: Icon(Icons.close, size: 16, color: Colors.white),
                                ),
                            )
                            ],
                        );
                        },
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                        Expanded(
                            child: OutlinedButton(
                                onPressed: _takePhoto, // Add more
                                child: const Text('Adicionar Mais')
                            )
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                            child: ElevatedButton.icon(
                                onPressed: _isUploading ? null : _uploadPhotos,
                                icon: const Icon(Icons.cloud_upload),
                                label: Text('Enviar (${_newPhotos.length})'),
                            )
                        ),
                    ],
                  )
                ],
              )
            else
               OutlinedButton.icon(
                onPressed: _takePhoto,
                icon: const Icon(Icons.camera_alt),
                label: const Text('Tirar Foto com a Câmera'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
              ),
              
            const SizedBox(height: 8),
            if (_isUploading) const LinearProgressIndicator(),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String? value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 100, child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.grey))),
          Expanded(child: Text(value ?? '-')),
        ],
      ),
    );
  }
}
