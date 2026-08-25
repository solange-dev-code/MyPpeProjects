import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../shared/widgets/sanar_button.dart';
import '../../shared/widgets/sanar_input.dart';
import 'login_page.dart';
import '../../core/utils/responsive.dart';
import '../../shared/services/api_service.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _nomController = TextEditingController();
  final _emailController = TextEditingController();
  final _telephoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _nomController.dispose();
    _emailController.dispose();
    _telephoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  

void _onRegister() async {
  if (_nomController.text.isEmpty ||
      _emailController.text.isEmpty ||
      _telephoneController.text.isEmpty ||
      _passwordController.text.isEmpty ||
      _confirmPasswordController.text.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Veuillez remplir tous les champs')),
    );
    return;
  }

  if (_passwordController.text != _confirmPasswordController.text) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Les mots de passe ne correspondent pas'),
        backgroundColor: Colors.red,
      ),
    );
    return;
  }

  setState(() => _isLoading = true);

  try {
    await ApiService.register({
      'username': _emailController.text.trim(),
      'email': _emailController.text.trim(),
      'password': _passwordController.text.trim(),
      'nom': _nomController.text.trim().split(' ').last,
      'prenom': _nomController.text.trim().split(' ').first,
      'telephone': _telephoneController.text.trim(),
      'date_naissance': '1990-01-01',
      'adresse': 'Abidjan',
      'groupe_sanguin': 'O+',
    });

    if (mounted) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const LoginPage()),
        (route) => false,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Compte créé ! Connectez-vous'),
          backgroundColor: Color(0xFF16A34A),
        ),
      );
    }
  } catch (e) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur : ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  } finally {
    if (mounted) setState(() => _isLoading = false);
  }
}

  

@override
Widget build(BuildContext context) {
  return Responsive.webWrapper(
    context: context,
    backgroundColor: AppColors.background,
    child: Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Créer un compte',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 32),
          child: Column(
            children: [
              SanarInput(
                hint: 'Nom complet',
                icon: Icons.person_outline_rounded,
                controller: _nomController,
                keyboardType: TextInputType.name,
              ),
              const SizedBox(height: 14),
              SanarInput(
                hint: 'Email',
                icon: Icons.mail_outline_rounded,
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 14),
              SanarInput(
                hint: 'Téléphone',
                icon: Icons.phone_outlined,
                controller: _telephoneController,
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 14),
              SanarInput(
                hint: 'Mot de passe',
                icon: Icons.lock_outline_rounded,
                controller: _passwordController,
                obscureText: true,
              ),
              const SizedBox(height: 14),
              SanarInput(
                hint: 'Confirmer le mot de passe',
                icon: Icons.lock_outline_rounded,
                controller: _confirmPasswordController,
                obscureText: true,
              ),
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.inputBackground,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.inputBorder),
                ),
                child: RichText(
                  text: TextSpan(
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                      height: 1.5,
                    ),
                    children: [
                      const TextSpan(
                        text: 'En créant un compte, vous acceptez nos ',
                      ),
                      TextSpan(
                        text: "Conditions d'utilisation",
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const TextSpan(text: ' et notre '),
                      TextSpan(
                        text: 'Politique de confidentialité',
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const TextSpan(text: '.'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 28),
              SanarButton(
                label: 'Créer mon compte',
                onPressed: _onRegister,
                isLoading: _isLoading,
              ),
            ],
          ),
        ),
      ),
    ),
  );
}
  }
