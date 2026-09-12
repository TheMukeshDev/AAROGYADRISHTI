/// Model parsing tests - focus on the "unknown values stay null" invariant.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/models/daily_log.dart';
import 'package:mobile/models/health_data.dart';

void main() {
  group('DailyLog.fromJson', () {
    test('parses full log', () {
      final log = DailyLog.fromJson({
        'id': 1,
        'user_id': 42,
        'date': '2026-09-11',
        'sleep_hours': 7.5,
        'sleep_quality': 'good',
        'steps': 12000,
        'active_minutes': 45,
        'exercise_minutes': 30,
        'exercise_level': 'moderate',
        'water_liters': 2.5,
        'meal_quality': 'mixed',
        'late_night_screen': false,
        'caffeine': 'low',
        'mood': 'good',
        'energy': 8,
        'stress': 2,
        'source': 'manual',
      });
      expect(log.date, DateTime(2026, 9, 11));
      expect(log.sleepHours, 7.5);
      expect(log.sleepQuality, SleepQuality.good);
      expect(log.exerciseLevel, ExerciseLevel.moderate);
      expect(log.isDemo, isFalse);
      expect(log.isPartial, isFalse);
      expect(log.answeredCount, 8);
    });

    test('unknown values stay null (never fabricated)', () {
      final log = DailyLog.fromJson({
        'id': 2,
        'user_id': 1,
        'date': '2026-09-11',
        'source': 'demo',
      });
      expect(log.sleepHours, isNull);
      expect(log.steps, isNull);
      expect(log.waterLiters, isNull);
      expect(log.energy, isNull);
      expect(log.stress, isNull);
      expect(log.mood, isNull);
      expect(log.answeredCount, 0);
      expect(log.isDemo, isTrue);
      expect(log.isPartial, isTrue);
    });
  });

  group('DashboardData.fromJson', () {
    test('parses summary + baseline', () {
      final data = DashboardData.fromJson({
        'has_data': true,
        'summary': {
          'date': '2026-09-11',
          'sleep_hours': 7.2,
          'energy': 7,
          'stress': 3,
          'water_liters': 2.1,
        },
        'baseline': {
          'status': 'building',
          'days_recorded': 3,
          'target_days': 7,
          'consecutive_days': 3,
          'message': 'Keep going',
        },
      });
      expect(data.hasData, isTrue);
      expect(data.summary?.sleepHours, 7.2);
      expect(data.summary?.energy, 7);
      expect(data.baseline.isReady, isFalse);
      expect(data.baseline.remainingDays, 4);
    });

    test('empty dashboard tolerates missing summary', () {
      final data = DashboardData.fromJson({
        'has_data': false,
        'baseline': {
          'status': 'getting_started',
          'days_recorded': 0,
          'target_days': 7,
          'consecutive_days': 0,
          'message': '',
        },
      });
      expect(data.summary, isNull);
      expect(data.baseline.isReady, isFalse);
    });
  });

  group('HealthConnectionState / DailyHealthData', () {
    test('isConnected reflects any enabled source', () {
      const none = HealthConnectionState();
      expect(none.isConnected, isFalse);
      const steps = HealthConnectionState(stepsEnabled: true);
      expect(steps.isConnected, isTrue);
    });

    test('sleep hours derived from minutes', () {
      const day = DailyHealthData(sleepMinutes: 450);
      expect(day.sleepHours, 7.5);
      const empty = DailyHealthData();
      expect(empty.sleepHours, isNull);
    });
  });
}