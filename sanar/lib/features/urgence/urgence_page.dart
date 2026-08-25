import 'package:flutter/material.dart';
import '../../shared/services/urgence_service.dart';
import '../../core/constants/app_colors.dart';

/// Écran de déclenchement d'urgence (bouton SOS).
///
/// Affiche 3 niveaux d'urgence (P1/P2/P3) et un bouton de déclenchement.
/// Récupère automatiquement la position GPS du patient.
class UrgencePage extends StatefulWidget {
  const UrgencePage({super.key});

  @override
  State<UrgencePage> createState() => _UrgencePageState();
}

class _UrgencePageState extends State<UrgencePage> {
  String _niveauSelectionne = 'P2';
  final _descriptionController = TextEditingController();
  bool _envoiEnCours = false;
  Map<String, dynamic>? _resultat;

  final List<Map<String, dynamic>> _niveaux = [
    {
      'code': 'P1',
      'label': 'Critique',
      'description': 'Arrêt cardiaque, traumatisme grave, inconscience',
      'color': const Color(0xFFDC2626),
      'icon': Icons.warning,
    },
    {
      'code': 'P2',
      'label': 'Urgent',
      'description': 'Douleur aiguë, fracture suspectée, saignement',
      'color': const Color(0xFFD97706),
      'icon': Icons.local_hospital,
    },
    {
      'code': 'P3',
      'label': 'Modéré',
      'description': 'Consultation rapide requise, symptômes inquiétants',
      'color': const Color(0xFF0284C7),
      'icon': Icons.medical_services,
    },
  ];

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _declencherUrgence() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirmer l\'urgence'),
        content: Text(
          'Vous allez déclencher une urgence de niveau $_niveauSelectionne. '
          'L\'hôpital le plus proche sera notifié avec votre position GPS.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('CONFIRMER'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _envoiEnCours = true);
    try {
      final result = await UrgenceService.triggerUrgence(
        niveau: _niveauSelectionne,
        description: _descriptionController.text.trim(),
      );
      setState(() {
        _resultat = result;
        _envoiEnCours = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Urgence envoyée à ${result['hopital_nom'] ?? 'l\'hôpital le plus proche'}',
            ),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      setState(() => _envoiEnCours = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Urgence SOS'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
      ),
      body: _resultat != null ? _buildResultat() : _buildFormulaire(),
    );
  }

  Widget _buildFormulaire() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Sélectionnez le niveau d\'urgence',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Cette alerte sera envoyée à l\'hôpital le plus proche '
            'avec votre position GPS actuelle.',
            style: TextStyle(color: Colors.grey, fontSize: 13),
          ),
          const SizedBox(height: 20),
          ..._niveaux.map((n) => _buildNiveauCard(n)),
          const SizedBox(height: 16),
          TextField(
            controller: _descriptionController,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Description (optionnel)',
              hintText: 'Décrivez vos symptômes...',
              border: OutlineInputBorder(),
            ),
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            height: 60,
            child: FilledButton.icon(
              onPressed: _envoiEnCours ? null : _declencherUrgence,
              icon: _envoiEnCours
                  ? const SizedBox(
                      width: 24, height: 24,
                      child: CircularProgressIndicator(color: Colors.white),
                    )
                  : const Icon(Icons.sos, size: 28),
              label: Text(
                _envoiEnCours ? 'Envoi en cours...' : 'DÉCLENCHER L\'URGENCE',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              style: FilledButton.styleFrom(
                backgroundColor: Colors.red,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNiveauCard(Map<String, dynamic> niveau) {
    final isSelected = _niveauSelectionne == niveau['code'];
    return GestureDetector(
      onTap: () => setState(() => _niveauSelectionne = niveau['code']),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isSelected ? niveau['color'].withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? niveau['color'] : Colors.grey.shade300,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: niveau['color'],
              child: Icon(niveau['icon'], color: Colors.white),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${niveau['code']} — ${niveau['label']}',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: niveau['color'],
                    ),
                  ),
                  Text(
                    niveau['description'],
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
            ),
            if (isSelected)
              Icon(Icons.check_circle, color: niveau['color']),
          ],
        ),
      ),
    );
  }

  Widget _buildResultat() {
    final r = _resultat!;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Center(
            child: Icon(Icons.check_circle, color: Colors.green, size: 80),
          ),
          const SizedBox(height: 16),
          const Center(
            child: Text(
              'Urgence envoyée',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 24),
          _buildInfoRow('Niveau', r['niveau'] ?? ''),
          _buildInfoRow('Hôpital destiné', r['hopital_nom'] ?? 'En cours d\'assignation'),
          _buildInfoRow('Statut', r['statut'] ?? ''),
          _buildInfoRow(
            'Position',
            '${(r['latitude'] as num?)?.toStringAsFixed(4) ?? '?'}, '
            '${(r['longitude'] as num?)?.toStringAsFixed(4) ?? '?'}',
          ),
          if (r['description'] != null && r['description'].isNotEmpty)
            _buildInfoRow('Description', r['description']),
          const Spacer(),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.phone),
                  label: const Text('Appeler l\'hôpital'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Retour'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}
