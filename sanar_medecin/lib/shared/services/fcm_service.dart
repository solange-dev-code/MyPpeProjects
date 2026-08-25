import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'api_service.dart';

/// Service de notifications push (Firebase Cloud Messaging).
/// Enregistre le token FCM aupres du backend et ecoute les messages entrants.
class FcmService {
  static final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  /// Initialise FCM : demande la permission, recupere le token et l'enregistre.
  static Future<void> init() async {
    if (kIsWeb) {
      // Sur web, l'init FCM necessite une config supplementaire.
      return;
    }

    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    if (settings.authorizationStatus != AuthorizationStatus.authorized &&
        settings.authorizationStatus != AuthorizationStatus.provisional) {
      debugPrint('FCM: permission refusee');
      return;
    }

    final token = await _messaging.getToken();
    if (token != null) {
      await _registerToken(token);
    }

    // Ecoute du refresh de token
    _messaging.onTokenRefresh.listen(_registerToken);

    // Messages en premier plan
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Tap sur notification lorsque l'app etait en background
    FirebaseMessaging.onMessageOpenedApp.listen(_handleTap);

    // Tap sur notification lorsque l'app etait termine (cold start)
    final initial = await _messaging.getInitialMessage();
    if (initial != null) {
      _handleTap(initial);
    }
  }

  static Future<void> _registerToken(String token) async {
    try {
      const platform = 'android'; // simplifie ; pourrait etre detecte
      await ApiService.registerDeviceToken(token, platform);
      debugPrint('FCM: token enregistre');
    } catch (e) {
      debugPrint('FCM: erreur enregistrement token: $e');
    }
  }

  static void _handleForegroundMessage(RemoteMessage message) {
    debugPrint('FCM foreground: ${message.notification?.title}');
    // Les pages interessées peuvent ecouter un stream global si besoin.
  }

  static void _handleTap(RemoteMessage message) {
    debugPrint('FCM tap: ${message.data}');
    // Le routing peut etre branche ici selon la categorie de notif.
  }

  /// Desabonne le token avant deconnexion.
  static Future<void> revoke() async {
    final token = await _messaging.getToken();
    if (token != null) {
      try {
        await ApiService.unregisterDeviceToken(token);
        await _messaging.deleteToken();
      } catch (_) {
        // Ignore silencieusement en cas de deconnexion hors ligne.
      }
    }
  }
}
