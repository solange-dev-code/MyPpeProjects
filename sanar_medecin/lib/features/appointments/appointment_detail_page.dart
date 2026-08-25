import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import '../../../shared/widgets/patient_chip.dart';
import '../consultation/consultation_form_page.dart';
import '../teleconsultation/teleconsultation_page.dart';

/// Page de detail d'un rendez-vous medecin.
/// Affiche les infos du RDV, du patient et permet de demarrer une consultation
/// ou une teleconsultation.
class AppointmentDetailPage extends StatefulWidget {
  final Map<String, dynamic> rdv;

  const AppointmentDetailPage({super.key, required this.rdv});

  @override
  State<AppointmentDetailPage> createState() => _AppointmentDetailPageState();
}

class _AppointmentDetailPageState extends State<AppointmentDetailPage> {
  bool _isLoading = false;

  Map<String, dynamic> get _patient {
    final p = widget.rdv['patient'];
    if (p is Map) return Map<String, dynamic>.from(p);
    return <String, dynamic>{};
  }

  Map<String, dynamic> get _medecin {
    final m = widget.rdv['medecin'];
    if (m is Map) return Map<String, dynamic>.from(m);
    return <String, dynamic>{};
  }

  String get _dateLabel {
    final d = widget.rdv['date'] ?? widget.rdv['date_heure'];
    if (d is String && d.isNotEmpty) {
      try {
        final dt = DateTime.parse(d);
        return DateFormat('EEEE d MMMM y - HH:mm', 'fr_FR').format(dt);
      } catch (_) {}
    }
    return 'Date inconnue';
  }

  Future<void> _annuler() async {
    final id = widget.rdv['id'];
    if (id == null) return;
    setState(() => _isLoading = true);
    try {
      await ApiService.delete('/rendez-vous/$id/');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Rendez-vous annule')),
        );
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: AppColors.danger,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detail RDV')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _buildInfoCard(),
                  const SizedBox(height: 16),
                  _buildPatientCard(),
                  const SizedBox(height: 16),
                  _buildMedecinCard(),
                  const SizedBox(height: 24),
                  _buildActions(),
                ],
              ),
            ),
    );
  }

  Widget _buildInfoCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.event, color: AppColors.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _dateLabel,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            _row('Motif', widget.rdv['motif']?.toString() ?? 'Consultation'),
            _row('Statut', _statutLabel(widget.rdv['statut']?.toString() ?? '')),
            if (widget.rdv['hopital'] != null)
              _row('Hopital', widget.rdv['hopital'].toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildPatientCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Patient',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 12),
            PatientChip(
              nom: _patient['nom']?.toString() ?? '',
              prenom: _patient['prenom']?.toString() ?? '',
              patientId: _patient['patient_id']?.toString() ?? '',
              age: _patient['age']?.toString(),
              groupeSanguin: _patient['groupe_sanguin']?.toString(),
            ),
            const SizedBox(height: 12),
            if (_patient['telephone'] != null)
              _row('Telephone', _patient['telephone'].toString()),
            if (_patient['email'] != null)
              _row('Email', _patient['email'].toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildMedecinCard() {
    final nom =
        'Dr. ${_medecin['prenom'] ?? ''} ${_medecin['nom'] ?? ''}'.trim();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Medecin',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            _row('Nom', nom.isEmpty ? 'Dr.' : nom),
            if (_medecin['specialite'] != null)
              _row('Specialite', _medecin['specialite'].toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildActions() {
    final statut = widget.rdv['statut']?.toString().toUpperCase() ?? '';
    final isAnnule = statut == 'ANNULE' || statut == 'CANCELLED';
    final isTermine = statut == 'TERMINE' || statut == 'DONE';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (!isAnnule && !isTermine) ...[
          ElevatedButton.icon(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) =>
                      ConsultationFormPage(rdv: widget.rdv),
                ),
              );
            },
            icon: const Icon(Icons.edit_note),
            label: const Text('Demarrer la consultation'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const TeleconsultationPage(),
                ),
              );
            },
            icon: const Icon(Icons.videocam_outlined),
            label: const Text('Demarrer la teleconsultation'),
          ),
          const SizedBox(height: 12),
          TextButton.icon(
            onPressed: _annuler,
            icon: const Icon(Icons.cancel_outlined, color: AppColors.danger),
            label: const Text('Annuler le RDV',
                style: TextStyle(color: AppColors.danger)),
          ),
        ] else ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.danger.withOpacity(0.08),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              isAnnule
                  ? 'Ce rendez-vous a ete annule.'
                  : 'Ce rendez-vous est termine.',
              style: const TextStyle(color: AppColors.danger),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ],
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 90,
            child: Text(
              label,
              style: const TextStyle(color: AppColors.textSecondary),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  String _statutLabel(String s) {
    switch (s.toUpperCase()) {
      case 'CONFIRME':
      case 'CONFIRMED':
        return 'Confirme';
      case 'EN_ATTENTE':
      case 'PENDING':
        return 'En attente';
      case 'ANNULE':
      case 'CANCELLED':
        return 'Annule';
      case 'TERMINE':
      case 'DONE':
        return 'Termine';
      default:
        return s.isEmpty ? 'Inconnu' : s;
    }
  }
}
