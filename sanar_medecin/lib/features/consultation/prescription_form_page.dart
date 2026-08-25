import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';

/// Formulaire de saisie d'une prescription medicale.
/// Champs : medicament, posologie, duree (jours), instructions optionnelles.
/// Permet d'ajouter plusieurs medicaments a la suite.
class PrescriptionFormPage extends StatefulWidget {
  final int consultationId;
  final Map<String, dynamic>? patient;

  const PrescriptionFormPage({
    super.key,
    required this.consultationId,
    this.patient,
  });

  @override
  State<PrescriptionFormPage> createState() => _PrescriptionFormPageState();
}

class _PrescriptionFormPageState extends State<PrescriptionFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _medicamentController = TextEditingController();
  final _posologieController = TextEditingController();
  final _dureeController = TextEditingController(text: '7');
  final _instructionsController = TextEditingController();
  bool _isLoading = false;
  final List<Map<String, dynamic>> _prescriptions = [];

  @override
  void dispose() {
    _medicamentController.dispose();
    _posologieController.dispose();
    _dureeController.dispose();
    _instructionsController.dispose();
    super.dispose();
  }

  Future<void> _addPrescription() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    try {
      final data = <String, dynamic>{
        'consultation': widget.consultationId,
        'medicament': _medicamentController.text.trim(),
        'posologie': _posologieController.text.trim(),
        'duree_jours': int.tryParse(_dureeController.text.trim()) ?? 7,
        if (_instructionsController.text.trim().isNotEmpty)
          'instructions': _instructionsController.text.trim(),
      };
      await ApiService.createPrescription(data);
      setState(() {
        _prescriptions.add(data);
        _medicamentController.clear();
        _posologieController.clear();
        _instructionsController.clear();
        _dureeController.text = '7';
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Prescription ajoutee'),
            backgroundColor: AppColors.accent,
          ),
        );
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

  void _finish() {
    if (_prescriptions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Aucune prescription ajoutee'),
          backgroundColor: AppColors.danger,
        ),
      );
      return;
    }
    Navigator.pop(context, true);
  }

  @override
  Widget build(BuildContext context) {
    final patient = widget.patient ?? <String, dynamic>{};
    final patientName =
        '${patient['prenom'] ?? ''} ${patient['nom'] ?? ''}'.trim();
    return Scaffold(
      appBar: AppBar(title: const Text('Prescription')),
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
                        'Consultation #${widget.consultationId}'),
                  ),
                ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _medicamentController,
                decoration: const InputDecoration(
                  labelText: 'Medicament',
                  prefixIcon: Icon(Icons.medication_outlined),
                ),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Veuillez saisir un medicament'
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _posologieController,
                decoration: const InputDecoration(
                  labelText: 'Posologie',
                  hintText: 'ex : 1 comprime x 3 fois par jour',
                  prefixIcon: Icon(Icons.schedule),
                ),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Veuillez saisir une posologie'
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _dureeController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Duree (jours)',
                  prefixIcon: Icon(Icons.date_range_outlined),
                ),
                validator: (v) {
                  final n = int.tryParse(v ?? '');
                  if (n == null || n <= 0) {
                    return 'Duree invalide';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _instructionsController,
                decoration: const InputDecoration(
                  labelText: 'Instructions (optionnel)',
                  prefixIcon: Icon(Icons.notes),
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _addPrescription,
                icon: _isLoading
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.add),
                label: const Text('Ajouter la prescription'),
              ),
              const SizedBox(height: 24),
              if (_prescriptions.isNotEmpty) ...[
                const Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    'Prescriptions ajoutees',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                ..._prescriptions.map((p) => Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          backgroundColor: AppColors.accent,
                          child: Icon(Icons.check, color: Colors.white),
                        ),
                        title: Text(p['medicament'].toString()),
                        subtitle: Text(
                          '${p['posologie']} - ${p['duree_jours']} jour(s)',
                        ),
                      ),
                    )),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: _finish,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accent,
                  ),
                  child: const Text('Terminer'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
