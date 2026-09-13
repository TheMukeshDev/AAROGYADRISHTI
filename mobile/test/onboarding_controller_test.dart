/// OnboardingController unit tests (pure Dart state machine).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:aarogyadrishti/features/onboarding/onboarding_controller.dart';
import 'package:aarogyadrishti/models/app_enums.dart';

void main() {
  group('steps', () {
    test('starts at 0 and advances to max 2', () {
      final c = OnboardingController();
      expect(c.step, 0);
      c.next();
      expect(c.step, 1);
      c.next();
      expect(c.step, 2);
      expect(c.isLast, isTrue);
      c.next();
      expect(c.step, 2);
    });

    test('back clamps at 0', () {
      final c = OnboardingController();
      c.back();
      expect(c.step, 0);
      c.next();
      c.back();
      expect(c.step, 0);
    });
  });

  group('goals (multi-select)', () {
    test('toggleGoal adds and removes while keeping other selections', () {
      final c = OnboardingController();
      expect(c.goalsSelected, isFalse);

      c.toggleGoal(PrimaryGoal.betterSleep);
      c.toggleGoal(PrimaryGoal.hydration);
      expect(c.goals.length, 2);
      expect(c.goalsSelected, isTrue);

      // Deselect one goal; the other must remain selected.
      c.toggleGoal(PrimaryGoal.betterSleep);
      expect(c.goals, [PrimaryGoal.hydration]);
      expect(c.goalsSelected, isTrue);

      // Deselect the last goal -> nothing selected, continue disabled.
      c.toggleGoal(PrimaryGoal.hydration);
      expect(c.goals, isEmpty);
      expect(c.goalsSelected, isFalse);
    });

    test('setGoals replaces the full selection and can be empty', () {
      final c = OnboardingController()..setGoals([PrimaryGoal.betterSleep, PrimaryGoal.moreEnergy]);
      expect(c.goals.length, 2);
      c.setGoals([]);
      expect(c.goalsSelected, isFalse);
    });
  });

  group('health selection', () {
    test('setHealthSelection replaces selection', () {
      final c = OnboardingController();
      c.setHealthSelection([
        HealthDataTypeWrapper(type: 'steps', title: 'Steps', description: ''),
        HealthDataTypeWrapper(type: 'sleep', title: 'Sleep', description: ''),
      ]);
      expect(c.selectedHealth.length, 2);
      c.setHealthSelection(const []);
      expect(c.selectedHealth, isEmpty);
    });
  });
}