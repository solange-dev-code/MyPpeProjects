import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import 'patient_detail_page.dart';

/// Page de recherche de patient par nom ou patient_id.
class PatientSearchPage extends StatefulWidget {
  const PatientSearchPage({super.key});

  @override
  State<PatientSearchPage> createState() => _PatientSearchPageState();
}

class _PatientSearchPageState extends State<PatientSearchPage> {
  final _controller = TextEditingController();
  List<dynamic> _results = [];
  bool _isLoading = false;
  bool _hasSearched = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty) return;
    setState(() {
      _isLoading = true;
      _hasSearched = true;
    });
    try {
      _results = await ApiService.searchPatients(query);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur : $e'),
            backgroundColor: AppColors.danger,
          ),
        );
      }
      _results = [];
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recherche patient')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      labelText: 'Nom, patient_id ou telephone',
                      prefixIcon: Icon(Icons.search),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isLoading ? null : _search,
                  child: const Text('OK'),
                ),
              ],
            ),
          ),
          Expanded(child: _buildResults()),
        ],
      ),
    );
  }

  Widget _buildResults() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (!_hasSearched) {
      return const Center(
        child: Text(
          'Saisissez un nom ou un identifiant pour lancer la recherche',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.textSecondary),
        ),
      );
    }
    if (_results.isEmpty) {
      return const Center(
        child: Text(
          'Aucun patient trouve',
          style: TextStyle(color: AppColors.textSecondary),
        ),
      );
    }
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _results.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, i) {
        final p = _results[i] as Map<String, dynamic>;
        final name =
            '${p['prenom'] ?? ''} ${p['nom'] ?? ''}'.trim();
        return Card(
          child: ListTile(
            leading: const CircleAvatar(
              backgroundColor: AppColors.primary,
              child: Icon(Icons.person, color: Colors.white),
            ),
            title: Text(name.isEmpty ? 'Patient' : name),
            subtitle: Text('ID : ${p['patient_id'] ?? p['id'] ?? '-'}'),
            trailing: const Icon(Icons.chevron_right,
                color: AppColors.textSecondary),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => PatientDetailPage(patient: p),
                ),
              );
            },
          ),
        );
      },
    );
  }
}
