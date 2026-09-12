/// Enum wire-value round-trip tests.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/models/app_enums.dart';

void main() {
  group('PrimaryGoal', () {
    test('fromWire round-trips every wire value', () {
      for (final g in PrimaryGoal.values) {
        expect(PrimaryGoal.fromWire(g.wire), g);
      }
    });
    test('fromWire returns null for unknown', () {
      expect(PrimaryGoal.fromWire('bogus'), isNull);
    });
    test('firstOrNull extension works on empty list', () {
      expect(<PrimaryGoal>[].firstOrNull, isNull);
    });
  });

  group('ActivityLevel', () {
    test('round-trips and labels', () {
      expect(ActivityLevel.fromWire('mostly_sedentary'), ActivityLevel.mostlySedentary);
      expect(ActivityLevel.mostlySedentary.label, 'Mostly sedentary');
      expect(ActivityLevel.fromWire('nope'), isNull);
    });
  });

  group('ExerciseLevel', () {
    test('maps minutes', () {
      expect(ExerciseLevel.fromWire('none')?.minutes, 0);
      expect(ExerciseLevel.fromWire('light')?.minutes, 15);
      expect(ExerciseLevel.fromWire('moderate')?.minutes, 30);
      expect(ExerciseLevel.fromWire('intense')?.minutes, 60);
      expect(ExerciseLevel.fromWire('x'), isNull);
    });
  });

  group('MealQuality / WaterIntake / MoodLevel / CaffeineLevel / SleepQuality', () {
    test('all round-trip', () {
      for (final m in MealQuality.values) {
        expect(MealQuality.fromWire(m.wire), m);
      }
      for (final w in WaterIntake.values) {
        expect(WaterIntake.fromWire(w.wire), w);
      }
      for (final m in MoodLevel.values) {
        expect(MoodLevel.fromWire(m.wire), m);
      }
      for (final c in CaffeineLevel.values) {
        expect(CaffeineLevel.fromWire(c.wire), c);
      }
      for (final s in SleepQuality.values) {
        expect(SleepQuality.fromWire(s.wire), s);
      }
    });
  });
}