/// Daily check-in log model (mirrors backend `DailyLogResponse`).
///
/// Unknown/missing values are `null`, never fabricated as zero - this is a
/// core Phase 1 data-quality rule.
library;

import 'app_enums.dart';
import '../core/utils/date_utils.dart';

class DailyLog {
  final int id;
  final int userId;
  final DateTime date;

  final double? sleepHours;
  final SleepQuality? sleepQuality;

  final int? steps;
  final int? activeMinutes;
  final int? exerciseMinutes;
  final ExerciseLevel? exerciseLevel;

  final double? waterLiters;
  final MealQuality? mealQuality;

  final int? screenTimeMinutes;
  final bool? lateNightScreen;

  final CaffeineLevel? caffeine;

  final MoodLevel? mood;
  final int? energy;
  final int? stress;

  final String? source;

  const DailyLog({
    required this.id,
    required this.userId,
    required this.date,
    this.sleepHours,
    this.sleepQuality,
    this.steps,
    this.activeMinutes,
    this.exerciseMinutes,
    this.exerciseLevel,
    this.waterLiters,
    this.mealQuality,
    this.screenTimeMinutes,
    this.lateNightScreen,
    this.caffeine,
    this.mood,
    this.energy,
    this.stress,
    this.source,
  });

  factory DailyLog.fromJson(Map<String, dynamic> json) => DailyLog(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        date: DateTime.parse(json['date'] as String),
        sleepHours: (json['sleep_hours'] as num?)?.toDouble(),
        sleepQuality: SleepQuality.fromWire(json['sleep_quality'] as String?),
        steps: json['steps'] as int?,
        activeMinutes: json['active_minutes'] as int?,
        exerciseMinutes: json['exercise_minutes'] as int?,
        exerciseLevel: ExerciseLevel.fromWire(json['exercise_level'] as String?),
        waterLiters: (json['water_liters'] as num?)?.toDouble(),
        mealQuality: MealQuality.fromWire(json['meal_quality'] as String?),
        screenTimeMinutes: json['screen_time_minutes'] as int?,
        lateNightScreen: json['late_night_screen'] as bool?,
        caffeine: CaffeineLevel.fromWire(json['caffeine'] as String?),
        mood: MoodLevel.fromWire(json['mood'] as String?),
        energy: json['energy'] as int?,
        stress: json['stress'] as int?,
        source: json['source'] as String?,
      );

  String get displayDate => AppDateUtils.shortDay(date);

  bool get isDemo => source == 'demo';
  bool get isPartial => energy == null && stress == null;

  /// Subjective portion score (0..10) is NOT an AI score - simply whether the
  /// user completed the manual part of the check-in.
  int get answeredCount => [
        energy,
        stress,
        mood,
        mealQuality,
        waterLiters,
        sleepHours,
        exerciseLevel,
      ].where((e) => e != null).length;
}