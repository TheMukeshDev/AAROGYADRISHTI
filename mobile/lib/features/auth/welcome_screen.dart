/// Welcome screen - plain-language product explanation, no medical claims.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/app_logo.dart';
import '../../widgets/primary_button.dart';
import '../../widgets/secondary_button.dart';
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
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxHeight < 620;
            return SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight - 40),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        LogoMark(size: 34),
                        const SizedBox(width: 12),
                        Text(
                          AppConstants.appName,
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, letterSpacing: -0.2),
                        ),
                      ],
                    ),
                    SizedBox(height: compact ? 12 : 40),
                    Hero(
                      tag: 'aarogya-logo',
                      child: LogoMark(size: compact ? 110 : 150),
                    ),
                    SizedBox(height: compact ? 20 : 36),
                    Text(
                      AppStrings.welcomeTitle,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 27, fontWeight: FontWeight.w800, height: 1.2, letterSpacing: -0.4),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      AppStrings.welcomeSubtitle,
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 15.5, height: 1.55, color: scheme.onSurfaceVariant),
                    ),
                    SizedBox(height: compact ? 20 : 40),
                    PrimaryButton(
                      label: AppStrings.getStarted,
                      icon: Icons.arrow_forward_rounded,
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const SignupScreen()),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SecondaryButton(
                      label: AppStrings.login,
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => const LoginScreen()),
                      ),
                    ),
                    if (!AppConstants.isProduction) ...[
                      SizedBox(height: compact ? 12 : 28),
                      _demoAccess(scheme),
                    ],
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  /// Clearly labelled demo access for hackathon / UI testing. It never merges
  /// into a real account and the backend flags demo rows with source=demo.
  Widget _demoAccess(ColorScheme scheme) {
    return Column(
      children: [
        Divider(height: 24, color: scheme.outlineVariant),
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
          icon: _demoLoading
              ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.science_outlined, size: 18),
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