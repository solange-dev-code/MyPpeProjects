import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/constants/app_colors.dart';
import '../appointments/appointments_page.dart';
import '../home/home_page.dart';
import '../messages/messages_page.dart';
import '../profile/profile_page.dart';
import '../../shared/services/api_service.dart';

class ResultsPage extends StatefulWidget {
  const ResultsPage({super.key});

  @override
  State<ResultsPage> createState() => _ResultsPageState();
}

class _ResultsPageState extends State<ResultsPage> {
  static const Color purple = Color(0xFF9333EA);

  List<dynamic> _analyses = [];
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadAnalyses();
  }

  Future<void> _loadAnalyses() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });
    try {
      final data = await ApiService.getAnalyses();
      if (mounted) {
        setState(() {
          _analyses = data;
          _isLoading = false;
        });
      }
    } on DioException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.type == DioExceptionType.connectionTimeout
              ? 'Impossible de contacter le serveur'
              : 'Erreur de chargement';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Erreur inattendue';
          _isLoading = false;
        });
      }
    }
  }

  List<dynamic> get _disponibles =>
      _analyses.where((a) => a['statut'] == 'disponible').toList();

  List<dynamic> get _enAttente =>
      _analyses.where((a) => a['statut'] == 'en_attente').toList();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: purple,
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          "Résultats d'analyses",
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadAnalyses,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 8),

                        // Résumé stats
                        Row(
                          children: [
                            _buildStatBadge(
                              '${_disponibles.length}',
                              'Disponibles',
                              const Color(0xFF16A34A),
                              const Color(0xFFDCFCE7),
                            ),
                            const SizedBox(width: 12),
                            _buildStatBadge(
                              '${_enAttente.length}',
                              'En attente',
                              const Color(0xFFD97706),
                              const Color(0xFFFEF3C7),
                            ),
                          ],
                        ),

                        const SizedBox(height: 20),

                        if (_analyses.isEmpty)
                          _buildEmpty()
                        else ...[
                          // Disponibles
                          if (_disponibles.isNotEmpty) ...[
                            const Text(
                              'Résultats disponibles',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1A1A2E),
                              ),
                            ),
                            const SizedBox(height: 12),
                            ..._disponibles.map((a) => Padding(
                                  padding: const EdgeInsets.only(bottom: 16),
                                  child: _buildAnalyseCard(a),
                                )),
                          ],

                          // En attente
                          if (_enAttente.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            const Text(
                              'En attente de résultats',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF1A1A2E),
                              ),
                            ),
                            const SizedBox(height: 12),
                            ..._enAttente.map((a) => Padding(
                                  padding: const EdgeInsets.only(bottom: 16),
                                  child: _buildAnalyseCard(a),
                                )),
                          ],
                        ],

                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),

      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey,
        currentIndex: 0,
        onTap: (index) {
          if (index == 0) {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const HomePage()),
              (route) => false,
            );
          } else if (index == 1) {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const AppointmentsPage()),
              (route) => false,
            );
          } else if (index == 2) {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const MessagesPage()),
              (route) => false,
            );
          } else if (index == 3) {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const ProfilePage()),
              (route) => false,
            );
          }
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_rounded),
            label: 'Accueil',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.calendar_month_outlined),
            label: 'Rendez-vous',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.chat_bubble_outline_rounded),
            label: 'Messages',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline_rounded),
            label: 'Profil',
          ),
        ],
      ),
    );
  }

  // ==================== CARTE ANALYSE ====================

  Widget _buildAnalyseCard(Map<String, dynamic> a) {
    final statut = a['statut'] ?? '';
    final isDisponible = statut == 'disponible';
    final typeDisplay = a['type_display'] ?? a['type_analyse'] ?? 'Analyse';

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: const Color(0xFFF3E8FF),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.science_outlined,
                  color: purple,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      typeDisplay,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                        color: Color(0xFF1A1A2E),
                      ),
                    ),
                    Text(
                      a['laboratoire'] ?? '—',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                    Text(
                      _formatDate(a['date'] ?? ''),
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              // Badge statut
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: isDisponible
                      ? const Color(0xFFDCFCE7)
                      : const Color(0xFFFEF3C7),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isDisponible
                          ? Icons.check_circle_outline
                          : Icons.access_time_rounded,
                      size: 13,
                      color: isDisponible
                          ? const Color(0xFF16A34A)
                          : const Color(0xFFD97706),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isDisponible ? 'Disponible' : 'En attente',
                      style: TextStyle(
                        color: isDisponible
                            ? const Color(0xFF16A34A)
                            : const Color(0xFFD97706),
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),
          const Divider(height: 1, color: Color(0xFFEEF2FF)),
          const SizedBox(height: 14),

          // Résultat si disponible
          if (isDisponible) ...[
            // Conclusion
            if (a['conclusion'] != null &&
                a['conclusion'].toString().isNotEmpty) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFF0FDF4),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFBBF7D0)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    RichText(
                      text: const TextSpan(
                        style: TextStyle(
                          fontSize: 13,
                          color: Color(0xFF4A5568),
                        ),
                        children: [
                          TextSpan(
                            text: 'Conclusion: ',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      a['conclusion'],
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF4A5568),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Résultat détaillé
            if (a['resultat'] != null &&
                a['resultat'].toString().isNotEmpty) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Résultat détaillé',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF4A5568),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      a['resultat'],
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF4A5568),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Boutons
            Row(
              children: [
                if (a['fichier_pdf'] != null) ...[
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        // TODO: ouvrir le PDF
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Téléchargement du PDF...'),
                          ),
                        );
                      },
                      icon: const Icon(Icons.download_outlined, size: 18),
                      label: const Text('Télécharger PDF'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: purple,
                        foregroundColor: Colors.white,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                ],
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _showDetails(context, a),
                    icon: const Icon(Icons.description_outlined, size: 18),
                    label: const Text('Voir détails'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF4A5568),
                      side: const BorderSide(color: Color(0xFFE2E8F0)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ] else ...[
            // En attente
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF9EC),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFFDE68A)),
              ),
              child: const Row(
                children: [
                  Icon(
                    Icons.hourglass_empty_rounded,
                    color: Color(0xFFD97706),
                    size: 20,
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Vos résultats sont en cours de traitement. Vous serez notifié dès qu\'ils sont disponibles.',
                      style: TextStyle(
                        fontSize: 13,
                        color: Color(0xFFD97706),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ==================== WIDGETS UTILITAIRES ====================

  Widget _buildStatBadge(
    String count,
    String label,
    Color color,
    Color bg,
  ) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Text(
              count,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                color: color,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          children: [
            Icon(
              Icons.science_outlined,
              size: 64,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            const Text(
              'Aucun résultat d\'analyse',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A1A2E),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            const Text(
              'Vos résultats d\'analyses apparaîtront ici une fois disponibles',
              style: TextStyle(fontSize: 13, color: Colors.grey),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.wifi_off_rounded,
              size: 64,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 16),
            Text(
              _error,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A1A2E),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadAnalyses,
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: purple,
                foregroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showDetails(BuildContext context, Map<String, dynamic> a) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              a['type_display'] ?? a['type_analyse'] ?? 'Analyse',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A1A2E),
              ),
            ),
            const SizedBox(height: 16),
            _buildDetailRow('Laboratoire', a['laboratoire'] ?? '—'),
            _buildDetailRow('Date', _formatDate(a['date'] ?? '')),
            _buildDetailRow('Statut',
                a['statut'] == 'disponible' ? 'Disponible' : 'En attente'),
            if (a['conclusion'] != null && a['conclusion'].isNotEmpty)
              _buildDetailRow('Conclusion', a['conclusion']),
            if (a['resultat'] != null && a['resultat'].isNotEmpty)
              _buildDetailRow('Résultat', a['resultat']),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: Colors.grey,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 13,
                color: Color(0xFF1A1A2E),
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ==================== HELPERS ====================

  String _formatDate(String date) {
    if (date.isEmpty) return '—';
    try {
      final d = DateTime.parse(date);
      const mois = [
        '', 'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
        'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
      ];
      return '${d.day} ${mois[d.month]} ${d.year}';
    } catch (_) {
      return date;
    }
  }
}