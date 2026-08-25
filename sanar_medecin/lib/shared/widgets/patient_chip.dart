import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

/// Badge patient reutilisable : affiche nom + patient_id + (option) age.
class PatientChip extends StatelessWidget {
  final String nom;
  final String prenom;
  final String patientId;
  final String? age;
  final String? groupeSanguin;
  final VoidCallback? onTap;

  const PatientChip({
    super.key,
    required this.nom,
    required this.prenom,
    required this.patientId,
    this.age,
    this.groupeSanguin,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.primary.withOpacity(0.2)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: AppColors.primary,
              child: Text(
                _initials(),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$prenom $nom',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
                Text(
                  _subtitle(),
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
            if (groupeSanguin != null && groupeSanguin!.isNotEmpty) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.danger.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  groupeSanguin!,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: AppColors.danger,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _initials() {
    final i1 = prenom.isNotEmpty ? prenom[0].toUpperCase() : '?';
    final i2 = nom.isNotEmpty ? nom[0].toUpperCase() : '?';
    return '$i1$i2';
  }

  String _subtitle() {
    final parts = <String>[];
    if (patientId.isNotEmpty) parts.add('#$patientId');
    if (age != null && age!.isNotEmpty) parts.add('$age ans');
    return parts.isEmpty ? 'Patient' : parts.join(' - ');
  }
}
