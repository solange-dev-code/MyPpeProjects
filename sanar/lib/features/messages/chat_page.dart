import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../appointments/appointments_page.dart';
import '../home/home_page.dart';
import 'message_model.dart';
import '../profile/profile_page.dart';
import '../../shared/services/api_service.dart';



class ChatPage extends StatefulWidget {
  final String name;
  final String role;
  final List<Message> messages;
  final int? convId;

  const ChatPage({
    super.key,
    required this.name,
    required this.role,
    required this.messages,
    this.convId,
    
  });

  @override
  State<ChatPage> createState() => _ChatPageState();

}

class _ChatPageState extends State<ChatPage> {
  final _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late List<Message> messages;
  

  @override
  void initState() {
    super.initState();
    messages = List.from(widget.messages);
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  String formatTime(DateTime dateTime) {
  return "${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}";
}

void scrollToBottom() {
  _scrollController.animateTo(
    _scrollController.position.maxScrollExtent,
    duration: const Duration(milliseconds: 300),
    curve: Curves.easeOut,
  );
}

  void _sendMessage() async {
  final text = _controller.text.trim();
  if (text.isEmpty) return;

  setState(() {
    messages.add(Message(text, formatTime(DateTime.now()), true));
    _controller.clear();
  });

  scrollToBottom();

  // Envoie à l'API si convId disponible
  if (widget.convId != null) {
    try {
      await ApiService.sendMessage(widget.convId!, text);
    } catch (e) {
      // Message envoyé localement même si l'API échoue
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
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.medical_services_outlined, size: 18, color: Colors.white),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.name,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  widget.role,
                  style: const TextStyle(
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
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                return _buildBubble(msg);
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
                        hintText: 'Tapez votre message',
                        hintStyle: TextStyle(
                          color: Color(0xFFB0BBC9),
                          fontSize: 14,
                        ),
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 12),
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: _sendMessage,
                  child: Container(
                    width: 46,
                    height: 46,
                    decoration: const BoxDecoration(
                      color: AppColors.primary,
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
        selectedItemColor: AppColors.primary,
        unselectedItemColor: Colors.grey,
        currentIndex: 2,
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

  Widget _buildBubble(Message msg) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            msg.isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!msg.isMe) ...[
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: Color(0xFFEFF6FF),
                shape: BoxShape.circle,
              ),
              child:  Icon(
                Icons.medical_services_outlined,
                color: AppColors.primary,
                size: 16,
              ),
            ),
            const SizedBox(width: 8),
          ],
          Column(
            crossAxisAlignment: msg.isMe
                ? CrossAxisAlignment.end
                : CrossAxisAlignment.start,
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
                  color: msg.isMe
                      ? AppColors.primary
                      : Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(18),
                    topRight: const Radius.circular(18),
                    bottomLeft: Radius.circular(msg.isMe ? 18 : 4),
                    bottomRight: Radius.circular(msg.isMe ? 4 : 18),
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
                    color: msg.isMe ? Colors.white : const Color(0xFF1A1A2E),
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                msg.time,
                style: const TextStyle(fontSize: 11, color: Colors.grey),
              ),
            ],
          ),
        ],
      ),
    );
  }
}