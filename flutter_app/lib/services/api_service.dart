import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // Use your local IP here if testing on emulator (e.g., 10.0.2.2 for Android)
  // For Windows development, it might be localhost:8000
  static const String baseUrl = 'http://192.168.10.32:8000/api';

  Future<String?> getToken() async {
    // In a real app, use SharedPreferences or FlutterSecureStorage
    // For this demo, we'll return a stored static variable or mock
    // Implementation of shared_preferences:
    // final prefs = await SharedPreferences.getInstance();
    // return prefs.getString('token');
    return _token;
  }

  static String? _token;

  Future<bool> login(String username, String password) async {
    // Note: This requires a JWT or Token Auth endpoint on Django.
    // Standard Django login creates a session. DRF commonly uses TokenAuth.
    // I will assume Basic Auth for simplicity in this generated code
    // OR we can implement a token endpoint.
    // Let's assume we use the Session or basic manual token auth.
    // Use Basic Auth header for now or implement a obtain_auth_token view in Django.

    // Simulating success for the user to proceed with building
    final String basicAuth =
        'Basic ${base64Encode(utf8.encode('$username:$password'))}';

    try {
      print('Tentando login em: $baseUrl/avarias/');
      final response = await http.get(
        Uri.parse('$baseUrl/avarias/'), // Test endpoint
        headers: {'Authorization': basicAuth},
      ).timeout(const Duration(seconds: 10));

      print('Resposta Login: ${response.statusCode}');

      if (response.statusCode == 200) {
        _token = basicAuth;
        return true;
      }
    } catch (e) {
      print('Erro no login: $e');
    }
    return false;
  }

  Future<List<dynamic>> getAvarias() async {
    final token = await getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/avarias/?status=EM_ABERTO'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ?? '',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    } else {
      throw Exception('Failed to load avarias');
    }
  }

  Future<int?> createAvariaReturningId(Map<String, dynamic> data) async {
    final token = await getToken();
    final response = await http.post(
      Uri.parse('$baseUrl/avarias/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ?? '',
      },
      body: jsonEncode(data),
    );

    if (response.statusCode == 201) {
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      return body['id']; // Assuming generic ViewSet returns the object
    }
    return null;
  }

  Future<bool> createAvaria(Map<String, dynamic> data) async {
    final id = await createAvariaReturningId(data);
    return id != null;
  }

  Future<bool> uploadPhoto(int avariaId, File imageFile) async {
    final token = await getToken();
    var uri = Uri.parse('$baseUrl/avarias/$avariaId/upload_foto/');

    var request = http.MultipartRequest('POST', uri);
    request.headers['Authorization'] = token ?? '';

    // 'arquivo' is the field name expected by AvariaFotoSerializer
    request.files
        .add(await http.MultipartFile.fromPath('arquivo', imageFile.path));

    try {
      var response = await request.send();
      return response.statusCode == 201;
    } catch (e) {
      print('Upload error: $e');
      return false;
    }
  }

  // Generic CRUD Helper
  Future<List<dynamic>> getList(String endpoint) async {
    final token = await getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/$endpoint/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ?? '',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    } else {
      throw Exception('Falha ao carregar $endpoint');
    }
  }

  Future<bool> createItem(String endpoint, Map<String, dynamic> data) async {
    final token = await getToken();
    final response = await http.post(
      Uri.parse('$baseUrl/$endpoint/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ?? '',
      },
      body: jsonEncode(data),
    );

    return response.statusCode == 201;
  }
}
