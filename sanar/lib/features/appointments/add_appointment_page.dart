import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/constants/app_colors.dart';
import '../../shared/widgets/sanar_button.dart';
import '../../shared/services/api_service.dart';

class AddAppointmentPage extends StatefulWidget {
  const AddAppointmentPage({super.key});

  @override
  State<AddAppointmentPage> createState() => _AddAppointmentPageState();
}

class _AddAppointmentPageState extends State<AddAppointmentPage> {
  final _noteController = TextEditingController();
  final _motifController = TextEditingController();

  String? _selectedSpecialty;
  Map<String, dynamic>? _selectedDoctor; // médecin sélectionné automatiquement
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  String? _selectedMotif;

  List<dynamic> _hopitaux = [];
  Map<String, dynamic>? _selectedHopital;
  bool _isLoadingHopitaux = true;

  List<dynamic> _medecins = [];
  List<dynamic> _medecinsFiltres = [];
  bool _isLoading = false;
  bool _isLoadingMedecins = true;

  List<String> _specialties = [
    'Cardiologie',
    'Dermatologie',
    'Généraliste',
    'Gynécologie',
    'Neurologie',
    'Ophtalmologie',
    'Pédiatrie',
    'Radiologie',
  ];

  // Map entre label affiché et valeur en base
  final Map<String, String> _specialtyMap = {
    'Cardiologie': 'cardiologue',
    'Dermatologie': 'dermatologue',
    'Généraliste': 'generaliste',
    'Gynécologie': 'gynecologue',
    'Neurologie': 'neurologue',
    'Ophtalmologie': 'ophtalmologue',
    'Pédiatrie': 'pediatre',
    'Radiologie': 'radiologue',
  };

  final List<String> _motifs = [
    'Consultation de routine',
    'Suivi de traitement',
    'Urgence',
    'Résultats d\'analyses',
    'Renouvellement d\'ordonnance',
    'Autre',
  ];

  @override
  void initState() {
    super.initState();
    _loadMedecins();
    _loadHopitaux();
  }

  @override
  void dispose() {
    _noteController.dispose();
    _motifController.dispose();
    super.dispose();
  }

