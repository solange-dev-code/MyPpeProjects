import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import 'analyse_validate_page.dart';

/// Page listant les analyses en attente de validation medecinale.
/// Filtres possibles : toutes / urgentes / par patient.
class AnalysesListPage extends StatefulWidget {
  const AnalysesListPage({super.key});

  @override
  State<AnalysesListPage> createState() => _AnalysesListPageState();
}

class _AnalysesListPageState extends State<AnalysesListPage> {
  List<dynamic> _analyses = [];
  bool _isLoading = true;
  String? _errorMessage;
  String _filter = 'EN_ATTENTE';

  static const _filters = [
    {'value': 'EN_ATTENTE', 'label': 'En attente'},
    {'value': 'URGENT', 'label': 'Urgentes'},
    {'value': 'TOUTES', 'label': 'Toutes'},
  ];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final statut = _filter == 'TOUTES' ? null : _filter;
      _analyses = await ApiService.getAnalyses(statut: statut);
    } catch (e) {
      _errorMessage = 'Erreur : $e';
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analyses'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildFilters(),
          Expanded(child: _buildList()),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      color: AppColors.surface,
      child: Row(
        children: _filters.map((f) {
          final selected = _filter == f['value'];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(f['label']!),
              selected: selected,
              onSelected: (_) {
                setState(() => _filter = f['value']!);
                _load();
              },
              selectedColor: AppColors.primary,
              labelStyle: TextStyle(
                color: selected ? Colors.white : AppColors.textPrimary,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildList() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 56, color: AppColors.danger),
            const SizedBox(height: 12),
            Text(_errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _load, child: const Text('Reessayer')),
          ],
        ),
      );
    }
    if (_analyses.isEmpty) {
      return const Center(
        child: Text(
          'Aucune analyse a valider',
          style: TextStyle(color: AppColors.textSecondary),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _analyses.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, i) => _analyseTile(_analyses[i]),
      ),
    );
  }

  Widget _analyseTile(dynamic item) {
    final a = item as Map<String, dynamic>;
    final patient = (a['patient'] is Map)
        ? Map<String, dynamic>.from(a['patient'] as Map)
        : <String, dynamic>{};
    final patientName =
        '${patient['prenom'] ?? ''} ${patient['nom'] ?? ''}'.trim();
    final type = (a['type_analyse'] is Map)
        ? (a['type_analyse'] as Map)['nom']?.toString() ?? 'Analyse'
        : a['type_analyse']?.toString() ?? 'Analyse';
    final dateStr = a['date_demande']?.toString() ?? '';
    final isUrgent = a['urgent'] == true || a['priorite'] == 'URGENT';

    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: (isUrgent ? AppColors.danger : AppColors.primary)
                .withOpacity(0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(
            Icons.science_outlined,
            color: isUrgent ? AppColors.danger : AppColors.primary,
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                type,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
            if (isUrgent)
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.danger,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'URGENT',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(patientName.isEmpty ? 'Patient' : patientName),
            if (dateStr.isNotEmpty)
              Text(
                'Demandee le $dateStr',
                style: const TextStyle(
                    fontSize: 12, color: AppColors.textSecondary),
              ),
          ],
        ),
        trailing: ElevatedButton(
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => AnalyseValidatePage(analyse: a),
              ),
            ).then((validated) {
              if (validated == true) _load();
            });
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.accent,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          ),
          child: const Text('Valider'),
        ),
      ),
    );
  }
}
