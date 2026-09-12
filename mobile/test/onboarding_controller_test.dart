/// OnboardingController unit tests (pure Dart state machine).
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/onboarding/onboarding_controller.dart';
import 'package:mobile/models/app_enums.dart';

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

  group('profile state', () {
    test('setGoal + setProfile drive profileValid', () {
      final c = OnboardingController();
      expect(c.profileValid, isFalse);
      c.setGoal(PrimaryGoal.betterSleep);
      expect(c.profileValid, isFalse);
      c.setProfile(ageGroup: '25_34', activityLevel: ActivityLevel.lightlyActive, gender: 'male');
      expect(c.profileValid, isTrue);
      expect(c.ageGroup, '25_34');
      expect(c.gender, 'male');
      expect(c.activityLevel, ActivityLevel.lightlyActive);
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