import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/constants/app_colors.dart';
import '../appointments/appointments_page.dart';
import '../home/home_page.dart';
import '../messages/messages_page.dart';
import '../profile/profile_page.dart';
import '../../shared/services/api_service.dart';

class PaymentsPage extends StatefulWidget {
  const PaymentsPage({super.key});

  @override
  State<PaymentsPage> createState() => _PaymentsPageState();
}

class _PaymentsPageState extends State<PaymentsPage> {
  static const Color payColor = Color(0xFF6366F1);

  List<dynamic> _factures = [];
  bool _isLoading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _loadFactures();
  }

  Future<void> _loadFactures() async {
    setState(() {
      _isLoading = true;
      _error = '';
    });
    try {
      final data = await ApiService.getFactures();
      if (mounted) {
        setState(() {
          _factures = data;
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

  // Total des factures en attente
  double get _totalEnAttente => _factures
      .where((f) => f['statut'] == 'en_attente' || f['statut'] == 'partiel')
      .fold(0.0, (sum, f) {
    final montant = double.tryParse(f['part_patient']?.toString() ?? '0') ?? 0;
    return sum + montant;
  });

  List<dynamic> get _facturesEnAttente => _factures
      .where((f) => f['statut'] == 'en_attente' || f['statut'] == 'partiel')
      .toList();

  List<dynamic> get _facturesPayees =>
      _factures.where((f) => f['statut'] == 'payee').toList();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: payColor,
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Paiements',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error.isNotEmpty
              ? _buildError()
              : RefreshIndicator(
                  onRefresh: _loadFactures,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 8),

                        // Carte solde à payer
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(22),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [
                                Color(0xFF6366F1),
                                Color(0xFF818CF8),
                              ],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Solde à payer',
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _totalEnAttente == 0
                                    ? 'Aucun solde dû'
                                    : '${_formatMontant(_totalEnAttente)} FCFA',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 28,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${_facturesEnAttente.length} facture(s) en attente',
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 13,
                                ),
                              ),
                              if (_totalEnAttente > 0) ...[
                                const SizedBox(height: 16),
                                ElevatedButton(
                                  onPressed: () => _showPaymentMethods(context),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white,
                                    foregroundColor: payColor,
                                    elevation: 0,
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 24,
                                      vertical: 10,
                                    ),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                  ),
                                  child: const Text(
                                    'Payer maintenant',
                                    style:
                                        TextStyle(fontWeight: FontWeight.w600),
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),

                        const SizedBox(height: 28),

                        // Moyens de paiement
                        const Text(
                          'Moyens de paiement',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1A1A2E),
                          ),
                        ),

                        const SizedBox(height: 14),

                        _buildPaymentMethod(
                          color: const Color(0xFF005AFF),
                          icon: Icons.grid_view_rounded,
                          label: 'Moov Money (Flooz)',
                        ),
                        _buildPaymentMethod(
                          color: const Color(0xFFFFCC00),
                          icon: Icons.favorite_rounded,
                          label: 'MTN Mobile Money',
                          iconColor: Colors.orange,
                        ),
                        _buildPaymentMethod(
                          color: const Color(0xFFFF6B00),
                          icon: Icons.favorite_rounded,
                          label: 'Orange Money',
                          iconColor: Colors.deepOrange,
                        ),
                        _buildPaymentMethod(
                          color: const Color(0xFF1A56DB),
                          icon: Icons.waves_rounded,
                          label: 'Wave',
                          iconColor: Colors.blue,
                        ),
                        _buildPaymentMethod(
                          color: const Color(0xFF00B2A9),
                          icon: Icons.phone_android_rounded,
                          label: 'Celtiis Cash',
                          iconColor: const Color(0xFF00B2A9),
                        ),
                        _buildPaymentMethod(
                          color: const Color(0xFF1A1A2E),
                          icon: Icons.credit_card_rounded,
                          label: 'Carte bancaire',
                          iconColor: const Color(0xFF4A5568),
                        ),

                        const SizedBox(height: 28),

                        // Historique
                        const Text(
                          'Historique de paiement',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1A1A2E),
                          ),
                        ),

                        const SizedBox(height: 14),

                        if (_factures.isEmpty)
                          _buildEmptyCard()
                        else
                          ..._factures.map((f) => Padding(
                                padding: const EdgeInsets.only(bottom: 12),
                                child: _buildHistoryCard(f),
                              )),

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

  // ==================== CARTE FACTURE ====================

  Widget _buildHistoryCard(Map<String, dynamic> f) {
    final statut = f['statut'] ?? '';
    final isPaid = statut == 'payee';
    final isPartiel = statut == 'partiel';
    final montantTotal = double.tryParse(
            f['montant_total']?.toString() ?? '0') ??
        0;
    final partPatient = double.tryParse(
            f['part_patient']?.toString() ?? '0') ??
        0;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  f['description'] ?? 'Facture',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                    color: Color(0xFF1A1A2E),
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(
                '${_formatMontant(montantTotal)} FCFA',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 15,
                  color: Color(0xFF1A1A2E),
                ),
              ),
            ],
          ),

          const SizedBox(height: 4),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                f['facture_id'] ?? '—',
                style: const TextStyle(fontSize: 13, color: Colors.grey),
              ),
              Row(
                children: [
                  Icon(
                    isPaid
                        ? Icons.check_circle_outline
                        : isPartiel
                            ? Icons.incomplete_circle_outlined
                            : Icons.access_time_rounded,
                    size: 14,
                    color: isPaid
                        ? const Color(0xFF16A34A)
                        : isPartiel
                            ? const Color(0xFF9333EA)
                            : const Color(0xFFD97706),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    isPaid
                        ? 'Payé'
                        : isPartiel
                            ? 'Partiel'
                            : 'En attente',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isPaid
                          ? const Color(0xFF16A34A)
                          : isPartiel
                              ? const Color(0xFF9333EA)
                              : const Color(0xFFD97706),
                    ),
                  ),
                ],
              ),
            ],
          ),

          const SizedBox(height: 4),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _formatDate(f['date_facture'] ?? ''),
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
              if (f['part_assurance'] != null &&
                  double.tryParse(f['part_assurance'].toString()) != 0)
                Text(
                  'Assurance: ${_formatMontant(double.tryParse(f['part_assurance'].toString()) ?? 0)} FCFA',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
            ],
          ),

          // Part patient
          if (partPatient > 0 && !isPaid) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF3C7),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'Votre part : ${_formatMontant(partPatient)} FCFA',
                style: const TextStyle(
                  fontSize: 13,
                  color: Color(0xFFD97706),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],

          if (!isPaid) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => _showPaymentMethods(context, facture: f),
                style: ElevatedButton.styleFrom(
                  backgroundColor: payColor,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                child: const Text(
                  'Payer',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ==================== MODAL PAIEMENT ====================

  void _showPaymentMethods(
    BuildContext context, {
    Map<String, dynamic>? facture,
  }) {
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
              facture != null
                  ? 'Payer ${facture['description'] ?? 'la facture'}'
                  : 'Choisir un moyen de paiement',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1A1A2E),
              ),
            ),
            if (facture != null) ...[
              const SizedBox(height: 4),
              Text(
                'Montant : ${_formatMontant(double.tryParse(facture['part_patient']?.toString() ?? '0') ?? 0)} FCFA',
                style: const TextStyle(
                  fontSize: 14,
                  color: Colors.grey,
                ),
              ),
            ],
            const SizedBox(height: 16),
            _buildPaymentOption('Moov Money (Flooz)', const Color(0xFF005AFF)),
            _buildPaymentOption('MTN Mobile Money', Colors.orange),
            _buildPaymentOption('Orange Money', Colors.deepOrange),
            _buildPaymentOption('Wave', Colors.blue),
            _buildPaymentOption('Celtiis Cash', const Color(0xFF00B2A9)),
            _buildPaymentOption('Carte bancaire', const Color(0xFF4A5568)),
            const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }

  Widget _buildPaymentOption(String label, Color color) {
    return InkWell(
      onTap: () {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Redirection vers $label...'),
            backgroundColor: payColor,
          ),
        );
      },
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.payment, color: color, size: 18),
            ),
            const SizedBox(width: 14),
            Text(
              label,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: Color(0xFF1A1A2E),
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
    );
  }

  // ==================== WIDGETS UTILITAIRES ====================

  Widget _buildPaymentMethod({
    required Color color,
    required IconData icon,
    required String label,
    Color? iconColor,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: iconColor ?? color, size: 22),
          ),
          const SizedBox(width: 16),
          Text(
            label,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w500,
              color: Color(0xFF1A1A2E),
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
    );
  }

  Widget _buildEmptyCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(30),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(
            Icons.receipt_long_outlined,
            size: 48,
            color: Colors.grey.shade300,
          ),
          const SizedBox(height: 12),
          const Text(
            'Aucune facture',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1A1A2E),
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Vos factures apparaîtront ici',
            style: TextStyle(fontSize: 13, color: Colors.grey),
          ),
        ],
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
              onPressed: _loadFactures,
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
              style: ElevatedButton.styleFrom(
                backgroundColor: payColor,
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

  // ==================== HELPERS ====================

  String _formatMontant(double montant) {
    if (montant == montant.truncate()) {
      return montant.truncate().toString().replaceAllMapped(
            RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
            (m) => '${m[1]},',
          );
    }
    return montant.toStringAsFixed(0);
  }

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