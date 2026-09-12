/// User profile model (mirrors backend `ProfileResponse`).
library;

import 'app_enums.dart';

class UserProfile {
  final int id;
  final int userId;
  final String? name;
  final String? ageGroup;
  final String? gender;
  final double? heightCm;
  final double? weightKg;
  final String? activityLevelWire;
  final String? primaryGoalWire;
  final bool onboardingCompleted;
  final DateTime? timeframeStart;

  const UserProfile({
    required this.id,
    required this.userId,
    this.name,
    this.ageGroup,
    this.gender,
    this.heightCm,
    this.weightKg,
    this.activityLevelWire,
    this.primaryGoalWire,
    this.onboardingCompleted = false,
    this.timeframeStart,
  });

  PrimaryGoal? get primaryGoal => PrimaryGoal.fromWire(primaryGoalWire);
  ActivityLevel? get activityLevel => ActivityLevel.fromWire(activityLevelWire);
  bool get isOnboarded => onboardingCompleted;

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        name: json['name'] as String?,
        ageGroup: json['age_group'] as String?,
        gender: json['gender'] as String?,
        heightCm: (json['height_cm'] as num?)?.toDouble(),
        weightKg: (json['weight_kg'] as num?)?.toDouble(),
        activityLevelWire: json['activity_level'] as String?,
        primaryGoalWire: json['primary_goal'] as String?,
        onboardingCompleted: json['onboarding_completed'] as bool? ?? false,
        timeframeStart: json['timeframe_start'] != null
            ? DateTime.tryParse(json['timeframe_start'] as String)
            : null,
      );

  UserProfile copyWith({
    String? name,
    String? ageGroup,
    String? gender,
    double? heightCm,
    double? weightKg,
    String? activityLevelWire,
    String? primaryGoalWire,
    bool? onboardingCompleted,
    bool clearName = false,
    bool clearHeight = false,
    bool clearWeight = false,
    bool clearAgeGroup = false,
    bool clearGender = false,
  }) =>
      UserProfile(
        id: id,
        userId: userId,
        name: clearName ? null : (name ?? this.name),
        ageGroup: clearAgeGroup ? null : (ageGroup ?? this.ageGroup),
        gender: clearGender ? null : (gender ?? this.gender),
        heightCm: clearHeight ? null : (heightCm ?? this.heightCm),
        weightKg: clearWeight ? null : (weightKg ?? this.weightKg),
        activityLevelWire: activityLevelWire ?? this.activityLevelWire,
        primaryGoalWire: primaryGoalWire ?? this.primaryGoalWire,
        onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
        timeframeStart: timeframeStart,
      );
}