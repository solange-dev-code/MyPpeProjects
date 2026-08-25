import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Service pour les urgences médicales (bouton SOS).
///
/// Fonctionnalités :
/// - trigger_urgence : déclenche une alerte auprès de l'hôpital le plus proche
/// - get_mes_urgences : récupère l'historique des urgences du patient
/// - get_acces_dossier_urgence : endpoint PUBLIC pour secouristes
/// - regenerer_qr : révoque et régénère le QR code d'urgence
/// - toggle_qr : active/désactive le QR code
class UrgenceService {
  static const String _baseUrl = 'http://10.0.2.2:8080/api';

  static Dio get _dio => Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
    headers: {'Content-Type': 'application/json'},
  ));

  // ──────────────────────────────────────────────────────────
  // Déclencher une urgence (bouton SOS)
  // ──────────────────────────────────────────────────────────
  /// Déclenche une demande d'urgence.
  ///
  /// [niveau] : 'P1' (critique), 'P2' (urgent), 'P3' (modéré)
  /// [description] : description optionnelle des symptômes
  ///
  /// Récupère automatiquement la position GPS du patient et envoie au backend
  /// qui calcule l'hôpital optimal via Haversine + charge actuelle.
  static Future<Map<String, dynamic>> triggerUrgence({
    required String niveau,
    String description = '',
  }) async {
    // 1. Récupérer la position GPS
    final position = await _getCurrentPosition();

    // 2. Récupérer le token JWT
    final token = await ApiService.getToken();
    if (token == null) {
      throw Exception('Non authentifié');
    }

    // 3. Appel API
    final response = await _dio.post(
      '/urgences/',
      data: {
        'niveau': niveau,
        'latitude': position.latitude,
        'longitude': position.longitude,
        'description': description,
      },
      options: Options(headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      }),
    );

    return response.data;
  }

  // ──────────────────────────────────────────────────────────
  // Mes urgences (historique)
  // ──────────────────────────────────────────────────────────
  static Future<List<dynamic>> getMesUrgences() async {
    final token = await ApiService.getToken();
    if (token == null) throw Exception('Non authentifié');

    final response = await _dio.get(
      '/urgences/mes-urgences/',
      options: Options(headers: {
        'Authorization': 'Bearer $token',
      }),
    );
    return response.data;
  }

  // ──────────────────────────────────────────────────────────
  // Accès PUBLIC d'urgence (secouriste scanne QR code)
  // ──────────────────────────────────────────────────────────
  /// Récupère les données d'urgence d'un patient via son token QR.
  ///
  /// Endpoint PUBLIC — ne nécessite pas d'authentification.
  /// Le token UUID est opaque et non devinable.
  static Future<Map<String, dynamic>> getAccesUrgence(String token) async {
    final response = await _dio.get('/urgence/$token/');
    return response.data;
  }

  // ──────────────────────────────────────────────────────────
  // Régénérer le QR code (révocation)
  // ──────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> regenererQr() async {
    final token = await ApiService.getToken();
    final response = await _dio.post(
      '/urgence/regenerer-qr/',
      options: Options(headers: {
        'Authorization': 'Bearer $token',
      }),
    );
    return response.data;
  }

  // ──────────────────────────────────────────────────────────
  // Activer / désactiver le QR code
  // ──────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> toggleQr() async {
    final token = await ApiService.getToken();
    final response = await _dio.post(
      '/urgence/toggle-qr/',
      options: Options(headers: {
        'Authorization': 'Bearer $token',
      }),
    );
    return response.data;
  }

  // ──────────────────────────────────────────────────────────
  // Helpers
  // ──────────────────────────────────────────────────────────
  static Future<Position> _getCurrentPosition() async {
    // Vérifie permissions
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception('Service de localisation désactivé');
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        throw Exception('Permissions de localisation refusées');
      }
    }
    if (permission == LocationPermission.deniedForever) {
      throw Exception('Permissions de localisation définitivement refusées');
    }

    return await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
      timeLimit: const Duration(seconds: 10),
    );
  }
}
