import 'api_service.dart';

/// Service d'authentification medecin.
/// Encapsule le login + 2FA TOTP.
class AuthService {
  /// Tente un login classique. Retourne une Map contenant:
  /// - require_2fa (bool)
  /// - access (String?) - token si pas de 2FA necessaire
  /// - medecin (Map?) - infos medecin
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    return ApiService.login(email, password);
  }

  /// Verifie un code TOTP 6 chiffres apres login.
  /// En cas de succes, le token JWT est stocke via ApiService.saveToken.
  static Future<Map<String, dynamic>> verify2fa({
    required String email,
    required String password,
    required String totpCode,
  }) async {
    return ApiService.verify2fa(email, password, totpCode);
  }

  /// Verifie si le medecin est deja connecte.
  static Future<bool> isLoggedIn() => ApiService.isLoggedIn();

  /// Deconnexion : efface le token et les donnees medecin.
  static Future<void> logout() async {
    await ApiService.clearToken();
  }

  /// Renvoie les donnees medecin persistees localement.
  static Future<Map<String, dynamic>> getMedecinData() {
    return ApiService.getMedecinData();
  }
}
