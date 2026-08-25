import 'package:flutter/material.dart';
import '../../shared/services/api_service.dart';

/// Écran affichant la position du patient dans la file d'attente de son hôpital.
///
/// Affiche :
/// - Position actuelle (ex: "Vous êtes en position 3")
/// - Temps d'attente estimé
/// - Niveau de triage (P1-P5)
/// - Rafraîchissement automatique toutes les 30 secondes
class FileAttentePage extends StatefulWidget {
  const FileAttentePage({super.key});

  @override
  State<FileAttentePage> createState() => _FileAttentePageState();
}

class _FileAttentePageState extends State<FileAttentePage> {
  Map<String, dynamic>? _fileEntry;
  bool _chargement = true;
  String _erreur = '';

  @override
  void initState() {
    super.initState();
    _loadData();
    // Auto-refresh toutes les 30 secondes
    Future.delayed(const Duration(seconds: 30), _autoRefresh);
  }

  Future<void> _autoRefresh() async {
    if (!mounted) return;
    await _loadData();
    Future.delayed(const Duration(seconds: 30), _autoRefresh);
  }

  Future<void> _loadData() async {
    try {
      final data = await ApiService.dioGet('/file-attente/ma-position/');
      setState(() {
        _fileEntry = data;
        _chargement = false;
        _erreur = '';
      });
    } catch (e) {
      setState(() {
        _chargement = false;
        _erreur = e.toString().contains('404')
            ? 'Vous n\'êtes pas en file d\'attente'
            : 'Erreur: $e';
        _fileEntry = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('File d\'attente'),
        backgroundColor: const Color(0xFF1F6C92),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            onPressed: () {
              setState(() => _chargement = true);
              _loadData();
            },
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _chargement
          ? const Center(child: CircularProgressIndicator())
          : _buildContent(),
    );
  }

  Widget _buildContent() {
    if (_fileEntry == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle, size: 80, color: Colors.green),
            const SizedBox(height: 16),
            Text(
              _erreur,
              style: const TextStyle(fontSize: 16, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.home),
              label: const Text('Retour à l\'accueil'),
            ),
          ],
        ),
      );
    }

    final position = _fileEntry!['position'] ?? '—';
    final tempsEstime = _fileEntry!['temps_attente_estime'] ?? '—';
    final niveau = _fileEntry!['niveau_triage'] ?? 4;
    final motif = _fileEntry!['motif'] ?? '';
    final arrivee = _fileEntry!['arrivee_at'] ?? '';

    final couleurNiveau = {
      1: Colors.red, 2: Colors.orange, 3: Colors.blue,
      4: Colors.grey, 5: Colors.green,
    }[niveau] ?? Colors.grey;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          // Carte principale : position
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [couleurNiveau, couleurNiveau.withOpacity(0.7)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              children: [
                const Text(
                  'Votre position',
                  style: TextStyle(color: Colors.white70, fontSize: 14),
                ),
                const SizedBox(height: 8),
                Text(
                  '#$position',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 64,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'Temps estimé : $tempsEstime min',
                  style: const TextStyle(color: Colors.white, fontSize: 18),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Niveau de triage
          Card(
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: couleurNiveau,
                child: Text(
                  'P$niveau',
                  style: const TextStyle(
                    color: Colors.white, fontWeight: FontWeight.bold),
              ),
              ),
              title: const Text('Niveau de triage'),
              subtitle: Text(_getTriageLabel(niveau)),
            ),
          ),
          const SizedBox(height: 8),

          if (motif.isNotEmpty)
            Card(
              child: ListTile(
                leading: const Icon(Icons.note),
                title: const Text('Motif'),
                subtitle: Text(motif),
              ),
            ),
          const SizedBox(height: 8),

          Card(
            child: ListTile(
              leading: const Icon(Icons.schedule),
              title: const Text('Arrivée'),
              subtitle: Text(arrivee.toString()),
            ),
          ),
          const SizedBox(height: 24),

          // Info
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.info, color: Colors.blue),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Cette page se met à jour automatiquement toutes '
                      'les 30 secondes. Vous recevrez une notification '
                      'quand votre tour approchera.',
                      style: TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getTriageLabel(dynamic niveau) {
    final n = niveau is int ? niveau : int.tryParse(niveau.toString()) ?? 4;
    return {
      1: 'Critique — réanimation immédiate',
      2: 'Urgent — moins de 15 min',
      3: 'Moins urgent — moins de 60 min',
      4: 'Standard — moins de 2 h',
      5: 'Non urgent — moins de 4 h',
    }[n] ?? 'Standard';
  }
}
