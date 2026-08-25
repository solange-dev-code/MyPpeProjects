import 'package:flutter/material.dart';

/// Palette de couleurs de l'application medecin Sanar.
/// Bleu medical (primary), vert (accent), rouge (danger).
class AppColors {
  // Couleur principale - bleu medical
  static const Color primary = Color(0xFF1F6C92);
  static const Color primaryDark = Color(0xFF155270);
  static const Color primaryLight = Color(0xFF3D8AB0);

  // Accent - vert validation
  static const Color accent = Color(0xFF16A34A);
  static const Color accentLight = Color(0xFF4ADE80);

  // Danger - rouge urgence
  static const Color danger = Color(0xFFDC2626);
  static const Color dangerLight = Color(0xFFFCA5A5);

  // Couleurs de triage P1-P5
  static const Color p1 = Color(0xFFDC2626); // Rouge - critique
  static const Color p2 = Color(0xFFF97316); // Orange - urgent
  static const Color p3 = Color(0xFF1F6C92); // Bleu - standard
  static const Color p4 = Color(0xFF6B7280); // Gris - moins urgent
  static const Color p5 = Color(0xFF16A34A); // Vert - non urgent

  // Couleurs de fond et surfaces
  static const Color background = Color(0xFFF5F7FA);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color cardBackground = Color(0xFFFFFFFF);

  // Textes
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF64748B);
  static const Color textHint = Color(0xFF94A3B8);
  static const Color textOnPrimary = Color(0xFFFFFFFF);

  // Bordures et dividers
  static const Color border = Color(0xFFE2E8F0);
  static const Color divider = Color(0xFFCBD5E1);

  // Statuts RDV
  static const Color statusConfirmed = Color(0xFF16A34A);
  static const Color statusPending = Color(0xFFF59E0B);
  static const Color statusCancelled = Color(0xFFDC2626);
  static const Color statusDone = Color(0xFF6B7280);

  // Analyses flags
  static const Color flagNormal = Color(0xFF16A34A);
  static const Color flagHigh = Color(0xFFF59E0B);
  static const Color flagLow = Color(0xFF3B82F6);
  static const Color flagCritical = Color(0xFFDC2626);
}
