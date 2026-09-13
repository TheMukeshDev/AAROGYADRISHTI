/// Onboarding goal selection screen.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../models/app_enums.dart';
import '../../widgets/checkin_option.dart';
import 'onboarding_controller.dart';

class GoalScreen extends StatelessWidget {
  const GoalScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<OnboardingController>();
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Text(
            AppStrings.goalTitle,
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 6),
          Text(
            AppStrings.goalSubtitle,
            style: TextStyle(fontSize: 15, color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView.separated(
              itemCount: PrimaryGoal.values.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final goal = PrimaryGoal.values[i];
                return CheckinOption(
                  label: goal.label,
                  icon: goal.icon,
                  selected: controller.goal == goal,
                  onTap: () => controller.setGoal(goal),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}