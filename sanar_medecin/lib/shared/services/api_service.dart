import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Service API central pour l'application medecin.
/// Dio + JWT + helpers get/post/put/delete.
class ApiService {
  // URL selon la plateforme (emulateur Android vs web)
  static String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8080/api';
    } else {
      return 'http://10.0.2.2:8080/api';
    }
  }

  static Dio? _dioInstance;

  static Dio get dio {
    _dioInstance ??= Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Content-Type': 'application/json'},
    ));
    return _dioInstance!;
  }

  // ==================== TOKEN ====================

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('medecin_access_token', token);
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('medecin_access_token');
  }

  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('medecin_access_token');
    await prefs.remove('medecin_data');
  }

  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<Options> get _authOptions async {
    final token = await getToken();
    return Options(headers: {
      if (token != null) 'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    });
  }

  // ==================== DONNEES MEDECIN ====================

  static Future<void> saveMedecinData(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('medecin_data', _encode(data));
  }

  static Future<Map<String, dynamic>> getMedecinData() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('medecin_data');
    if (raw == null || raw.isEmpty) return {};
    return _decode(raw);
  }

  static String _encode(Map<String, dynamic> data) {
    // Encodage minimal : on stocke une string brute separee par "|"
    final nom = data['nom'] ?? '';
    final prenom = data['prenom'] ?? '';
    final id = data['id'] ?? 0;
    final specialite = data['specialite'] ?? '';
    return '$id|$nom|$prenom|$specialite';
  }

  static Map<String, dynamic> _decode(String raw) {
    final parts = raw.split('|');
    return {
      'id': int.tryParse(parts.isNotEmpty ? parts[0] : '0') ?? 0,
      'nom': parts.length > 1 ? parts[1] : '',
      'prenom': parts.length > 2 ? parts[2] : '',
      'specialite': parts.length > 3 ? parts[3] : '',
    };
  }

  // ==================== HELPERS GENERIQUES ====================

  /// GET generique renvoyant une liste.
  static Future<List<dynamic>> getList(String path,
      {Map<String, dynamic>? query}) async {
    final response = await dio.get(
      path,
      queryParameters: query,
      options: await _authOptions,
    );
    return response.data is List ? response.data : (response.data['results'] ?? []);
  }

  /// GET generique renvoyant une Map.
  static Future<Map<String, dynamic>> get(String path,
      {Map<String, dynamic>? query}) async {
    final response = await dio.get(
      path,
      queryParameters: query,
      options: await _authOptions,
    );
    return Map<String, dynamic>.from(response.data);
  }

  /// POST generique.
  static Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> data,
  ) async {
    final response = await dio.post(
      path,
      data: data,
      options: await _authOptions,
    );
    return Map<String, dynamic>.from(response.data);
  }

  /// PUT generique.
  static Future<Map<String, dynamic>> put(
    String path,
    Map<String, dynamic> data,
  ) async {
    final response = await dio.put(
      path,
      data: data,
      options: await _authOptions,
    );
    return Map<String, dynamic>.from(response.data);
  }

  /// DELETE generique.
  static Future<void> delete(String path) async {
    await dio.delete(path, options: await _authOptions);
  }

  // ==================== AUTH ====================

  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final response = await dio.post(
      '/auth/login/',
      data: {'username': email, 'password': password},
    );
    final data = Map<String, dynamic>.from(response.data);
    // Si la reponse contient un token d'acces direct on le stocke,
    // sinon on attend la verification 2FA.
    if (data['access'] != null && data['require_2fa'] != true) {
      await saveToken(data['access'] as String);
    }
    if (data['medecin'] != null) {
      await saveMedecinData(Map<String, dynamic>.from(data['medecin']));
    }
    return data;
  }

  static Future<Map<String, dynamic>> verify2fa(
    String email,
    String password,
    String totpCode,
  ) async {
    final response = await dio.post(
      '/2fa/verify/',
      data: {
        'username': email,
        'password': password,
        'otp_code': totpCode,
      },
    );
    final data = Map<String, dynamic>.from(response.data);
    if (data['access'] != null) {
      await saveToken(data['access'] as String);
    }
    if (data['medecin'] != null) {
      await saveMedecinData(Map<String, dynamic>.from(data['medecin']));
    }
    return data;
  }

  // ==================== RENDEZ-VOUS ====================

  static Future<List<dynamic>> getRendezVous({String? date}) async {
    return getList('/rendez-vous/', query: date != null ? {'date': date} : null);
  }

  static Future<Map<String, dynamic>> getRendezVousDetail(int id) async {
    return get('/rendez-vous/$id/');
  }

  // ==================== FILE D'ATTENTE ====================

  static Future<Map<String, dynamic>> getFileAttente() async {
    return get('/file-attente/ma-position/');
  }

  static Future<Map<String, dynamic>> appelerPatient(int fileAttenteId) async {
    return post('/file-attente/$fileAttenteId/appeler/', {});
  }

  static Future<Map<String, dynamic>> terminerPatient(int fileAttenteId) async {
    return post('/file-attente/$fileAttenteId/terminer/', {});
  }

  static Future<Map<String, dynamic>> abandonnerPatient(int fileAttenteId) async {
    return post('/file-attente/$fileAttenteId/abandonner/', {});
  }

  // ==================== PATIENTS ====================

  static Future<List<dynamic>> searchPatients(String query) async {
    return getList('/patient/profile/', query: {'search': query});
  }

  static Future<Map<String, dynamic>> getPatientDetail(int patientId) async {
    return get('/patient/profile/$patientId/');
  }

  // ==================== CONSULTATIONS ====================

  static Future<Map<String, dynamic>> createConsultation(
    Map<String, dynamic> data,
  ) async {
    return post('/consultations/', data);
  }

  static Future<Map<String, dynamic>> createPrescription(
    Map<String, dynamic> data,
  ) async {
    return post('/prescriptions/', data);
  }

  // ==================== ANALYSES ====================

  static Future<List<dynamic>> getAnalyses({String? statut}) async {
    return getList('/analyses/',
        query: statut != null ? {'statut': statut} : null);
  }

  static Future<Map<String, dynamic>> validerAnalyse(
    int analyseId,
    Map<String, dynamic> data,
  ) async {
    return post('/analyses/$analyseId/valider/', data);
  }

  // ==================== CRENEAUX MEDECIN ====================

  static Future<List<dynamic>> getCreneauxMedecin(
    int medecinId,
    String date,
  ) async {
    return getList('/medecins/$medecinId/creneaux/', query: {'date': date});
  }

  // ==================== DEVICE TOKEN (FCM) ====================

  static Future<void> registerDeviceToken(
    String token,
    String platform,
  ) async {
    await post('/device-token/', {'token': token, 'platform': platform});
  }

  static Future<void> unregisterDeviceToken(String token) async {
    await delete('/device-token/$token/');
  }
}
