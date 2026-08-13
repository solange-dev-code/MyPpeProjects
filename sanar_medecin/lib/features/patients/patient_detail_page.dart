import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import '../consultation/consultation_form_page.dart';

/// Page de detail patient - vue condensed.
/// Affiche : identite, allergies, antecedents (ATCD), traitements actifs.
class PatientDetailPage extends StatefulWidget {
  final Map<String, dynamic> patient;

  const PatientDetailPage({super.key, required this.patient});

  @override
  State<PatientDetailPage> createState() => _PatientDetailPageState();
}

class _PatientDetailPageState extends State<PatientDetailPage> {
  Map<String, dynamic> _detail = {};
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _detail = Map<String, dynamic>.from(widget.patient);
    _loadFullDetail();
  }

  Future<void> _loadFullDetail() async {
    final id = widget.patient['id'];
    if (id == null) return;
    setState(() => _isLoading = true);
    try {
      final data = await ApiService.getPatientDetail(id as int);
      setState(() {
        _detail = data;
        _errorMessage = null;
      });
    } catch (e) {
      setState(() => _errorMessage = 'Erreur : $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          '${_detail['prenom'] ?? ''} ${_detail['nom'] ?? ''}'.trim(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadFullDetail,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 56, color: AppColors.danger),
                      const SizedBox(height: 12),
                      Text(_errorMessage!,
                          textAlign: TextAlign.center,
                          style:
                              const TextStyle(color: AppColors.textSecondary)),
                      const SizedBox(height: 16),
                      ElevatedButton(
                          onPressed: _loadFullDetail,
                          child: const Text('Reessayer')),
                    ],
                  ),
                )
              : RefreshIndicator(
              onRefresh: _loadFullDetail,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _buildIdentityCard(),
                    const SizedBox(height: 16),
                    _buildAllergiesCard(),
                    const SizedBox(height: 16),
                    _buildAtcdCard(),
                    const SizedBox(height: 16),
                    _buildTreatmentsCard(),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                ConsultationFormPage(patient: _detail),
                          ),
                        );
                      },
                      icon: const Icon(Icons.edit_note),
                      label: const Text('Nouvelle consultation'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildIdentityCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: AppColors.primary,
                  child: Text(
                    _initials(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${_detail['prenom'] ?? ''} ${_detail['nom'] ?? ''}'
                            .trim(),
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'ID : ${_detail['patient_id'] ?? _detail['id'] ?? '-'}',
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 13),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (_detail['age'] != null)
                  _infoChip('Age', '${_detail['age']} ans'),
                if (_detail['sexe'] != null)
                  _infoChip('Sexe', _detail['sexe'].toString()),
                if (_detail['groupe_sanguin'] != null &&
                    _detail['groupe_sanguin'].toString().isNotEmpty)
                  _infoChip(
                      'Groupe', _detail['groupe_sanguin'].toString(),
                      highlight: true),
                if (_detail['telephone'] != null)
                  _infoChip('Tel', _detail['telephone'].toString()),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoChip(String label, String value, {bool highlight = false}) {
    final color = highlight ? AppColors.danger : AppColors.primary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '$label : ',
            style: TextStyle(
              fontSize: 12,
              color: color.withOpacity(0.8),
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAllergiesCard() {
    final allergies = _detail['allergies']?.toString() ?? '';
    final hasAllergies = allergies.isNotEmpty && allergies.toLowerCase() != 'aucune';
    return _sectionCard(
      title: 'Allergies',
      icon: Icons.warning_amber_rounded,
      color: hasAllergies ? AppColors.danger : AppColors.accent,
      child: Text(
        hasAllergies ? allergies : 'Aucune allergie connue',
        style: TextStyle(
          color: hasAllergies ? AppColors.danger : AppColors.textSecondary,
          fontWeight: hasAllergies ? FontWeight.w600 : FontWeight.normal,
        ),
      ),
    );
  }

  Widget _buildAtcdCard() {
    final atcd = _detail['antecedents']?.toString() ??
        _detail['atcd']?.toString() ??
        '';
    return _sectionCard(
      title: 'Antecedents (ATCD)',
      icon: Icons.history,
      color: AppColors.primary,
      child: Text(
        atcd.isEmpty ? 'Aucun antecedent enregistre' : atcd,
        style: TextStyle(
          color: atcd.isEmpty
              ? AppColors.textSecondary
              : AppColors.textPrimary,
        ),
      ),
    );
  }

  Widget _buildTreatmentsCard() {
    final traitements = _detail['traitements']?.toString() ??
        _detail['traitements_actifs']?.toString() ??
        '';
    return _sectionCard(
      title: 'Traitements actifs',
      icon: Icons.medication,
      color: AppColors.accent,
      child: Text(
        traitements.isEmpty
            ? 'Aucun traitement en cours'
            : traitements,
        style: TextStyle(
          color: traitements.isEmpty
              ? AppColors.textSecondary
              : AppColors.textPrimary,
        ),
      ),
    );
  }

  Widget _sectionCard({
    required String title,
    required IconData icon,
    required Color color,
    required Widget child,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const Divider(height: 20),
            child,
          ],
        ),
      ),
    );
  }

  String _initials() {
    final p = _detail['prenom']?.toString() ?? '';
    final n = _detail['nom']?.toString() ?? '';
    final i1 = p.isNotEmpty ? p[0].toUpperCase() : '?';
    final i2 = n.isNotEmpty ? n[0].toUpperCase() : '?';
    return '$i1$i2';
  }
}
