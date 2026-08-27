import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../shared/services/api_service.dart';

/// Écran affichant le QR code médical du patient pour accès d'urgence.
///
/// Le QR code encode l'URL publique /api/urgence/<token>/ qui permet
/// à un secouriste de récupérer les données vitales du patient
/// (groupe sanguin, allergies, médecin référent) sans authentification.
class QrMedicalPage extends StatefulWidget {
  const QrMedicalPage({super.key});

  @override
  State<QrMedicalPage> createState() => _QrMedicalPageState();
}

class _QrMedicalPageState extends State<QrMedicalPage> {
  String _tokenUrgence = '';
  bool _qrActif = true;
  bool _chargement = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _tokenUrgence = prefs.getString('patient_token_urgence') ?? '';
    });
    // Récupère le statut via API
    try {
      final profile = await ApiService.getProfile();
      setState(() {
        _tokenUrgence = profile['token_urgence'] ?? _tokenUrgence;
        _qrActif = profile['urgence_qr_actif'] ?? true;
      });
      await prefs.setString('patient_token_urgence', _tokenUrgence);
    } catch (_) {}
  }

  Future<void> _regenererQr() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Régénérer le QR code'),
        content: const Text(
          'Cette action va révoquer votre ancien QR code et en générer '
          'un nouveau. L\'ancien ne fonctionnera plus. À utiliser en cas '
          'de perte ou de vol de votre carte.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Confirmer'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _chargement = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = await ApiService.getToken();
      // Appel API via dio directement
      final response = await ApiService.dioPost(
        '/urgence/regenerer-qr/',
        {},
      );
      setState(() {
        _tokenUrgence = response['token_urgence'];
        _chargement = false;
      });
      await prefs.setString('patient_token_urgence', _tokenUrgence);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('QR code régénéré avec succès'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      setState(() => _chargement = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _toggleQr() async {
    setState(() => _chargement = true);
    try {
      final response = await ApiService.dioPost('/urgence/toggle-qr/', {});
      setState(() {
        _qrActif = response['urgence_qr_actif'] ?? !_qrActif;
        _chargement = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response['message'] ?? '')),
        );
      }
    } catch (e) {
      setState(() => _chargement = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('QR Code Médical'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            const Icon(Icons.qr_code, size: 60, color: Color(0xFF16A34A)),
            const SizedBox(height: 8),
            const Text(
              'Votre QR Code Médical',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'À imprimer et à porter sur vous. Permet aux secouristes '
              'd\'accéder à vos informations vitales en cas d\'urgence.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 24),

            // QR code visuel (placeholder — utiliser package qr_flutter en prod)
            Container(
              width: 250, height: 250,
              decoration: BoxDecoration(
                color: _qrActif ? Colors.white : Colors.grey.shade200,
                border: Border.all(
                  color: _qrActif ? const Color(0xFF16A34A) : Colors.grey,
                  width: 3,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: _qrActif
                  ? _buildQrPlaceholder()
                  : const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.block, size: 60, color: Colors.grey),
                          SizedBox(height: 8),
                          Text('QR code désactivé', style: TextStyle(color: Colors.grey)),
                        ],
                      ),
                    ),
            ),
            const SizedBox(height: 12),
            Text(
              'Token: ${_tokenUrgence.isNotEmpty ? _tokenUrgence.substring(0, 8) : "Chargement..."}...',
              style: const TextStyle(fontFamily: 'monospace', color: Colors.grey),
            ),
            const SizedBox(height: 24),

            // Boutons d'action
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _chargement ? null : _toggleQr,
                    icon: Icon(_qrActif ? Icons.pause : Icons.play_arrow),
                    label: Text(_qrActif ? 'Désactiver' : 'Activer'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _chargement ? null : _regenererQr,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Régénérer'),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF16A34A),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Infos affichées par le QR code
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Données accessibles par le QR code :',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 8),
                    Text('• Nom, prénom, date de naissance'),
                    Text('• Groupe sanguin'),
                    Text('• Allergies'),
                    Text('• Traitements actifs'),
                    Text('• Médecin référent (nom + téléphone)'),
                    Text('• Hôpital de rattachement'),
                    SizedBox(height: 8),
                    Text(
                      '⚠️ Vos notes médicales, historique complet et '
                      'résultats d\'analyses ne sont PAS exposés.',
                      style: TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Placeholder visuel du QR code.
  /// En production, remplacer par package qr_flutter :
  ///   QrImageView(data: 'https://sanar.app/u/$_tokenUrgence', size: 250)
  Widget _buildQrPlaceholder() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.qr_code_2, size: 180, color: Colors.grey.shade800),
          const SizedBox(height: 8),
          const Text(
            'sanar.app/u/••••',
            style: TextStyle(fontFamily: 'monospace', color: Colors.grey),
          ),
        ],
      ),
    );
  }
}
