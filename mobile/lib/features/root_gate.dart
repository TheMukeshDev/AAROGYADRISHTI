/// Root gate: decides where an authenticated user lands next.
///
/// - unauthenticated  -> WelcomeScreen
/// - authenticated but onboarding incomplete -> OnboardingFlow
/// - authenticated & onboarded -> AppScaffold
///
/// Onboarding state is fetched from the server profile (authoritative) and
/// mirrored to local cache for instant cold-start decisions.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/constants/app_strings.dart';
import '../core/network/api_exception.dart';
import '../core/storage/storage_service.dart';
import '../providers/auth_provider.dart';
import '../widgets/app_scaffold.dart';
import '../app.dart';
import 'auth/welcome_screen.dart';
import 'onboarding/onboarding_flow.dart';

class RootGate extends StatefulWidget {
  const RootGate({super.key});

  @override
  State<RootGate> createState() => _RootGateState();
}

class _RootGateState extends State<RootGate> {
  bool _checking = false;
  bool _onboarded = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _resolve());
  }

  Future<void> _resolve() async {
    final auth = context.read<AuthProvider>();
    if (!auth.isAuthenticated) return;

    setState(() {
      _checking = true;
      _error = null;
    });

    try {
      final cached = await StorageService.instance.getBool('onboarding_completed');
      if (cached == true) {
        setState(() => _onboarded = true);
      } else {
        final profile = await AppServices.instance.profileRepository.get();
        _onboarded = profile.isOnboarded;
        await StorageService.instance.setBool('onboarding_completed', _onboarded);
      }
    } catch (e) {
      // Offline / API unavailable: fall back to cache, default to onboarding.
      if (e is NetworkException || e is ServerException) {
        final cached = await StorageService.instance.getBool('onboarding_completed');
        setState(() => _onboarded = cached ?? false);
      } else {
        _error = AppStrings.somethingWentWrong;
      }
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    if (auth.status == AuthStatus.unknown) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (!auth.isAuthenticated) {
      return const WelcomeScreen();
    }
    if (_checking) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.cloud_off, size: 40),
                const SizedBox(height: 12),
                Text(_error!, textAlign: TextAlign.center),
                const SizedBox(height: 16),
                FilledButton(onPressed: _resolve, child: const Text('Try again')),
              ],
            ),
          ),
        ),
      );
    }

    return _onboarded ? const AppScaffold() : OnboardingFlow(onComplete: () {
      setState(() => _onboarded = true);
    });
  }
}