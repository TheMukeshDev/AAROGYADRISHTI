/// Health Connect integration (Android).
///
/// This service is the ONLY place that touches the `health` plugin. The UI
/// talks to this service (or the HealthRepository) and never imports the
/// health package itself, keeping device code isolated and replaceable.
///
/// Phase 1 reads: steps, sleep, active exercise minutes. Missing values are
/// returned as `null`, never invented. Permission flow is explicit and can
/// always be declined without blocking the rest of the app.
library;

import 'package:flutter/foundation.dart';
import 'package:health/health.dart';

import '../models/health_data.dart';

enum HealthConnectAvailability {
  supported,
  notInstalled,
  notGranted,
  unsupported,
  error,
}

class HealthConnectService {
  HealthConnectService._();

  static final HealthConnectService instance = HealthConnectService._();

  final Health _health = Health();
  bool _configured = false;
  HealthConnectAvailability? _availability;

  bool get isConfigured => _configured;
  HealthConnectAvailability? get availability => _availability;

  /// The three data categories offered in Phase 1 (Steps / Sleep / Activity).
  static const Map<HealthDataType, String> categoryTitles = {
    HealthDataType.STEPS: 'Steps',
    HealthDataType.SLEEP_ASLEEP: 'Sleep',
    HealthDataType.MOVE_MINUTES: 'Activity',
  };

  /// Detects platform + Health Connect availability. Requests nothing.
  Future<HealthConnectAvailability> setup() async {
    try {
      await _health.configure();
      _configured = true;
      if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
        final supported = await _health.isHealthConnectSupported();
        if (!supported) {
          _availability = HealthConnectAvailability.unsupported;
        } else {
          final installed = await _health.isHealthConnectInstalled();
          _availability =
              installed ? HealthConnectAvailability.supported : HealthConnectAvailability.notInstalled;
        }
        return _availability!;
      }
      _availability = HealthConnectAvailability.unsupported;
      return _availability!;
    } catch (_) {
      _availability = HealthConnectAvailability.error;
      return _availability!;
    }
  }

  /// Ask for Health Connect permission (system dialog appears once per type).
  Future<bool> requestPermissions(List<HealthDataType> types) async {
    try {
      if (!_configured) await _health.configure();
      return await _health.requestAuthorization(types);
    } catch (_) {
      return false;
    }
  }

  /// Best-effort check of which types are already granted (no system prompt).
  Future<bool> checkPermissions(List<HealthDataType> types) async {
    try {
      if (!_configured) await _health.configure();
      final result = await _health.hasPermissions(types);
      if (result is bool) return result;
      if (result is Set) return result.length == types.length;
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Read steps between [start] and [end], aggregated to a single count.
  Future<int> readSteps(DateTime start, DateTime end) async {
    final data = await _syncRead(HealthDataType.STEPS, start, end);
    return data.fold<int>(0, (sum, d) => sum + (d.value as num).toInt());
  }

  /// Read active/exercise minutes between [start] and [end].
  Future<int> readActiveMinutes(DateTime start, DateTime end) async {
    final data = await _syncRead(HealthDataType.MOVE_MINUTES, start, end);
    return data.fold<int>(0, (sum, d) => sum + (d.value as num).round());
  }

  /// Read total sleep minutes between [start] and [end].
  Future<int> readSleepMinutes(DateTime start, DateTime end) async {
    final data = await _syncRead(HealthDataType.SLEEP_ASLEEP, start, end);
    return data.fold<int>(0, (sum, d) => sum + (d.value as num).round());
  }

  Future<List<HealthDataPoint>> _syncRead(HealthDataType type, DateTime start, DateTime end) async {
    if (!_configured) await _health.configure();
    return _health.getHealthDataFromTypes(start, end, [type]);
  }

  /// Convenience: read all tracked metrics for a single day.
  ///
  /// Returns a `DailyHealthData` with `null` fields for anything not measured.
  Future<DailyHealthData> readDay(DateTime day) async {
    final start = DateTime(day.year, day.month, day.day);
    final end = start.add(const Duration(days: 1)).subtract(const Duration(seconds: 1));

    int? steps;
    int? active;
    int? sleep;
    try {
      steps = await readSteps(start, end);
    } catch (_) {}
    try {
      active = await readActiveMinutes(start, end);
    } catch (_) {}
    try {
      sleep = await readSleepMinutes(start, end);
    } catch (_) {}
    return DailyHealthData(steps: steps, activeMinutes: active, sleepMinutes: sleep);
  }
}