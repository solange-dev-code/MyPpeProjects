import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/services/api_service.dart';
import 'appointment_detail_page.dart';

/// Page des rendez-vous medecin.
/// Vue jour / semaine avec liste detaillee des RDV.
class AppointmentsPage extends StatefulWidget {
  const AppointmentsPage({super.key});

  @override
  State<AppointmentsPage> createState() => _AppointmentsPageState();
}

class _AppointmentsPageState extends State<AppointmentsPage> {
  DateTime _selectedDate = DateTime.now();
  bool _weekView = false;
  List<dynamic> _rendezVous = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadRendezVous();
  }

  Future<void> _loadRendezVous() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
      _rendezVous = await ApiService.getRendezVous(date: dateStr);
    } catch (e) {
      _errorMessage = 'Erreur de chargement : $e';
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
      locale: const Locale('fr', 'FR'),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() => _selectedDate = picked);
      _loadRendezVous();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Rendez-vous'),
        actions: [
          IconButton(
            icon: Icon(_weekView ? Icons.view_day : Icons.view_week),
            tooltip: _weekView ? 'Vue jour' : 'Vue semaine',
            onPressed: () => setState(() => _weekView = !_weekView),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadRendezVous,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildDateSelector(),
          Expanded(child: _buildList()),
        ],
      ),
    );
  }

  Widget _buildDateSelector() {
    return Container(
      padding: const EdgeInsets.all(12),
      color: AppColors.surface,
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            onPressed: () {
              setState(() {
                _selectedDate = _selectedDate.subtract(
                  Duration(days: _weekView ? 7 : 1),
                );
              });
              _loadRendezVous();
            },
          ),
          Expanded(
            child: InkWell(
              onTap: _pickDate,
              child: Center(
                child: Text(
                  _weekView
                      ? 'Semaine du ${DateFormat('d MMM', 'fr_FR').format(_selectedDate)}'
                      : DateFormat('EEEE d MMMM y', 'fr_FR')
                          .format(_selectedDate),
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: () {
              setState(() {
                _selectedDate = _selectedDate.add(
                  Duration(days: _weekView ? 7 : 1),
                );
              });
              _loadRendezVous();
            },
          ),
        ],
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
            const Icon(Icons.error_outline,
                size: 56, color: AppColors.danger),
            const SizedBox(height: 12),
            Text(_errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loadRendezVous, child: const Text('Reessayer')),
          ],
        ),
      );
    }
    if (_rendezVous.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.event_busy, size: 56, color: AppColors.textHint),
            const SizedBox(height: 12),
            const Text(
              'Aucun rendez-vous',
              style: TextStyle(color: AppColors.textSecondary),
            ),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _loadRendezVous,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _rendezVous.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, i) => _rdvTile(_rendezVous[i]),
      ),
    );
  }

  Widget _rdvTile(dynamic rdv) {
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

    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.all(12),
        leading: Container(
          width: 60,
          padding: const EdgeInsets.symmetric(vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.access_time, size: 14, color: AppColors.primary),
              const SizedBox(height: 2),
              Text(
                heure,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),
        ),
        title: Text(
          patientName.isEmpty ? 'Patient' : patientName,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(motif.toString()),
        trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => AppointmentDetailPage(rdv: r),
            ),
          );
        },
      ),
    );
  }
}