  Future<void> _loadMedecins() async {
    try {
      final medecins = await ApiService.getMedecins();
      if (mounted) {
        setState(() {
          _medecins = medecins;
          _isLoadingMedecins = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingMedecins = false);
    }
  }

  Future<void> _loadHopitaux() async {
    try {
      final hopitaux = await ApiService.getHopitaux();
      if (mounted) {
        setState(() {
          _hopitaux = hopitaux;
          _isLoadingHopitaux = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingHopitaux = false);
    }
  }


 void _onSpecialtyChanged(String? specialty) {
    setState(() {
        _selectedSpecialty = specialty;
        _selectedDoctor = null;
    });

    if (specialty == null) return;

    final valeurSpec = _specialtyMap[specialty] ?? specialty.toLowerCase();
    
    // Filtrer par specialite ET par hopital choisi
    List<dynamic> filtres;
    if (_selectedHopital != null) {
      final hopitalId = _selectedHopital!['id'];
      filtres = _medecins
          .where((m) => m['hopital'] == hopitalId)
          .where((m) => m['specialite'].toString().toLowerCase() == valeurSpec.toLowerCase())
          .toList();
    } else {
      filtres = _medecins
          .where((m) => m['specialite'].toString().toLowerCase() == valeurSpec.toLowerCase())
          .toList();
    }

    setState(() {
        _medecinsFiltres = filtres;
        if (filtres.length == 1) {
            _selectedDoctor = filtres[0];
        }
    });
}

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(
          colorScheme: const ColorScheme.light(primary: AppColors.primary),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 9, minute: 0),
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(
          colorScheme: const ColorScheme.light(primary: AppColors.primary),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _selectedTime = picked);
  }

  Future<void> _submit() async {
    // Validation
    if (_selectedSpecialty == null) {
      _showError('Veuillez choisir une spécialité');
      return;
    }
    if (_selectedDoctor == null && _medecinsFiltres.isEmpty) {
      _showError('Aucun médecin disponible pour cette spécialité');
      return;
    }
    if (_selectedDate == null) {
      _showError('Veuillez choisir une date');
      return;
    }
    if (_selectedTime == null) {
      _showError('Veuillez choisir une heure');
      return;
    }

    if (_selectedHopital == null) {
      _showError('Veuillez choisir un hôpital');
      return;
    }

    if (_selectedMotif == null) {
      _showError('Veuillez choisir un motif');
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Si plusieurs médecins, prend le premier disponible
      final medecin = _selectedDoctor ?? _medecinsFiltres.first;

      // Formate la date et l'heure
      final date =
          '${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}';
      final heure =
          '${_selectedTime!.hour.toString().padLeft(2, '0')}:${_selectedTime!.minute.toString().padLeft(2, '0')}:00';

      await ApiService.createRendezVous({
        'medecin_id': medecin['id'],
        'hopital_id': _selectedHopital!['id'], 
        'date': date,
        'heure': heure,
        'motif': _selectedMotif,
        'note': _noteController.text.trim(),
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Rendez-vous pris avec succès !'),
            backgroundColor: Color(0xFF16A34A),
          ),
        );
        Navigator.pop(context);
      }
    } on DioException catch (e) {
      if (mounted) {
        String message = 'Erreur lors de la création du rendez-vous';
        if (e.type == DioExceptionType.connectionTimeout) {
          message = 'Impossible de contacter le serveur';
        }
        _showError(message);
      }
    } catch (e) {
      if (mounted) _showError('Erreur inattendue');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
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
          'Prendre un rendez-vous',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      body: _isLoadingMedecins
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 8),

                  // Info card
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFBFDBFE)),
                    ),
                    child: const Row(
                      children: [
                        Icon(
                          Icons.info_outline,
                          color: AppColors.primary,
                          size: 18,
                        ),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Choisissez votre spécialité et un médecin vous sera assigné automatiquement.',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.primary,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),


                  // Hôpital
                  _buildLabel('Hôpital *'),
                  _isLoadingHopitaux
                      ? const Center(child: CircularProgressIndicator())
                      : Container(
                          height: 54,
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: const Color(0xFFE2E8F0)),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.local_hospital_outlined,
                                color: AppColors.primary,
                                size: 20,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: DropdownButtonHideUnderline(
                                  child: DropdownButton<Map<String, dynamic>>(
                                    value: _selectedHopital,
                                    hint: const Text(
                                      'Choisir un hôpital',
                                      style: TextStyle(
                                        color: Color(0xFFB0BBC9),
                                        fontSize: 15,
                                      ),
                                    ),
                                    isExpanded: true,
                                    icon: const Icon(
                                      Icons.arrow_forward_ios_rounded,
                                      size: 14,
                                      color: Colors.grey,
                                    ),
                                    style: const TextStyle(
                                      fontSize: 15,
                                      color: Color(0xFF1A1A2E),
                                    ),
                                    items: _hopitaux
                                        .map(
                                          (h) => DropdownMenuItem<Map<String, dynamic>>(
                                            value: h,
                                            child: Text('${h['nom']} — ${h['ville']}'),
                                          ),
                                        )
                                        .toList(),
                                    onChanged: (val) {
                                      setState(() {
                                        _selectedHopital = val;
                                        // Filtrer les medecins selon l'hopital choisi
                                        _selectedDoctor = null;
                                        _selectedSpecialty = null;
                                        _medecinsFiltres = [];
                                        if (val != null) {
                                          final hopitalId = val['id'];
                                          _medecinsFiltres = _medecins
                                              .where((m) => m['hopital'] == hopitalId)
                                              .toList();
                                          // Extraire les specialites disponibles dans cet hopital
                                          final specs = <String>[];
                                          for (var m in _medecinsFiltres) {
                                            final spec = m['specialite'] as String?;
                                            if (spec != null && !specs.contains(spec)) {
                                              specs.add(spec);
                                            }
                                          }
                                          _specialties = specs.map((s) {
                                            // Capitaliser la première lettre
                                            return s[0].toUpperCase() + s.substring(1);
                                          }).toList();
                                        } else {
                                          // Restaurer toutes les specialites
                                          _specialties = [
                                            'Cardiologue', 'Généraliste', 'Dermatologue',
                                            'Gynécologue', 'Neurologue', 'Ophtalmologue',
                                            'Pédiatre', 'Radiologue',
                                          ];
                                        }
                                      });
                                    },
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),

                  const SizedBox(height: 16),
                  
                  // Spécialité (affichée seulement si un hôpital est choisi)
                  if (_selectedHopital != null) ...[
                  _buildLabel('Spécialité *'),
                  _buildDropdown(
                    hint: 'Choisir une spécialité',
                    value: _selectedSpecialty,
                    items: _specialties,
                    icon: Icons.medical_services_outlined,
                    onChanged: _onSpecialtyChanged,
                  ),
                  ],

                  // Médecin assigné (affiché si spécialité choisie)
                  if (_selectedSpecialty != null) ...[
                    const SizedBox(height: 16),
                    _buildLabel('Médecin assigné'),
                    if (_medecinsFiltres.isEmpty)
                      Container(
                        height: 54,
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEE2E2),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFFFCA5A5)),
                        ),
                        child: const Row(
                          children: [
                            Icon(
                              Icons.warning_amber_rounded,
                              color: Color(0xFFDC2626),
                              size: 20,
                            ),
                            SizedBox(width: 12),
                            Text(
                              'Aucun médecin disponible pour cette spécialité',
                              style: TextStyle(
                                color: Color(0xFFDC2626),
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      )
                    else if (_medecinsFiltres.length == 1)
                      // Un seul médecin → affichage direct
                      Container(
                        height: 54,
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          color: const Color(0xFFDCFCE7),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFF86EFAC)),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.person_outline_rounded,
                              color: Color(0xFF16A34A),
                              size: 20,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Dr. ${_medecinsFiltres[0]['prenom']} ${_medecinsFiltres[0]['nom']}',
                                style: const TextStyle(
                                  fontSize: 15,
                                  color: Color(0xFF16A34A),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                            const Icon(
                              Icons.check_circle,
                              color: Color(0xFF16A34A),
                              size: 18,
                            ),
                          ],
                        ),
                      )
                    else
                      // Plusieurs médecins → dropdown de choix
                      Container(
                        height: 54,
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFFE2E8F0)),
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.person_outline_rounded,
                              color: AppColors.primary,
                              size: 20,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: DropdownButtonHideUnderline(
                                child: DropdownButton<Map<String, dynamic>>(
                                  value: _selectedDoctor,
                                  hint: const Text(
                                    'Choisir un médecin',
                                    style: TextStyle(
                                      color: Color(0xFFB0BBC9),
                                      fontSize: 15,
                                    ),
                                  ),
                                  isExpanded: true,
                                  icon: const Icon(
                                    Icons.arrow_forward_ios_rounded,
                                    size: 14,
                                    color: Colors.grey,
                                  ),
                                  style: const TextStyle(
                                    fontSize: 15,
                                    color: Color(0xFF1A1A2E),
                                  ),
                                  items: _medecinsFiltres
                                    .map(
                                      (m) => DropdownMenuItem<Map<String, dynamic>>(
                                        value: m,
                                        child: Text(
                                          'Dr. ${m['prenom']} ${m['nom']}',
                                        ),
                                      ),
                                    )
                                    .toList(),
                                  onChanged: (val) =>
                                      setState(() => _selectedDoctor = val),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],

                  const SizedBox(height: 16),

                  // Date
                  _buildLabel('Date du rendez-vous *'),
                  GestureDetector(
                    onTap: _pickDate,
                    child: Container(
                      height: 54,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFFE2E8F0)),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.calendar_today_outlined,
                            color: AppColors.primary,
                            size: 20,
                          ),
                          const SizedBox(width: 12),
                          Text(
                            _selectedDate == null
                                ? 'Sélectionner une date'
                                : '${_selectedDate!.day.toString().padLeft(2, '0')}/${_selectedDate!.month.toString().padLeft(2, '0')}/${_selectedDate!.year}',
                            style: TextStyle(
                              fontSize: 15,
                              color: _selectedDate == null
                                  ? const Color(0xFFB0BBC9)
                                  : const Color(0xFF1A1A2E),
                            ),
                          ),
                          const Spacer(),
                          const Icon(
                            Icons.arrow_forward_ios_rounded,
                            size: 14,
                            color: Colors.grey,
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Heure
                  _buildLabel('Heure du rendez-vous *'),
                  GestureDetector(
                    onTap: _pickTime,
                    child: Container(
                      height: 54,
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFFE2E8F0)),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.access_time_rounded,
                            color: AppColors.primary,
                            size: 20,
                          ),
                          const SizedBox(width: 12),
                          Text(
                            _selectedTime == null
                                ? 'Sélectionner une heure'
                                : _selectedTime!.format(context),
                            style: TextStyle(
                              fontSize: 15,
                              color: _selectedTime == null
                                  ? const Color(0xFFB0BBC9)
                                  : const Color(0xFF1A1A2E),
                            ),
                          ),
                          const Spacer(),
                          const Icon(
                            Icons.arrow_forward_ios_rounded,
                            size: 14,
                            color: Colors.grey,
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Motif
                  _buildLabel('Motif de consultation *'),
                  _buildDropdown(
                    hint: 'Choisir un motif',
                    value: _selectedMotif,
                    items: _motifs,
                    icon: Icons.note_outlined,
                    onChanged: (val) => setState(() => _selectedMotif = val),
                  ),

                  const SizedBox(height: 16),

                  // Note
                  _buildLabel('Note (optionnel)'),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: TextField(
                      controller: _noteController,
                      maxLines: 4,
                      style: const TextStyle(fontSize: 15),
                      decoration: const InputDecoration(
                        hintText: 'Décrivez vos symptômes ou remarques...',
                        hintStyle: TextStyle(
                          color: Color(0xFFB0BBC9),
                          fontSize: 15,
                        ),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.all(16),
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),

                  SanarButton(
                    label: 'Confirmer le rendez-vous',
                    onPressed: _submit,
                    isLoading: _isLoading,
                  ),

                  const SizedBox(height: 20),
                ],
              ),
            ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: Color(0xFF1A1A2E),
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required String hint,
    required String? value,
    required List<String> items,
    required IconData icon,
    required void Function(String?) onChanged,
  }) {
    return Container(
      height: 54,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.primary, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: value,
                hint: Text(
                  hint,
                  style: const TextStyle(
                    color: Color(0xFFB0BBC9),
                    fontSize: 15,
                  ),
                ),
                isExpanded: true,
                icon: const Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 14,
                  color: Colors.grey,
                ),
                style: const TextStyle(
                  fontSize: 15,
                  color: Color(0xFF1A1A2E),
                ),
                items: items
                    .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                    .toList(),
                onChanged: onChanged,
              ),
            ),
          ),
        ],
      ),
    );
  }
}