import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';

/// Page de validation d'une analyse.
/// Saisie du resultat + flag automatique Normal / Haut / Bas / Critique
/// en fonction des seuils definis sur le TypeAnalyse.
class AnalyseValidatePage extends StatefulWidget {
  final Map<String, dynamic> analyse;

  const AnalyseValidatePage({super.key, required this.analyse});

  @override
  State<AnalyseValidatePage> createState() => _AnalyseValidatePageState();
}

class _AnalyseValidatePageState extends State<AnalyseValidatePage> {
  final _formKey = GlobalKey<FormState>();
  final _resultatController = TextEditingController();
  final _commentaireController = TextEditingController();
  bool _isLoading = false;
  String _computedFlag = 'N';

  @override
  void dispose() {
    _resultatController.dispose();
    _commentaireController.dispose();
    super.dispose();
  }

  Map<String, dynamic> get _typeAnalyse {
    final t = widget.analyse['type_analyse'];
    if (t is Map) return Map<String, dynamic>.from(t);
    return <String, dynamic>{};
  }

  double? get _seuilBas {
    final v = _typeAnalyse['seuil_bas'] ?? _typeAnalyse['min_normal'];
    return (v is num) ? v.toDouble() : double.tryParse(v?.toString() ?? '');
  }

  double? get _seuilHaut {
    final v = _typeAnalyse['seuil_haut'] ?? _typeAnalyse['max_normal'];
    return (v is num) ? v.toDouble() : double.tryParse(v?.toString() ?? '');
  }

  double? get _seuilCritiqueBas {
    final v =
        _typeAnalyse['seuil_critique_bas'] ?? _typeAnalyse['min_critique'];
    return (v is num) ? v.toDouble() : double.tryParse(v?.toString() ?? '');
  }

  double? get _seuilCritiqueHaut {
    final v =
        _typeAnalyse['seuil_critique_haut'] ?? _typeAnalyse['max_critique'];
    return (v is num) ? v.toDouble() : double.tryParse(v?.toString() ?? '');
  }

  void _computeFlag(String value) {
    final v = double.tryParse(value);
    if (v == null) {
      setState(() => _computedFlag = '-');
      return;
    }
    String flag = 'N';
    if (_seuilCritiqueBas != null && v < _seuilCritiqueBas!) {
      flag = 'C';
    } else if (_seuilCritiqueHaut != null && v > _seuilCritiqueHaut!) {
      flag = 'C';
    } else if (_seuilBas != null && v < _seuilBas!) {
      flag = 'L';
    } else if (_seuilHaut != null && v > _seuilHaut!) {
      flag = 'H';
    }
    setState(() => _computedFlag = flag);
  }

  Color _flagColor(String flag) {
    switch (flag) {
      case 'N':
        return AppColors.flagNormal;
      case 'H':
        return AppColors.flagHigh;
      case 'L':
        return AppColors.flagLow;
      case 'C':
        return AppColors.flagCritical;
      default:
        return AppColors.textSecondary;
    }
  }

  String _flagLabel(String flag) {
    switch (flag) {
      case 'N':
        return 'Normal';
      case 'H':
        return 'Haut';
      case 'L':
        return 'Bas';
      case 'C':
        return 'Critique';
      default:
        return 'En attente de saisie';
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final id = widget.analyse['id'];
    if (id == null) return;

    setState(() => _isLoading = true);
    try {
      await ApiService.validerAnalyse(id as int, {
        'resultat': _resultatController.text.trim(),
        'flag': _computedFlag,
        'commentaire': _commentaireController.text.trim(),
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Analyse validee'),
          backgroundColor: AppColors.accent,
        ),
      );
      Navigator.pop(context, true);
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
    final patient = (widget.analyse['patient'] is Map)
        ? Map<String, dynamic>.from(widget.analyse['patient'] as Map)
        : <String, dynamic>{};
    final patientName =
        '${patient['prenom'] ?? ''} ${patient['nom'] ?? ''}'.trim();
    final typeNom = _typeAnalyse['nom']?.toString() ?? 'Analyse';
    final unite = _typeAnalyse['unite']?.toString() ?? '';

    return Scaffold(
      appBar: AppBar(title: const Text('Valider analyse')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        typeNom,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        patientName.isEmpty ? 'Patient' : patientName,
                        style: const TextStyle(color: AppColors.textSecondary),
                      ),
                      const Divider(height: 24),
                      if (_seuilBas != null || _seuilHaut != null)
                        _row('Normales',
                            '${_seuilBas ?? '-'} - ${_seuilHaut ?? '-'} ${unite}'),
                      if (_seuilCritiqueBas != null ||
                          _seuilCritiqueHaut != null)
                        _row('Critiques',
                            '${_seuilCritiqueBas ?? '-'} - ${_seuilCritiqueHaut ?? '-'} ${unite}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _resultatController,
                keyboardType: const TextInputType.numberWithOptions(
                    decimal: true, signed: true),
                decoration: InputDecoration(
                  labelText: 'Resultat${unite.isNotEmpty ? ' ($unite)' : ''}',
                  prefixIcon: const Icon(Icons.input),
                  suffixIcon: Container(
                    margin: const EdgeInsets.all(8),
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: _flagColor(_computedFlag).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Text(
                        _flagLabel(_computedFlag),
                        style: TextStyle(
                          color: _flagColor(_computedFlag),
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                ),
                onChanged: _computeFlag,
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Veuillez saisir un resultat'
                    : null,
              ),
              const SizedBox(height: 8),
              if (_computedFlag == 'C')
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.danger.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.danger.withOpacity(0.4)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.warning, color: AppColors.danger, size: 20),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Valeur critique : alerter immediatement le patient.',
                          style: TextStyle(color: AppColors.danger),
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _commentaireController,
                decoration: const InputDecoration(
                  labelText: 'Commentaire (optionnel)',
                  prefixIcon: Icon(Icons.notes),
                ),
                maxLines: 3,
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
                    : const Text('Valider l\'analyse'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
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
}
