import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import '../../../shared/services/auth_service.dart';
import '../../../shared/widgets/stat_card.dart';
import '../analyses/analyses_list_page.dart';
import '../appointments/appointments_page.dart';
import '../file_attente/file_attente_page.dart';
import '../profile/profile_page.dart';

/// Dashboard principal du medecin.
/// Affiche les KPIs (RDV jour, file attente, urgences, analyses a valider),
/// l'agenda du jour (scrollable horizontal) et la file d'attente (liste P1-P5).
/// Bottom nav : Accueil, RDV, File, Analyses, Profil.
class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  Map<String, dynamic> _medecin = {};
  List<dynamic> _rendezVous = [];
  List<dynamic> _fileAttente = [];
  int _analysesCount = 0;
  bool _isLoading = true;
  String? _errorMessage;
  Timer? _refreshTimer;
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _loadData();
    // Auto-refresh toutes les 30 secondes pour la file d'attente
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (_currentIndex == 0) _loadFileAttente();
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      _medecin = await AuthService.getMedecinData();
      final rdv = await ApiService.getRendezVous(
        date: DateFormat('yyyy-MM-dd').format(DateTime.now()),
      );
      _rendezVous = rdv;

      try {
        final fileData = await ApiService.getFileAttente();
        _fileAttente = (fileData['items'] as List?) ?? [];
      } catch (_) {
        _fileAttente = [];
      }

      try {
        final analyses = await ApiService.getAnalyses(statut: 'EN_ATTENTE');
        _analysesCount = analyses.length;
      } catch (_) {
        _analysesCount = 0;
      }
    } catch (e) {
      _errorMessage = 'Erreur de chargement : $e';
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadFileAttente() async {
    try {
      final fileData = await ApiService.getFileAttente();
      setState(() {
        _fileAttente = (fileData['items'] as List?) ?? [];
      });
    } catch (_) {
      // Silencieux : on garde les donnees existantes
    }
  }

  String get _medecinFullName {
    final prenom = _medecin['prenom'] ?? '';
    final nom = _medecin['nom'] ?? '';
    if (prenom.isEmpty && nom.isEmpty) return 'Medecin';
    return 'Dr. $prenom $nom';
  }

  int get _rdvJourCount => _rendezVous.length;
  int get _fileAttenteCount => _fileAttente.length;
  int get _urgencesCount =>
      _fileAttente.where((e) => (e['priorite'] ?? 'P5') == 'P1').length;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: _buildBody(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (i) {
          setState(() => _currentIndex = i);
          if (i != 0) _navigateTo(i);
        },
        items: const [
          BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined), label: 'Accueil'),
          BottomNavigationBarItem(
              icon: Icon(Icons.event_outlined), label: 'RDV'),
          BottomNavigationBarItem(
              icon: Icon(Icons.list_alt_outlined), label: 'File'),
          BottomNavigationBarItem(
              icon: Icon(Icons.science_outlined), label: 'Analyses'),
          BottomNavigationBarItem(
              icon: Icon(Icons.person_outline), label: 'Profil'),
        ],
      ),
    );
  }

  void _navigateTo(int index) {
    Widget? page;
    switch (index) {
      case 1:
        page = const AppointmentsPage();
        break;
      case 2:
        page = const FileAttentePage();
        break;
      case 3:
        page = const AnalysesListPage();
        break;
      case 4:
        page = const ProfilePage();
        break;
    }
    if (page != null) {
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => page!),
      ).then((_) {
        setState(() => _currentIndex = 0);
        _loadData();
      });
    }
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline,
                size: 56, color: AppColors.danger),
            const SizedBox(height: 12),
            Text(_errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: const Text('Reessayer'),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _loadData,
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(child: _buildHeader()),
          SliverToBoxAdapter(child: _buildKpiGrid()),
          SliverToBoxAdapter(child: _buildAgendaSection()),
          SliverToBoxAdapter(child: _buildFileAttenteSection()),
          const SliverToBoxAdapter(child: SizedBox(height: 32)),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
      decoration: const BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(24),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _medecinFullName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    if (_medecin['specialite'] != null)
                      Text(
                        _medecin['specialite'].toString(),
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.85),
                          fontSize: 13,
                        ),
                      ),
                    const SizedBox(height: 4),
                    Text(
                      DateFormat('EEEE d MMMM y', 'fr_FR')
                          .format(DateTime.now()),
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.85),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.notifications_outlined,
                    color: Colors.white),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Aucune nouvelle notification')),
                  );
                },
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildKpiGrid() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Vue d\'ensemble',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 12),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.0,
            children: [
              StatCard(
                title: 'RDV jour',
                value: '$_rdvJourCount',
                icon: Icons.event_available_rounded,
                color: AppColors.primary,
                onTap: () => _navigateTo(1),
              ),
              StatCard(
                title: 'File d\'attente',
                value: '$_fileAttenteCount',
                icon: Icons.people_alt_outlined,
                color: AppColors.accent,
                onTap: () => _navigateTo(2),
              ),
              StatCard(
                title: 'Urgences (P1)',
                value: '$_urgencesCount',
                icon: Icons.warning_amber_rounded,
                color: AppColors.danger,
                onTap: () => _navigateTo(2),
              ),
              StatCard(
                title: 'Analyses a valider',
                value: '$_analysesCount',
                icon: Icons.science_outlined,
                color: const Color(0xFFF59E0B),
                onTap: () => _navigateTo(3),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAgendaSection() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Agenda du jour',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              TextButton(
                onPressed: () => _navigateTo(1),
                child: const Text('Tout voir'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 130,
            child: _rendezVous.isEmpty
                ? _emptyAgenda()
                : ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: _rendezVous.length,
                    itemBuilder: (context, i) => _agendaCard(_rendezVous[i]),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _emptyAgenda() {
    return Container(
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: const Text(
        'Aucun rendez-vous aujourd\'hui',
        style: TextStyle(color: AppColors.textSecondary),
      ),
    );
  }

  Widget _agendaCard(dynamic rdv) {
    final r = rdv as Map<String, dynamic>;
    final dateStr = r['date'] ?? r['date_heure'] ?? '';
    String heure = '--:--';
    try {
      if (dateStr is String && dateStr.length >= 16) {
        final dt = DateTime.parse(dateStr);
        heure = DateFormat('HH:mm').format(dt);
      }
    } catch (_) {}
    final patient = (r['patient'] is Map)
        ? r['patient'] as Map<String, dynamic>
        : <String, dynamic>{};
    final patientName =
        '${patient['prenom'] ?? ''} ${patient['nom'] ?? ''}'.trim();
    final motif = r['motif'] ?? r['raison'] ?? 'Consultation';
    final statut = r['statut'] ?? 'CONFIRME';
    final color = _statusColor(statut.toString());

    return Container(
      width: 220,
      margin: const EdgeInsets.only(right: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border(
          left: BorderSide(color: color, width: 4),
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.textPrimary.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            heure,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            patientName.isEmpty ? 'Patient' : patientName,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 2),
          Text(
            motif.toString(),
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              _statutLabel(statut.toString()),
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFileAttenteSection() {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'File d\'attente',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              TextButton(
                onPressed: () => _navigateTo(2),
                child: const Text('Gerer'),
              ),
            ],
          ),
          const SizedBox(height: 4),
          if (_fileAttente.isEmpty)
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.border),
              ),
              child: const Center(
                child: Text(
                  'File d\'attente vide',
                  style: TextStyle(color: AppColors.textSecondary),
                ),
              ),
            )
          else
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _fileAttente.length,
              itemBuilder: (context, i) => _fileAttenteRow(_fileAttente[i]),
            ),
        ],
      ),
    );
  }

  Widget _fileAttenteRow(dynamic item) {
    final fa = item as Map<String, dynamic>;
    final priorite = fa['priorite'] ?? 'P5';
    final patient = (fa['patient'] is Map)
        ? fa['patient'] as Map<String, dynamic>
        : <String, dynamic>{};
    final patientName =
        '${patient['prenom'] ?? ''} ${patient['nom'] ?? ''}'.trim();
    final color = _prioriteColor(priorite.toString());

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color,
          child: Text(
            priorite.toString(),
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        title: Text(patientName.isEmpty ? 'Patient' : patientName),
        subtitle: Text(fa['motif']?.toString() ?? 'Consultation'),
        trailing: ElevatedButton(
          onPressed: () => _navigateTo(2),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          ),
          child: const Text('Appeler'),
        ),
      ),
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

  Color _statusColor(String s) {
    switch (s.toUpperCase()) {
      case 'CONFIRME':
      case 'CONFIRMED':
        return AppColors.statusConfirmed;
      case 'EN_ATTENTE':
      case 'PENDING':
        return AppColors.statusPending;
      case 'ANNULE':
      case 'CANCELLED':
        return AppColors.statusCancelled;
      case 'TERMINE':
      case 'DONE':
        return AppColors.statusDone;
      default:
        return AppColors.statusPending;
    }
  }

  String _statutLabel(String s) {
    switch (s.toUpperCase()) {
      case 'CONFIRME':
      case 'CONFIRMED':
        return 'Confirme';
      case 'EN_ATTENTE':
      case 'PENDING':
        return 'En attente';
      case 'ANNULE':
      case 'CANCELLED':
        return 'Annule';
      case 'TERMINE':
      case 'DONE':
        return 'Termine';
      default:
        return s;
    }
  }
}
