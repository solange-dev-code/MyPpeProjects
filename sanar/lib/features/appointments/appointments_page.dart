import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/constants/app_colors.dart';
import '../home/home_page.dart';
import 'add_appointment_page.dart';
import '../messages/messages_page.dart';
import '../profile/profile_page.dart';
import '../../shared/services/api_service.dart';

class AppointmentsPage extends StatefulWidget {
  const AppointmentsPage({super.key});

  @override
  State<AppointmentsPage> createState() => _AppointmentsPageState();
}

class _AppointmentsPageState extends State<AppointmentsPage> {
  int _selectedTab = 0;
  List<dynamic> _rdvs = [];
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadRdvs();
  }

  Future<void> _loadRdvs() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });
    try {
      final rdvs = await ApiService.getRendezVous();
      if (mounted) {
        setState(() {
          _rdvs = rdvs;
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

  List<dynamic> get _aVenir {
    final today = DateTime.now();
    return _rdvs.where((r) {
        if (r['statut'] != 'en_attente' && r['statut'] != 'confirme') {
            return false;
        }
        try {
            final dateRdv = DateTime.parse(r['date']);
            return dateRdv.isAfter(today) ||
                   (dateRdv.year == today.year &&
                    dateRdv.month == today.month &&
                    dateRdv.day == today.day);
        } catch (_) {
            return false;
        }
    }).toList();
}

List<dynamic> get _passes {
    final today = DateTime.now();
    return _rdvs.where((r) {
        if (r['statut'] == 'termine' || r['statut'] == 'annule') {
            return true;
        }
        try {
            final dateRdv = DateTime.parse(r['date']);
            return dateRdv.isBefore(today) &&
                   !(dateRdv.year == today.year &&
                     dateRdv.month == today.month &&
                     dateRdv.day == today.day);
        } catch (_) {
            return false;
        }
    }).toList();
}



  Future<void> _annulerRdv(int id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: const Text('Annuler le rendez-vous'),
        content: const Text(
          'Êtes-vous sûr de vouloir annuler ce rendez-vous ?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Non', style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Text('Oui, annuler'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ApiService.annulerRendezVous(id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Rendez-vous annulé'),
              backgroundColor: Colors.green,
            ),
          );
          _loadRdvs(); // Recharge la liste
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Erreur lors de l\'annulation'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

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
          'Rendez-vous',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            decoration: const BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: const Icon(Icons.add, color: AppColors.primary),
              onPressed: () async {
                await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const AddAppointmentPage(),
                  ),
                );
                _loadRdvs(); // Recharge après ajout
              },
            ),
          ),
        ],
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
                  _buildTab(
                    'À venir (${_aVenir.length})',
                    0,
                  ),
                  _buildTab(
                    'Passés (${_passes.length})',
                    1,
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          // Contenu
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error.isNotEmpty
                    ? _buildError()
                    : RefreshIndicator(
                        onRefresh: _loadRdvs,
                        child: SingleChildScrollView(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: _selectedTab == 0
                              ? _buildAVenir()
                              : _buildPasses(),
                        ),
                      ),
          ),
        ],
      ),

      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey,
        currentIndex: 1,
        onTap: (index) {
          if (index == 0) {
            Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const HomePage()),
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
                      color: Colors.black.withOpacity(0.08),
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

  Widget _buildAVenir() {
    if (_aVenir.isEmpty) {
      return _buildEmpty(
        'Aucun rendez-vous à venir',
        'Prenez un rendez-vous en cliquant sur le + ci-dessus',
        Icons.calendar_today_outlined,
      );
    }
    return Column(
      children: [
        ..._aVenir.map((rdv) => Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: _buildRdvCard(rdv, isPast: false),
            )),
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _buildPasses() {
    if (_passes.isEmpty) {
      return _buildEmpty(
        'Aucun rendez-vous passé',
        'Vos rendez-vous terminés apparaîtront ici',
        Icons.history_rounded,
      );
    }
    return Column(
      children: [
        ..._passes.map((rdv) => Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: _buildRdvCard(rdv, isPast: true),
            )),
        const SizedBox(height: 20),
      ],
    );
  }

  // ==================== CARTE RDV ====================

  Widget _buildRdvCard(Map<String, dynamic> rdv, {required bool isPast}) {
    final statut = rdv['statut'] ?? '';
    final statutLabel = _getStatutLabel(statut);
    final statutColor = _getStatutColor(statut);
    final statutBg = _getStatutBg(statut);
    final statutIcon = _getStatutIcon(statut);

    return Container(
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
          // Nom + statut
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  rdv['medecin_nom'] ?? 'Médecin',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Color(0xFF1A1A2E),
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 5,
                ),
                decoration: BoxDecoration(
                  color: statutBg,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(statutIcon, size: 13, color: statutColor),
                    const SizedBox(width: 4),
                    Text(
                      statutLabel,
                      style: TextStyle(
                        color: statutColor,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 4),

          Text(
            rdv['medecin_specialite'] ?? '',
            style: const TextStyle(color: Colors.grey, fontSize: 13),
          ),

          const SizedBox(height: 14),

          _buildInfoRow(
            Icons.calendar_today_outlined,
            _formatDate(rdv['date'] ?? ''),
          ),
          const SizedBox(height: 8),
          _buildInfoRow(
            Icons.access_time_rounded,
            _formatTime(rdv['heure'] ?? ''),
          ),
          const SizedBox(height: 8),
          _buildInfoRow(
            Icons.info_outline,
            rdv['motif'] ?? '—',
          ),

          if (!isPast && statut != 'annule') ...[
            const SizedBox(height: 18),
            const Divider(height: 1, color: Color(0xFFEEF2FF)),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _annulerRdv(rdv['id']),
                    icon: const Icon(Icons.close, size: 16),
                    label: const Text('Annuler'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red,
                      side: const BorderSide(color: Color(0xFFFFE4E4)),
                      backgroundColor: const Color(0xFFFFF5F5),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () async {
                      await Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const AddAppointmentPage(),
                        ),
                      );
                      _loadRdvs();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      'Nouveau RDV',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ],
            ),
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
              onPressed: _loadRdvs,
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
        Icon(icon, size: 16, color: Colors.grey),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 14,
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
      case 'confirme': return 'Confirmé';
      case 'en_attente': return 'En attente';
      case 'annule': return 'Annulé';
      case 'reporte': return 'Reporté';
      case 'termine': return 'Terminé';
      default: return statut;
    }
  }

  Color _getStatutColor(String statut) {
    switch (statut) {
      case 'confirme': return const Color(0xFF16A34A);
      case 'en_attente': return const Color(0xFFD97706);
      case 'annule': return const Color(0xFFDC2626);
      case 'reporte': return const Color(0xFF9333EA);
      default: return Colors.grey;
    }
  }

  Color _getStatutBg(String statut) {
    switch (statut) {
      case 'confirme': return const Color(0xFFDCFCE7);
      case 'en_attente': return const Color(0xFFFEF3C7);
      case 'annule': return const Color(0xFFFEE2E2);
      case 'reporte': return const Color(0xFFF3E8FF);
      default: return const Color(0xFFF1F5F9);
    }
  }

  IconData _getStatutIcon(String statut) {
    switch (statut) {
      case 'confirme': return Icons.check_circle_outline;
      case 'en_attente': return Icons.access_time_rounded;
      case 'annule': return Icons.cancel_outlined;
      case 'reporte': return Icons.update_rounded;
      default: return Icons.history_rounded;
    }
  }
}