import 'package:flutter/material.dart';

class Responsive {
  static bool isMobile(BuildContext context) =>
      MediaQuery.of(context).size.width < 600;

  static bool isWeb(BuildContext context) =>
      MediaQuery.of(context).size.width >= 600;

  static double maxWidth(BuildContext context) =>
      isWeb(context) ? 480 : double.infinity;

  static Widget webWrapper({
    required BuildContext context,
    required Widget child,
    Color? backgroundColor,
  }) {
    if (isMobile(context)) return child;

    return Scaffold(
      backgroundColor: backgroundColor ?? const Color(0xFFE8EDF5),
      body: Center(
        child: Container(
          width: 480,
          height: MediaQuery.of(context).size.height,
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.15),
                blurRadius: 30,
                offset: const Offset(0, 0),
              ),
            ],
          ),
          child: ClipRect(child: child),
        ),
      ),
    );
  }
}