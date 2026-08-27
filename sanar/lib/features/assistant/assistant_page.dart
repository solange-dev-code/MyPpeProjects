import 'package:flutter/material.dart';
import '../appointments/appointments_page.dart';
import '../appointments/add_appointment_page.dart';
import '../home/home_page.dart';
import '../messages/messages_page.dart';
import '../payments/payments_page.dart';
import '../results/results_page.dart';

class AssistantPage extends StatefulWidget {
  const AssistantPage({super.key});

  @override
  State<AssistantPage> createState() => _AssistantPageState();
}

class _AssistantMessage {
  final String text;
  final bool isBot;
  _AssistantMessage(this.text, this.isBot);
}

class _AssistantPageState extends State<AssistantPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  final List<_AssistantMessage> _messages = [
    _AssistantMessage(
      'Bonjour! Je suis votre assistant virtuel Sanar. Comment puis-je vous aider aujourd\'hui?',
      true,
    ),
  ];

  static const Color green = Color(0xFF16A34A);

  final List<Map<String, String>> _quickActions = [
    {'label': 'Prendre un rendez-vous', 'action': 'rdv'},
    {'label': 'Voir mes résultats', 'action': 'results'},
    {'label': 'Contacter un médecin', 'action': 'contact'},
    {'label': 'Payer une facture', 'action': 'pay'},
  ];

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage(String text) {
    if (text.trim().isEmpty) return;
    setState(() {
      _messages.add(_AssistantMessage(text, false));
    });
    _controller.clear();
    _scrollToBottom();

    // Réponse automatique du bot
    Future.delayed(const Duration(milliseconds: 800), () {
      if (mounted) {
        setState(() {
          _messages.add(_AssistantMessage(_getBotResponse(text), true));
        });
        _scrollToBottom();
      }
    });
  }

  String _getBotResponse(String input) {
    final lower = input.toLowerCase();
    if (lower.contains('rendez') || lower.contains('rdv')) {
      return 'Je peux vous aider à prendre un rendez-vous. Veuillez choisir une spécialité dans le formulaire de prise de rendez-vous.';
    } else if (lower.contains('résultat') || lower.contains('analyse')) {
      return 'Vos résultats d\'analyses sont disponibles dans la section "Résultats" de l\'application.';
    } else if (lower.contains('médecin') || lower.contains('contact')) {
      return 'Vous pouvez contacter votre médecin directement via la messagerie de l\'application.';
    } else if (lower.contains('payer') || lower.contains('facture') || lower.contains('paiement')) {
      return 'Vous pouvez régler vos factures dans la section "Paiements". Plusieurs moyens de paiement sont disponibles.';
    } else if (lower.contains('bonjour') || lower.contains('salut')) {
      return 'Bonjour! Comment puis-je vous aider aujourd\'hui?';
    } else {
      return 'Je comprends votre demande. Pour toute assistance médicale urgente, veuillez contacter directement votre médecin ou appeler le 15.';
    }
  }

  void _handleQuickAction(String action, String label) {
    _sendMessage(label);
    if (action == 'rdv') {
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const AddAppointmentPage()),
          );
        }
      });
    } else if (action == 'results') {
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ResultsPage()),
          );
        }
      });
    } else if (action == 'pay') {
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PaymentsPage()),
          );
        }
      });
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: green,
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.smart_toy_outlined,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Assistant virtuel',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  'En ligne',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white70,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Messages
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + 1,
              itemBuilder: (context, index) {
                if (index == _messages.length) {
                  // Actions rapides après le premier message
                  if (_messages.length == 1) {
                    return _buildQuickActions();
                  }
                  return const SizedBox.shrink();
                }
                return _buildBubble(_messages[index]);
              },
            ),
          ),

          // Champ de saisie
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(
                top: BorderSide(color: Color(0xFFEEF2FF)),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF5F7FA),
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(
                        hintText: 'Posez votre question',
                        hintStyle: TextStyle(
                          color: Color(0xFFB0BBC9),
                          fontSize: 14,
                        ),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 12),
                      ),
                      onSubmitted: _sendMessage,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: () => _sendMessage(_controller.text),
                  child: Container(
                    width: 46,
                    height: 46,
                    decoration: const BoxDecoration(
                      color: green,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.send_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        selectedItemColor: green,
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

  Widget _buildBubble(_AssistantMessage msg) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            msg.isBot ? MainAxisAlignment.start : MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (msg.isBot) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: green.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.smart_toy_outlined,
                color: green,
                size: 16,
              ),
            ),
            const SizedBox(width: 8),
          ],
          Column(
            crossAxisAlignment: msg.isBot
                ? CrossAxisAlignment.start
                : CrossAxisAlignment.end,
            children: [
              Container(
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.65,
                ),
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
                decoration: BoxDecoration(
                  color: msg.isBot ? Colors.white : green,
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(18),
                    topRight: const Radius.circular(18),
                    bottomLeft: Radius.circular(msg.isBot ? 4 : 18),
                    bottomRight: Radius.circular(msg.isBot ? 18 : 4),
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 4,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Text(
                  msg.text,
                  style: TextStyle(
                    fontSize: 14,
                    color: msg.isBot
                        ? const Color(0xFF1A1A2E)
                        : Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Maintenant',
                style: TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActions() {
    return Column(
      children: [
        const SizedBox(height: 8),
        const Text(
          'Actions rapides',
          style: TextStyle(
            fontSize: 13,
            color: Colors.grey,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 12),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 2.8,
          children: _quickActions.map((action) {
            return GestureDetector(
              onTap: () => _handleQuickAction(
                action['action']!,
                action['label']!,
              ),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.03),
                      blurRadius: 4,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Center(
                  child: Text(
                    action['label']!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 13,
                      color: Color(0xFF1A1A2E),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 16),
      ],
    );
  }
}