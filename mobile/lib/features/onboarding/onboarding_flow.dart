/// Root onboarding flow (3 pages, never shows navigation bar).
///
/// After completion the profile is posted to the server with
/// `onboarding_completed = true`, and the local onboarding cache flag is
/// set so subsequent cold starts skip onboarding instantly.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../core/storage/storage_service.dart';
import '../../widgets/primary_button.dart';
import '../../app.dart';
import '../root_gate.dart';
import 'goal_screen.dart';
import 'health_permission_screen.dart';
import 'onboarding_controller.dart';
import 'profile_screen.dart';

class OnboardingFlow extends StatefulWidget {
  const OnboardingFlow({super.key, required this.onComplete});

  /// Called after the server confirms onboarding_completed.
  final VoidCallback onComplete;

  @override
  State<OnboardingFlow> createState() => _OnboardingFlowState();
}

class _OnboardingFlowState extends State<OnboardingFlow> {
  late final OnboardingController _ctrl;
  final PageController _pages = PageController();

  @override
  void initState() {
    super.initState();
    _ctrl = OnboardingController();
    _ctrl.addListener(() {
      if (!_pages.hasClients) return;
      _pages.animateToPage(_ctrl.step, duration: const Duration(milliseconds: 280), curve: Curves.easeInOut);
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _pages.dispose();
    super.dispose();
  }

  Future<void> _finish() async {
    final profileRepo = AppServices.instance.profileRepository;
    try {
      await profileRepo.update(
        primaryGoalWire: _ctrl.goal?.wire,
        ageGroup: _ctrl.ageGroup,
        gender: _ctrl.gender,
        heightCm: _ctrl.heightCm,
        weightKg: _ctrl.weightKg,
        activityLevelWire: _ctrl.activityLevel?.wire,
        onboardingCompleted: true,
      );
      await StorageService.instance.setBool('onboarding_completed', true);
      widget.onComplete();
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const RootGate()),
          (_) => false,
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text(AppStrings.somethingWentWrong)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ChangeNotifierProvider<OnboardingController>.value(
      value: _ctrl,
      child: Scaffold(
        appBar: AppBar(
          title: const Text(AppStrings.appName),
          actions: [
            if (_ctrl.step > 0)
              TextButton(onPressed: () => _ctrl.back(), child: const Text('Back')),
            const SizedBox(width: 4),
          ],
        ),
        body: PageView(
          controller: _pages,
          physics: const NeverScrollableScrollPhysics(),
          children: const [
            GoalScreen(),
            ProfileScreen(),
            HealthPermissionScreen(),
          ],
        ),
        bottomNavigationBar: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Step indicator dots
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(3, (i) {
                    final active = i == _ctrl.step;
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 250),
                      margin: const EdgeInsets.symmetric(horizontal: 5),
                      width: active ? 24 : 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: active ? scheme.primary : scheme.outlineVariant,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    );
                  }),
                ),
              ),
              if (_ctrl.step < 2)
                PrimaryButton(
                  label: 'Continue',
                  onPressed: (_ctrl.step == 0 && _ctrl.goal == null) ||
                          (_ctrl.step == 1 && _ctrl.activityLevel == null)
                      ? null
                      : _ctrl.next,
                )
              else
                PrimaryButton(
                  label: 'Start my journey',
                  icon: Icons.arrow_forward,
                  onPressed: _finish,
                ),
            ],
          ),
        ),
      ),
    );
  }
}