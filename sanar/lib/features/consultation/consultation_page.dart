import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/constants/app_colors.dart';
import '../appointments/appointments_page.dart';
import '../home/home_page.dart';
import '../messages/messages_page.dart';
import '../profile/profile_page.dart';
import '../../shared/services/api_service.dart';

class ConsultationPage extends StatefulWidget {
  const ConsultationPage({super.key});

  @override
  State<ConsultationPage> createState() => _ConsultationPageState();
}

class _ConsultationPageState extends State<ConsultationPage> {
  int _selectedTab = 0;
  List<dynamic> _consultations = [];
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadConsultations();
  }

  Future<void> _loadConsultations() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });
    try {
      final data = await ApiService.getConsultations();
      if (mounted) {
        setState(() {
          _consultations = data;
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

  List<dynamic> get _enCours => _consultations
      .where((c) =>
          c['statut'] == 'en_cours' || c['statut'] == 'en_attente')
      .toList();

  List<dynamic> get _terminees => _consultations
      .where((c) =>
          c['statut'] == 'terminee' ||
          c['statut'] == 'annulee' ||
          c['statut'] == 'reportee')
      .toList();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Consultations',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      body: Column(
        children: [
          const SizedBox(height: 20),

          // Onglets
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: const Color(0xFFEEF2FF),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  _buildTab('En cours (${_enCours.length})', 0),
                  _buildTab('Terminées (${_terminees.length})', 1),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error.isNotEmpty
                    ? _buildError()
                    : RefreshIndicator(
                        onRefresh: _loadConsultations,
                        child: SingleChildScrollView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: _selectedTab == 0
                              ? _buildEnCours()
                              : _buildTerminees(),
                        ),
                      ),
          ),
        ],
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

  // ==================== ONGLETS ====================

  Widget _buildTab(String label, int index) {
    final isSelected = _selectedTab == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _selectedTab = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.08),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : [],
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: isSelected ? AppColors.primary : Colors.grey,
            ),
          ),
        ),
      ),
    );
  }

  // ==================== LISTES ====================

  Widget _buildEnCours() {
    if (_enCours.isEmpty) {
      return _buildEmpty(
        'Aucune consultation en cours',
        'Vos consultations planifiées apparaîtront ici',
        Icons.medical_services_outlined,
      );
    }
    return Column(
      children: [
        ..._enCours.map((c) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _buildConsultationCard(c, isTerminee: false),
            )),
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _buildTerminees() {
    if (_terminees.isEmpty) {
      return _buildEmpty(
        'Aucune consultation terminée',
        'Vos consultations passées apparaîtront ici',
        Icons.history_rounded,
      );
    }
    return Column(
      children: [
        ..._terminees.map((c) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _buildConsultationCard(c, isTerminee: true),
            )),
        const SizedBox(height: 20),
      ],
    );
  }

  // ==================== CARTE ====================

  Widget _buildConsultationCard(
    Map<String, dynamic> c, {
    required bool isTerminee,
  }) {
    final statut = c['statut'] ?? '';
    final statutLabel = _getStatutLabel(statut);
    final statutColor = _getStatutColor(statut);
    final statutBg = _getStatutBg(statut);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header médecin + statut
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: const BoxDecoration(
                  color: Color(0xFFEFF6FF),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.person_outline_rounded,
                  color: AppColors.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      c['medecin_nom'] ?? 'Médecin',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                        color: Color(0xFF1A1A2E),
                      ),
                    ),
                    Text(
                      c['medecin_specialite'] ?? '',
                      style: const TextStyle(
                        fontSize: 13,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: statutBg,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  statutLabel,
                  style: TextStyle(
                    color: statutColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 14),
          const Divider(height: 1, color: Color(0xFFEEF2FF)),
          const SizedBox(height: 12),

          // ID consultation
          if (c['consultation_id'] != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: _buildInfoRow(
                Icons.tag_rounded,
                c['consultation_id'],
              ),
            ),

          _buildInfoRow(
            Icons.calendar_today_outlined,
            '${_formatDate(c['date'] ?? '')}  •  ${_formatTime(c['heure'] ?? '')}',
          ),
          const SizedBox(height: 6),
          _buildInfoRow(Icons.note_outlined, c['motif'] ?? '—'),

          if (c['type_consultation'] != null &&
              c['type_consultation'].toString().isNotEmpty) ...[
            const SizedBox(height: 6),
            _buildInfoRow(
              Icons.category_outlined,
              c['type_consultation'],
            ),
          ],

          // Coût
          if (c['cout'] != null && c['cout'] != 0) ...[
            const SizedBox(height: 6),
            _buildInfoRow(
              Icons.payments_outlined,
              '${c['cout']} FCFA',
            ),
          ],

          // Résumé si terminée
          if (isTerminee) ...[
            if (c['diagnostic'] != null &&
                c['diagnostic'].toString().isNotEmpty) ...[
              const SizedBox(height: 14),
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
                    RichText(
                      text: TextSpan(
                        style: const TextStyle(
                          fontSize: 13,
                          color: Color(0xFF4A5568),
                        ),
                        children: [
                          const TextSpan(
                            text: 'Diagnostic: ',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                          TextSpan(text: c['diagnostic'] ?? '—'),
                        ],
                      ),
                    ),
                    if (c['notes'] != null &&
                        c['notes'].toString().isNotEmpty) ...[
                      const SizedBox(height: 6),
                      RichText(
                        text: TextSpan(
                          style: const TextStyle(
                            fontSize: 13,
                            color: Color(0xFF4A5568),
                          ),
                          children: [
                            const TextSpan(
                              text: 'Notes: ',
                              style: TextStyle(fontWeight: FontWeight.w600),
                            ),
                            TextSpan(text: c['notes'] ?? '—'),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ],
      ),
    );
  }

  // ==================== WIDGETS UTILITAIRES ====================

  Widget _buildEmpty(String title, String subtitle, IconData icon) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          children: [
            Icon(icon, size: 64, color: Colors.grey.shade300),
            const SizedBox(height: 16),
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A1A2E),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 13, color: Colors.grey),
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
            Icon(Icons.wifi_off_rounded, size: 64, color: Colors.grey.shade300),
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
              onPressed: _loadConsultations,
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
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

  Widget _buildInfoRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 15, color: Colors.grey),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 13,
              color: Color(0xFF4A5568),
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
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

  String _formatTime(String time) {
    if (time.isEmpty) return '—';
    return time.length >= 5 ? time.substring(0, 5) : time;
  }

  String _getStatutLabel(String statut) {
    switch (statut) {
      case 'en_attente': return 'En attente';
      case 'en_cours': return 'En cours';
      case 'terminee': return 'Terminée';
      case 'reportee': return 'Reportée';
      case 'annulee': return 'Annulée';
      default: return statut;
    }
  }

  Color _getStatutColor(String statut) {
    switch (statut) {
      case 'en_attente': return const Color(0xFFD97706);
      case 'en_cours': return AppColors.primary;
      case 'terminee': return const Color(0xFF16A34A);
      case 'reportee': return const Color(0xFF9333EA);
      case 'annulee': return const Color(0xFFDC2626);
      default: return Colors.grey;
    }
  }

  Color _getStatutBg(String statut) {
    switch (statut) {
      case 'en_attente': return const Color(0xFFFEF3C7);
      case 'en_cours': return const Color(0xFFEFF6FF);
      case 'terminee': return const Color(0xFFDCFCE7);
      case 'reportee': return const Color(0xFFF3E8FF);
      case 'annulee': return const Color(0xFFFEE2E2);
      default: return const Color(0xFFF1F5F9);
    }
  }
}