import 'dart:async';
import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';

/// Page de gestion de la file d'attente medecin.
/// Liste triee P1-P5 avec actions Appeler / Terminer / Abandonner.
/// Auto-refresh toutes les 30 secondes.
class FileAttentePage extends StatefulWidget {
  const FileAttentePage({super.key});

  @override
  State<FileAttentePage> createState() => _FileAttentePageState();
}

class _FileAttentePageState extends State<FileAttentePage> {
  List<dynamic> _items = [];
  bool _isLoading = true;
  String? _errorMessage;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _load();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _load(silent: true));
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);
    try {
      final data = await ApiService.getFileAttente();
      final items = (data['items'] as List?) ?? [];
      // Tri par priorite P1..P5
      items.sort((a, b) {
        final pa = (a as Map)['priorite']?.toString() ?? 'P5';
        final pb = (b as Map)['priorite']?.toString() ?? 'P5';
        return pa.compareTo(pb);
      });
      setState(() {
        _items = items;
        _errorMessage = null;
      });
    } catch (e) {
      if (!silent) {
        setState(() => _errorMessage = 'Erreur : $e');
      }
    } finally {
      if (!silent && mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _action(int id, String kind) async {
    try {
      switch (kind) {
        case 'appeler':
          await ApiService.appelerPatient(id);
          break;
        case 'terminer':
          await ApiService.terminerPatient(id);
          break;
        case 'abandonner':
          await ApiService.abandonnerPatient(id);
          break;
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Action "$kind" effectuee')),
        );
      }
      _load(silent: true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: AppColors.danger,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('File d\'attente'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _load(),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
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
    if (_items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle_outline,
                size: 56, color: AppColors.accent),
            const SizedBox(height: 12),
            const Text(
              'Aucun patient en attente',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: () => _load(),
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _items.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, i) => _row(_items[i] as Map<String, dynamic>, i),
      ),
    );
  }

  Widget _row(Map<String, dynamic> item, int index) {
    final priorite = item['priorite']?.toString() ?? 'P5';
    final color = _prioriteColor(priorite);
    final patient = (item['patient'] is Map)
        ? Map<String, dynamic>.from(item['patient'] as Map)
        : <String, dynamic>{};
    final name =
        '${patient['prenom'] ?? ''} ${patient['nom'] ?? ''}'.trim();
    final motif = item['motif']?.toString() ?? 'Consultation';
    final id = (item['id'] is int) ? item['id'] as int : 0;
    final statut = item['statut']?.toString().toUpperCase() ?? 'EN_ATTENTE';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    priorite,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '#${index + 1}',
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name.isEmpty ? 'Patient' : name,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    motif,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      _statutLabel(statut),
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: color,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            _actionButtons(id, statut),
          ],
        ),
      ),
    );
  }

  Widget _actionButtons(int id, String statut) {
    if (statut == 'EN_CONSULTATION') {
      return Column(
        children: [
          ElevatedButton(
            onPressed: () => _action(id, 'terminer'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.accent,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            ),
            child: const Text('Terminer'),
          ),
          const SizedBox(height: 6),
          TextButton(
            onPressed: () => _action(id, 'abandonner'),
            style: TextButton.styleFrom(
              foregroundColor: AppColors.danger,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            ),
            child: const Text('Abandonner', style: TextStyle(fontSize: 12)),
          ),
        ],
      );
    }
    return ElevatedButton(
      onPressed: () => _action(id, 'appeler'),
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      ),
      child: const Text('Appeler'),
    );
  }

  Color _prioriteColor(String p) {
    switch (p) {
      case 'P1':
        return AppColors.p1;
      case 'P2':
        return AppColors.p2;
      case 'P3':
        return AppColors.p3;
      case 'P4':
        return AppColors.p4;
      case 'P5':
        return AppColors.p5;
      default:
        return AppColors.p4;
    }
  }

  String _statutLabel(String s) {
    switch (s) {
      case 'EN_ATTENTE':
        return 'En attente';
      case 'EN_CONSULTATION':
        return 'En consultation';
      case 'TERMINE':
        return 'Termine';
      case 'ABANDONNE':
        return 'Abandonne';
      default:
        return s;
    }
  }
}
