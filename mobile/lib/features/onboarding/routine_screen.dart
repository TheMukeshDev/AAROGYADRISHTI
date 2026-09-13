/// Daily routine screen (onboarding step 2). All fields optional.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/app_enums.dart';
import 'onboarding_controller.dart';

class RoutineScreen extends StatelessWidget {
  const RoutineScreen({super.key});

  static const _sleepOptions = [
    (6.0, '<6 h'),
    (7.0, '6\u20137 h'),
    (8.0, '7\u20139 h'),
    (10.0, '9 h+'),
  ];

  @override
  Widget build(BuildContext context) {
    final ctrl = context.watch<OnboardingController>();
    final scheme = Theme.of(context).colorScheme;

    final waterIndex = ctrl.waterIntake == null ? -1 : WaterIntake.values.indexOf(ctrl.waterIntake!);
    final stressIndex = ctrl.stressLevel == null ? -1 : MoodLevel.values.indexOf(ctrl.stressLevel!);
    final activityIndex = ctrl.activityLevel == null ? -1 : ActivityLevel.values.indexOf(ctrl.activityLevel!);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          const Text(
            'Tell us about your daily routine',
            style: TextStyle(fontSize: 23, fontWeight: FontWeight.w800, height: 1.2),
          ),
          const SizedBox(height: 6),
          Text(
            'Optional \u2014 helps us personalise suggestions. You can update these anytime.',
            style: TextStyle(fontSize: 14.5, height: 1.5, color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 20),
          Expanded(
            child: SingleChildScrollView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _SectionLabel(icon: Icons.bedtime_outlined, label: 'Typical sleep'),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final (hours, label) in _sleepOptions) ...[
                          ChoiceChip(
                            label: Text(label),
                            selected: ctrl.sleepHours != null && (ctrl.sleepHours! - hours).abs() < 0.9,
                            onSelected: (_) => ctrl.setRoutine(sleepHours: hours),
                          ),
                        ],
                      ],
                    ),
                  ),
                  _SectionLabel(icon: Icons.directions_run_rounded, label: 'Daily activity'),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (var i = 0; i < ActivityLevel.values.length; i++) ...[
                          ChoiceChip(
                            label: Text(ActivityLevel.values[i].label),
                            selected: activityIndex == i,
                            onSelected: (_) => ctrl.setRoutine(activityLevel: ActivityLevel.values[i]),
                          ),
                        ],
                      ],
                    ),
                  ),
                  _SectionLabel(icon: Icons.water_drop_outlined, label: 'Water intake per day'),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (var i = 0; i < WaterIntake.values.length; i++) ...[
                          ChoiceChip(
                            label: Text(WaterIntake.values[i].label),
                            selected: waterIndex == i,
                            onSelected: (_) => ctrl.setRoutine(waterIntake: WaterIntake.values[i]),
                          ),
                        ],
                      ],
                    ),
                  ),
                  _SectionLabel(icon: Icons.self_improvement_outlined, label: 'Stress level'),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (var i = 0; i < MoodLevel.values.length; i++) ...[
                          ChoiceChip(
                            label: Text(MoodLevel.values[i].label),
                            selected: stressIndex == i,
                            onSelected: (_) => ctrl.setRoutine(stressLevel: MoodLevel.values[i]),
                          ),
                        ],
                      ],
                    ),
                  ),
                  if (Theme.of(context).platform == TargetPlatform.android) const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 2),
      child: Row(
        children: [
          Icon(icon, size: 18, color: scheme.primary),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}