import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import '../../../shared/services/auth_service.dart';
import '../../../shared/widgets/stat_card.dart';
import '../auth/login_page.dart';

/// Page de profil medecin.
/// Affiche le profil + statistiques personnelles + bouton deconnexion.
class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  Map<String, dynamic> _medecin = {};
  bool _isLoading = true;
  int _consultationsCount = 0;
  int _rdvCount = 0;
  int _analysesCount = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      _medecin = await AuthService.getMedecinData();
      try {
        final rdv = await ApiService.getRendezVous();
        _rdvCount = rdv.length;
      } catch (_) {}
      try {
        final analyses = await ApiService.getAnalyses();
        _analysesCount = analyses.length;
      } catch (_) {}
      // Le nombre de consultations depend d'un endpoint dedie ;
      // on l'estime a partir des RDV termines si l'endpoint n'existe pas.
      _consultationsCount = _rdvCount;
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _logout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Deconnexion'),
        content: const Text('Voulez-vous vraiment vous deconnecter ?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Se deconnecter'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await AuthService.logout();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
      (_) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profil')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _buildHeader(),
                    const SizedBox(height: 24),
                    const Text(
                      'Statistiques',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 2,
                      mainAxisSpacing: 12,
                      crossAxisSpacing: 12,
                      childAspectRatio: 1.1,
                      children: [
                        StatCard(
                          title: 'Consultations',
                          value: '$_consultationsCount',
                          icon: Icons.assignment_outlined,
                          color: AppColors.primary,
                        ),
                        StatCard(
                          title: 'RDV total',
                          value: '$_rdvCount',
                          icon: Icons.event_available_rounded,
                          color: AppColors.accent,
                        ),
                        StatCard(
                          title: 'Analyses',
                          value: '$_analysesCount',
                          icon: Icons.science_outlined,
                          color: const Color(0xFFF59E0B),
                        ),
                        StatCard(
                          title: 'Patients actifs',
                          value: '-',
                          icon: Icons.people_alt_outlined,
                          color: AppColors.p3,
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    _buildMenu(),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: _logout,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.danger,
                      ),
                      icon: const Icon(Icons.logout),
                      label: const Text('Se deconnecter'),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildHeader() {
    final prenom = _medecin['prenom']?.toString() ?? '';
    final nom = _medecin['nom']?.toString() ?? '';
    final specialite = _medecin['specialite']?.toString() ?? '';
    final initials = ((prenom.isNotEmpty ? prenom[0] : '?') +
            (nom.isNotEmpty ? nom[0] : '?'))
        .toUpperCase();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            CircleAvatar(
              radius: 36,
              backgroundColor: AppColors.primary,
              child: Text(
                initials,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Dr. $prenom $nom'.trim(),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (specialite.isNotEmpty)
                    Text(
                      specialite,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenu() {
    return Card(
      child: Column(
        children: [
          ListTile(
            leading: const Icon(Icons.lock_outline, color: AppColors.primary),
            title: const Text('Securite & 2FA'),
            subtitle: const Text('Gerer l\'authentification a deux facteurs'),
            trailing: const Icon(Icons.chevron_right,
                color: AppColors.textSecondary),
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Configuration 2FA a venir')),
              );
            },
          ),
          const Divider(height: 1),
          ListTile(
            leading:
                const Icon(Icons.notifications_outlined, color: AppColors.primary),
            title: const Text('Notifications'),
            subtitle: const Text('Preferences d\'alertes'),
            trailing: const Icon(Icons.chevron_right,
                color: AppColors.textSecondary),
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Preferences de notifications')),
              );
            },
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.info_outline, color: AppColors.primary),
            title: const Text('A propos'),
            subtitle: const Text('Sanar Medecin v1.0.0'),
            trailing: const Icon(Icons.chevron_right,
                color: AppColors.textSecondary),
            onTap: () {
              showAboutDialog(
                context: context,
                applicationName: 'Sanar Medecin',
                applicationVersion: '1.0.0',
                applicationLegalese: 'Projet PPE - usage pedagogique',
              );
            },
          ),
        ],
      ),
    );
  }
}
