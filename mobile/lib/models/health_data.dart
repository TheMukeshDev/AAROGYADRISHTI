/// Health data models.
///
/// - `DailyHealthData` is a raw observation synced from a device.
/// - `HealthConnectionState` describes what the user has authorised.
library;

import 'dashboard.dart' show DashboardSummary;

class DailyHealthData {
  final int? steps;
  final int? activeMinutes;
  final int? sleepMinutes;
  final String source;

  const DailyHealthData({
    this.steps,
    this.activeMinutes,
    this.sleepMinutes,
    this.source = 'health_connect',
  });

  // Device-computed sleep hours (rounded to 1 decimal) for display.
  double? get sleepHours => sleepMinutes == null ? null : (sleepMinutes! / 60);
}

class HealthConnectionState {
  final String provider;
  final bool stepsEnabled;
  final bool sleepEnabled;
  final bool activityEnabled;
  final DateTime? lastSyncedAt;

  const HealthConnectionState({
    this.provider = 'health_connect',
    this.stepsEnabled = false,
    this.sleepEnabled = false,
    this.activityEnabled = false,
    this.lastSyncedAt,
  });

  bool get isConnected => stepsEnabled || sleepEnabled || activityEnabled;

  factory HealthConnectionState.fromJson(Map<String, dynamic> json) =>
      HealthConnectionState(
        provider: json['provider'] as String? ?? 'health_connect',
        stepsEnabled: json['steps_enabled'] as bool? ?? false,
        sleepEnabled: json['sleep_enabled'] as bool? ?? false,
        activityEnabled: json['activity_enabled'] as bool? ?? false,
        lastSyncedAt: json['last_synced_at'] != null
            ? DateTime.tryParse(json['last_synced_at'] as String)
            : null,
      );
}

class DashboardData {
  final bool hasData;
  final DashboardSummary? summary;
  final BaselineInfo baseline;

  const DashboardData({required this.hasData, this.summary, required this.baseline});

  factory DashboardData.fromJson(Map<String, dynamic> json) => DashboardData(
        hasData: json['has_data'] as bool? ?? false,
        summary: json['summary'] != null
            ? DashboardSummary.fromJson(json['summary'] as Map<String, dynamic>)
            : null,
        baseline: BaselineInfo.fromJson(json['baseline'] as Map<String, dynamic>),
      );
}

class BaselineInfo {
  final String status;
  final int daysRecorded;
  final int targetDays;
  final int consecutiveDays;
  final String message;
  final DateTime? firstDay;
  final DateTime? lastDay;

  const BaselineInfo({
    required this.status,
    required this.daysRecorded,
    required this.targetDays,
    required this.consecutiveDays,
    required this.message,
    this.firstDay,
    this.lastDay,
  });

  bool get isReady => status == 'ready';
  int get remainingDays => (targetDays - daysRecorded).clamp(0, targetDays);

  factory BaselineInfo.fromJson(Map<String, dynamic> json) => BaselineInfo(
        status: json['status'] as String,
        daysRecorded: json['days_recorded'] as int? ?? 0,
        targetDays: json['target_days'] as int? ?? 7,
        consecutiveDays: json['consecutive_days'] as int? ?? 0,
        message: json['message'] as String? ?? '',
        firstDay: json['first_day'] != null ? DateTime.tryParse(json['first_day'] as String) : null,
        lastDay: json['last_day'] != null ? DateTime.tryParse(json['last_day'] as String) : null,
      );
}