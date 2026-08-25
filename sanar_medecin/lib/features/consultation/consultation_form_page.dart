import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import 'prescription_form_page.dart';

/// Formulaire de saisie d'une consultation.
/// Champs : diagnostic, notes, code ICD-10, cout, type_consultation.
/// A l'enregistrement, propose d'ajouter une prescription.
class ConsultationFormPage extends StatefulWidget {
  final Map<String, dynamic>? rdv;
  final Map<String, dynamic>? patient;

  const ConsultationFormPage({
    super.key,
    this.rdv,
    this.patient,
  });

  @override
  State<ConsultationFormPage> createState() => _ConsultationFormPageState();
}

class _ConsultationFormPageState extends State<ConsultationFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _diagnosticController = TextEditingController();
  final _notesController = TextEditingController();
  final _icd10Controller = TextEditingController();
  final _coutController = TextEditingController();
  String _typeConsultation = 'CONSULTATION';
  bool _isLoading = false;

  static const _types = [
    'CONSULTATION',
    'TELECONSULTATION',
    'URGENCE',
    'CONTROLE',
    'VISITE_DOMICILE',
  ];

  @override
  void dispose() {
    _diagnosticController.dispose();
    _notesController.dispose();
    _icd10Controller.dispose();
    _coutController.dispose();
    super.dispose();
  }

  Map<String, dynamic> get _patient {
    if (widget.patient != null) return widget.patient!;
    final r = widget.rdv;
    if (r != null && r['patient'] is Map) {
      return Map<String, dynamic>.from(r['patient'] as Map);
    }
    return <String, dynamic>{};
  }

  int? get _patientId {
    final p = _patient;
    return (p['id'] is int)
        ? p['id'] as int
        : int.tryParse(p['id']?.toString() ?? '');
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_patientId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Patient manquant'),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final data = <String, dynamic>{
        'patient': _patientId,
        'diagnostic': _diagnosticController.text.trim(),
        'notes': _notesController.text.trim(),
        'code_icd10': _icd10Controller.text.trim(),
        'cout': double.tryParse(_coutController.text.trim()) ?? 0.0,
        'type_consultation': _typeConsultation,
        if (widget.rdv != null && widget.rdv!['id'] != null)
          'rendez_vous': widget.rdv!['id'],
      };
      final response = await ApiService.createConsultation(data);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Consultation #${response['id'] ?? ''} enregistree'),
          backgroundColor: AppColors.accent,
        ),
      );
      // Proposer l'ajout d'une prescription
      final consultId = response['id'];
      final ajoutPrescription = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Prescription'),
          content: const Text('Souhaitez-vous ajouter une prescription ?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Non, terminer'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Oui, prescrire'),
            ),
          ],
        ),
      );
      if (ajoutPrescription == true && consultId != null) {
        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => PrescriptionFormPage(
              consultationId: (consultId is int)
                  ? consultId
                  : int.tryParse(consultId.toString()) ?? 0,
              patient: _patient,
            ),
          ),
        );
      } else {
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
    final patientName =
        '${_patient['prenom'] ?? ''} ${_patient['nom'] ?? ''}'.trim();
    return Scaffold(
      appBar: AppBar(title: const Text('Nouvelle consultation')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (patientName.isNotEmpty)
                Card(
                  child: ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: AppColors.primary,
                      child: Icon(Icons.person, color: Colors.white),
                    ),
                    title: Text(patientName),
                    subtitle: Text(
                        'ID : ${_patient['patient_id'] ?? _patient['id'] ?? '-'}'),
                  ),
                ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _typeConsultation,
                decoration: const InputDecoration(
                  labelText: 'Type de consultation',
                  prefixIcon: Icon(Icons.category_outlined),
                ),
                items: _types
                    .map((t) => DropdownMenuItem(
                          value: t,
                          child: Text(_typeLabel(t)),
                        ))
                    .toList(),
                onChanged: (v) {
                  if (v != null) setState(() => _typeConsultation = v);
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _diagnosticController,
                decoration: const InputDecoration(
                  labelText: 'Diagnostic',
                  prefixIcon: Icon(Icons.assignment_outlined),
                ),
                maxLines: 2,
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Veuillez saisir un diagnostic'
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _icd10Controller,
                decoration: const InputDecoration(
                  labelText: 'Code ICD-10',
                  hintText: 'ex : J00, E11.9, I10',
                  prefixIcon: Icon(Icons.local_hospital_outlined),
                ),
                textCapitalization: TextCapitalization.characters,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _notesController,
                decoration: const InputDecoration(
                  labelText: 'Notes cliniques',
                  prefixIcon: Icon(Icons.notes),
                ),
                maxLines: 4,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _coutController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Cout (FCFA)',
                  prefixIcon: Icon(Icons.payments_outlined),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2),
                      )
                    : const Text('Enregistrer la consultation'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _typeLabel(String t) {
    switch (t) {
      case 'CONSULTATION':
        return 'Consultation';
      case 'TELECONSULTATION':
        return 'Teleconsultation';
      case 'URGENCE':
        return 'Urgence';
      case 'CONTROLE':
        return 'Controle';
      case 'VISITE_DOMICILE':
        return 'Visite a domicile';
      default:
        return t;
    }
  }
}
