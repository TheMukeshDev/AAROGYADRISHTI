/// Aggregated dashboard view models.
library;

class DashboardSummary {
  final DateTime date;
  final double? sleepHours;
  final String? sleepQuality;
  final int? steps;
  final int? activeMinutes;
  final double? waterLiters;
  final int? energy;
  final int? stress;

  const DashboardSummary({
    required this.date,
    this.sleepHours,
    this.sleepQuality,
    this.steps,
    this.activeMinutes,
    this.waterLiters,
    this.energy,
    this.stress,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) => DashboardSummary(
        date: DateTime.parse(json['date'] as String),
        sleepHours: (json['sleep_hours'] as num?)?.toDouble(),
        sleepQuality: json['sleep_quality'] as String?,
        steps: json['steps'] as int?,
        activeMinutes: json['active_minutes'] as int?,
        waterLiters: (json['water_liters'] as num?)?.toDouble(),
        energy: json['energy'] as int?,
        stress: json['stress'] as int?,
      );
}