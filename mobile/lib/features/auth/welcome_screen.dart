/// Welcome screen - plain-language product explanation, no medical claims.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/primary_button.dart';
import 'login_screen.dart';
import 'signup_screen.dart';

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> {
  bool _demoLoading = false;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                AppConstants.appName,
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: scheme.primary),
              ),
              const Spacer(),
              Container(
                width: 84,
                height: 84,
                decoration: BoxDecoration(
                  color: scheme.primaryContainer,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: Icon(Icons.filter_center_focus, size: 44, color: scheme.primary),
              ),
              const SizedBox(height: 28),
              Text(
                AppStrings.welcomeTitle,
                style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, height: 1.15),
              ),
              const SizedBox(height: 14),
              Text(
                AppStrings.welcomeSubtitle,
                style: TextStyle(fontSize: 16, height: 1.5, color: scheme.onSurfaceVariant),
              ),
              const Spacer(),
              PrimaryButton(
                label: AppStrings.getStarted,
                icon: Icons.arrow_forward,
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const SignupScreen()),
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                ),
                child: const Text(AppStrings.alreadyHaveAccount),
              ),
              const SizedBox(height: 4),
              _demoAccess(scheme),
            ],
          ),
        ),
      ),
    );
  }

  /// Clearly labelled demo access for hackathon / UI testing. It never merges
  /// into a real account and the backend flags demo rows with source=demo.
  Widget _demoAccess(ColorScheme scheme) {
    if (AppConstants.isProduction) return const SizedBox.shrink();
    return Column(
      children: [
        Divider(height: 28, color: scheme.outlineVariant),
        TextButton.icon(
          onPressed: _demoLoading
              ? null
              : () async {
                  setState(() => _demoLoading = true);
                  try {
                    await context.read<AuthProvider>().loginWithDemo();
                  } finally {
                    if (mounted) setState(() => _demoLoading = false);
                  }
                },
          icon: const Icon(Icons.science_outlined, size: 18),
          label: Text(_demoLoading ? 'Loading demo data\u2026' : 'Explore with Demo Data'),
        ),
        Text(
          'Demo Data \u00b7 development only',
          style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
        ),
      ],
    );
  }
}