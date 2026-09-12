/// Basic profile screen (age group, gender, activity level, height, weight).
///
/// Changes are written directly to the controller so the parent flow's
/// "Continue" button can advance without an extra tap.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/app_enums.dart';
import '../../widgets/checkin_option.dart';
import 'onboarding_controller.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  static const _ageGroups = [
    ('under_18', 'Under 18'),
    ('18_24', '18 - 24'),
    ('25_34', '25 - 34'),
    ('35_44', '35 - 44'),
    ('45_54', '45 - 54'),
    ('55_64', '55 - 64'),
    ('65_plus', '65 +'),
  ];

  static const _genders = [
    ('female', 'Female'),
    ('male', 'Male'),
    ('non_binary', 'Non-binary'),
    ('prefer_not_to_say', 'Prefer not to say'),
  ];

  @override
  Widget build(BuildContext context) {
    final ctrl = context.watch<OnboardingController>();
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          const Text(
            'Tell us a little about yourself',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 6),
          Text(
            'All fields are optional. Only share what you are comfortable with.',
            style: TextStyle(fontSize: 14.5, color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 18),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _sectionTitle('Age group'),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: _ageGroups.map((e) {
                      final wire = e.$1;
                      final label = e.$2;
                      return ChoiceChip(
                        label: Text(label),
                        selected: ctrl.ageGroup == wire,
                        onSelected: (_) => ctrl.setProfile(ageGroup: wire, activityLevel: ctrl.activityLevel, gender: ctrl.gender),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  _sectionTitle('Gender (optional)'),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: _genders.map((e) {
                      final wire = e.$1;
                      final label = e.$2;
                      return ChoiceChip(
                        label: Text(label),
                        selected: ctrl.gender == wire,
                        onSelected: (_) => ctrl.setProfile(ageGroup: ctrl.ageGroup, activityLevel: ctrl.activityLevel, gender: wire),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  _sectionTitle('Daily activity level'),
                  ...ActivityLevel.values.map((level) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: CheckinOption(
                          label: level.label,
                          selected: ctrl.activityLevel == level,
                          onTap: () => ctrl.setProfile(
                            ageGroup: ctrl.ageGroup,
                            activityLevel: level,
                            gender: ctrl.gender,
                          ),
                        ),
                      )),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 8, top: 4),
        child: Text(text, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
      );
}