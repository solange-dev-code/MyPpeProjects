import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // URL selon la plateforme
    static String get baseUrl {
      if (kIsWeb) {
          return 'http://127.0.0.1:8080/api';  // ← 8080
      } else {
          return 'http://10.0.2.2:8080/api';   // ← 8080
      }
  }

  static Dio get _dio => Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
    headers: {'Content-Type': 'application/json'},
  ));

  // ==================== TOKEN ====================

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<void> savePatientData(Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('patient_nom', data['nom'] ?? '');
    await prefs.setString('patient_prenom', data['prenom'] ?? '');
    await prefs.setString('patient_id', data['patient_id'] ?? '');
    await prefs.setString('patient_email', data['email'] ?? '');
    await prefs.setString('patient_telephone', data['telephone'] ?? '');
    await prefs.setString('patient_groupe_sanguin', data['groupe_sanguin'] ?? '');
    await prefs.setString('patient_allergies', data['allergies'] ?? '');
    await prefs.setString('patient_adresse', data['adresse'] ?? '');
    await prefs.setInt('patient_pk', data['id'] ?? 0);
  }

  static Future<Map<String, String>> getPatientData() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'nom': prefs.getString('patient_nom') ?? '',
      'prenom': prefs.getString('patient_prenom') ?? '',
      'patient_id': prefs.getString('patient_id') ?? '',
      'email': prefs.getString('patient_email') ?? '',
      'telephone': prefs.getString('patient_telephone') ?? '',
      'groupe_sanguin': prefs.getString('patient_groupe_sanguin') ?? '',
      'allergies': prefs.getString('patient_allergies') ?? '',
      'adresse': prefs.getString('patient_adresse') ?? '',
    };
  }

  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }

  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  static Future<Options> get _authOptions async {
    final token = await getToken();
    return Options(headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    });
  }

  // ==================== AUTH ====================

  static Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final response = await _dio.post(
      '/auth/login/',
      data: {'username': email, 'password': password},
    );
    await saveToken(response.data['access']);
    if (response.data['patient'] != null) {
      await savePatientData(response.data['patient']);
    }
    return response.data;
  }

  static Future<Map<String, dynamic>> register(
    Map<String, dynamic> data,
  ) async {
    final response = await _dio.post('/auth/register/', data: data);
    return response.data;
  }

  // ==================== PROFIL ====================

  static Future<Map<String, dynamic>> getProfile() async {
    final response = await _dio.get(
      '/patient/profile/',
      options: await _authOptions,
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> updateProfile(
    Map<String, dynamic> data,
  ) async {
    final response = await _dio.put(
      '/patient/profile/',
      data: data,
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== RENDEZ-VOUS ====================

  static Future<List<dynamic>> getRendezVous() async {
    final response = await _dio.get(
      '/rendez-vous/',
      options: await _authOptions,
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> createRendezVous(
    Map<String, dynamic> data,
  ) async {
    final response = await _dio.post(
      '/rendez-vous/',
      data: data,
      options: await _authOptions,
    );
    return response.data;
  }

  static Future<void> annulerRendezVous(int id) async {
    await _dio.delete(
      '/rendez-vous/$id/',
      options: await _authOptions,
    );
  }

  // ==================== CONSULTATIONS ====================

  static Future<List<dynamic>> getConsultations() async {
    final response = await _dio.get(
      '/consultations/',
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== ANALYSES ====================

  static Future<List<dynamic>> getAnalyses() async {
    final response = await _dio.get(
      '/analyses/',
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== DOSSIER MEDICAL ====================

  static Future<Map<String, dynamic>> getDossierMedical() async {
    final response = await _dio.get(
      '/dossier-medical/',
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== FACTURES ====================

  static Future<List<dynamic>> getFactures() async {
    final response = await _dio.get(
      '/factures/',
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== MÉDECINS ====================

  static Future<List<dynamic>> getMedecins() async {
    final response = await _dio.get(
      '/medecins/',
      options: await _authOptions,
    );
    return response.data;
  }


  // ==================== HÔPITAUX ====================

  static Future<List<dynamic>> getHopitaux() async {
    final response = await _dio.get(
      '/hopitaux/',
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== NOTIFICATIONS ====================

  static Future<List<dynamic>> getNotifications() async {
    final response = await _dio.get(
      '/notifications/',
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== MESSAGES ====================

  static Future<List<dynamic>> getConversations() async {
    final response = await _dio.get(
      '/conversations/',
      options: await _authOptions,
    );
    return response.data;
  }

  static Future<List<dynamic>> getMessages(int convId) async {
    final response = await _dio.get(
      '/conversations/$convId/messages/',
      options: await _authOptions,
    );
    return response.data;
  }

  static Future<Map<String, dynamic>> sendMessage(
    int convId,
    String contenu,
  ) async {
    final response = await _dio.post(
      '/conversations/$convId/messages/',
      data: {'contenu': contenu},
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== NOUVEAU : Helpers génériques ====================

  /// GET générique pour les nouveaux endpoints (urgences, file_attente, etc.)
  static Future<Map<String, dynamic>> dioGet(String path) async {
    final response = await _dio.get(path, options: await _authOptions);
    return response.data;
  }

  /// POST générique pour les nouveaux endpoints
  static Future<Map<String, dynamic>> dioPost(
    String path,
    Map<String, dynamic> data,
  ) async {
    final response = await _dio.post(path, data: data, options: await _authOptions);
    return response.data;
  }

  // ==================== URGENCES ====================

  static Future<Map<String, dynamic>> triggerUrgence({
    required String niveau,
    required double latitude,
    required double longitude,
    String description = '',
  }) async {
    final response = await _dio.post(
      '/urgences/',
      data: {
        'niveau': niveau,
        'latitude': latitude,
        'longitude': longitude,
        'description': description,
      },
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== FILE D'ATTENTE ====================

  static Future<Map<String, dynamic>> getFileAttentePosition() async {
    return dioGet('/file-attente/ma-position/');
  }

  // ==================== CRÉNEAUX MÉDECIN ====================

  static Future<List<dynamic>> getCreneauxMedecin(
    int medecinId,
    String date,
  ) async {
    final response = await _dio.get(
      '/medecins/$medecinId/creneaux/',
      queryParameters: {'date': date},
      options: await _authOptions,
    );
    return response.data;
  }

  // ==================== EXPORTS ====================

  static Future<String> exportDossierPdf() async {
    final response = await _dio.get(
      '/exports/dossier-pdf/',
      options: (await _authOptions).copyWith(
        responseType: ResponseType.bytes,
      ),
    );
    // Pour téléchargement : utiliser un fichier ou Platform channel
    return response.data.toString();
  }

  // ==================== DEVICE TOKEN (FCM) ====================

  static Future<void> registerDeviceToken(
    String token,
    String platform,
  ) async {
    await _dio.post(
      '/device-token/',
      data: {'token': token, 'platform': platform},
      options: await _authOptions,
    );
  }

  static Future<void> unregisterDeviceToken(String token) async {
    await _dio.delete(
      '/device-token/$token/',
      options: await _authOptions,
    );
  }
}