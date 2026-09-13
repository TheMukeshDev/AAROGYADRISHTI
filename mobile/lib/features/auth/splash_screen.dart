/// Splash screen - premium brand moment while the session is restored.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../root_gate.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _navigate();
  }

  Future<void> _navigate() async {
    await Future.delayed(const Duration(milliseconds: 650));
    if (!mounted) return;
    _goTo(const RootGate());
  }

  void _goTo(Widget screen) {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (_, __, ___) => screen,
        transitionsBuilder: (_, animation, __, child) =>
            FadeTransition(opacity: animation, child: child),
        transitionDuration: const Duration(milliseconds: 350),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [scheme.primary, scheme.primaryContainer],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TweenAnimationBuilder<double>(
              tween: Tween(begin: 0.84, end: 1),
              duration: const Duration(milliseconds: 550),
              curve: Curves.easeOutBack,
              builder: (context, scale, child) => Transform.scale(scale: scale, child: child),
              child: Image.asset(
                'assets/images/AarogyaDrishti.png',
                width: 180,
                height: 180,
                fit: BoxFit.contain,
              ),
            ),
            const SizedBox(height: 28),
            Text(
              AppConstants.appName,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white,
                fontSize: 34,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              AppStrings.tagline,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.9),
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 40),
            const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
            ),
          ],
        ),
      ),
    );
  }
}