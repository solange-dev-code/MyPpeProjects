import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../appointments/appointments_page.dart';
import '../auth/login_page.dart';
import '../home/home_page.dart';
import '../messages/messages_page.dart';
import '../../shared/services/api_service.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  Map<String, dynamic> _patient = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      // D'abord depuis SharedPreferences (rapide)
      final localData = await ApiService.getPatientData();
      if (mounted) {
        setState(() {
          _patient = localData;
          _isLoading = false;
        });
      }
      // Ensuite depuis l'API (données fraîches)
      try {
        final apiData = await ApiService.getProfile();
        await ApiService.savePatientData(apiData);
        if (mounted) {
          setState(() {
            _patient = apiData;
          });
        }
      } catch (_) {}
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String get _nomComplet {
    final prenom = _patient['prenom'] ?? '';
    final nom = _patient['nom'] ?? '';
    return '$prenom $nom'.trim().isEmpty ? '—' : '$prenom $nom'.trim();
  }

  String get _patientId => _patient['patient_id'] ?? '—';
  String get _email => _patient['email'] ?? '—';
  String get _telephone => _patient['telephone'] ?? '—';
  String get _adresse => _patient['adresse'] ?? '—';
  String get _groupeSanguin => _patient['groupe_sanguin'] ?? '—';
  String get _allergies => _patient['allergies'] ?? '—';

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
          'Mon profil',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 8),

                  // Carte profil
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(24),
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
                      children: [
                        // Avatar avec initiales
                        Container(
                          width: 90,
                          height: 90,
                          decoration: const BoxDecoration(
                            color: AppColors.primary,
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              _getInitiales(),
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 32,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          _nomComplet,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1A1A2E),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Patient ID: #$_patientId',
                          style: const TextStyle(
                            fontSize: 13,
                            color: Colors.grey,
                          ),
                        ),
                        const SizedBox(height: 12),
                        // Badge groupe sanguin
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 14,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFFEFF6FF),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.water_drop_outlined,
                                size: 16,
                                color: AppColors.primary,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Groupe $_groupeSanguin',
                                style: const TextStyle(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Informations personnelles
                  const Text(
                    'Informations personnelles',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1A1A2E),
                    ),
                  ),

                  const SizedBox(height: 12),

                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        _buildInfoTile(
                          icon: Icons.person_outline_rounded,
                          label: 'Nom complet',
                          value: _nomComplet,
                          isFirst: true,
                        ),
                        const Divider(height: 1, indent: 56),
                        _buildInfoTile(
                          icon: Icons.mail_outline_rounded,
                          label: 'Email',
                          value: _email,
                        ),
                        const Divider(height: 1, indent: 56),
                        _buildInfoTile(
                          icon: Icons.phone_outlined,
                          label: 'Téléphone',
                          value: _telephone,
                        ),
                        const Divider(height: 1, indent: 56),
                        _buildInfoTile(
                          icon: Icons.location_on_outlined,
                          label: 'Adresse',
                          value: _adresse,
                        ),
                        const Divider(height: 1, indent: 56),
                        _buildInfoTile(
                          icon: Icons.medical_information_outlined,
                          label: 'Allergies',
                          value: _allergies.isEmpty ? 'Aucune' : _allergies,
                          isLast: true,
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Paramètres
                  const Text(
                    'Paramètres',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1A1A2E),
                    ),
                  ),

                  const SizedBox(height: 12),

                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        _buildSettingTile(
                          icon: Icons.notifications_outlined,
                          label: 'Notifications',
                          isFirst: true,
                          onTap: () {},
                        ),
                        const Divider(height: 1, indent: 56),
                        _buildSettingTile(
                          icon: Icons.lock_outline_rounded,
                          label: 'Sécurité et confidentialité',
                          onTap: () {},
                        ),
                        const Divider(height: 1, indent: 56),
                        _buildSettingTile(
                          icon: Icons.help_outline_rounded,
                          label: 'Aide et support',
                          isLast: true,
                          onTap: () {},
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Bouton déconnexion
                  Container(
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: TextButton(
                      onPressed: () => _showLogoutDialog(context),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.logout_rounded, color: Colors.red, size: 20),
                          SizedBox(width: 8),
                          Text(
                            'Se déconnecter',
                            style: TextStyle(
                              color: Colors.red,
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  const Center(
                    child: Column(
                      children: [
                        Text(
                          'Version 1.0.0',
                          style: TextStyle(fontSize: 13, color: Colors.grey),
                        ),
                        SizedBox(height: 4),
                        Text(
                          '© 2026 Sanar. Tous droits réservés.',
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),
                ],
              ),
            ),

      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey,
        currentIndex: 3,
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

  // ==================== HELPERS ====================

  String _getInitiales() {
    final prenom = (_patient['prenom'] ?? '').toString();
    final nom = (_patient['nom'] ?? '').toString();
    final p = prenom.isNotEmpty ? prenom[0].toUpperCase() : '';
    final n = nom.isNotEmpty ? nom[0].toUpperCase() : '';
    return '$p$n'.isEmpty ? '?' : '$p$n';
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        title: const Text(
          'Se déconnecter',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        content: const Text(
          'Êtes-vous sûr de vouloir vous déconnecter ?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text(
              'Annuler',
              style: TextStyle(color: Colors.grey),
            ),
          ),
          ElevatedButton(
            onPressed: () async {
              await ApiService.clearToken();
              if (context.mounted) {
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(builder: (_) => const LoginPage()),
                  (route) => false,
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Text('Se déconnecter'),
          ),
        ],
      ),
    );
  }

  // ==================== WIDGETS ====================

  Widget _buildInfoTile({
    required IconData icon,
    required String label,
    required String value,
    bool isFirst = false,
    bool isLast = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, size: 20, color: Colors.grey),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontSize: 13, color: Colors.grey),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 15,
                    color: Color(0xFF1A1A2E),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          const Icon(
            Icons.arrow_forward_ios_rounded,
            size: 14,
            color: Colors.grey,
          ),
        ],
      ),
    );
  }

  Widget _buildSettingTile({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool isFirst = false,
    bool isLast = false,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.vertical(
        top: isFirst ? const Radius.circular(16) : Radius.zero,
        bottom: isLast ? const Radius.circular(16) : Radius.zero,
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: Row(
          children: [
            Icon(icon, size: 20, color: Colors.grey),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 15,
                  color: Color(0xFF1A1A2E),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            const Icon(
              Icons.arrow_forward_ios_rounded,
              size: 14,
              color: Colors.grey,
            ),
          ],
        ),
      ),
    );
  }
}