/// Health connection and sync repository.
library;

import '../../core/constants/app_constants.dart';
import '../../core/network/api_client.dart';
import '../../models/health_data.dart';

class HealthRepository {
  HealthRepository(this._api);
  final ApiClient _api;

  String get _prefix => '${AppConstants.apiV1Prefix}/health';

  Future<HealthConnectionState> getStatus() async {
    final data = await _api.get('$_prefix/status');
    if (data == null) return const HealthConnectionState();
    return HealthConnectionState.fromJson(data as Map<String, dynamic>);
  }

  Future<HealthConnectionState> connect({
    required bool steps,
    required bool sleep,
    required bool activity,
  }) async {
    final data = await _api.post(
      '$_prefix/connect',
      body: {'provider': 'health_connect', 'steps_enabled': steps, 'sleep_enabled': sleep, 'activity_enabled': activity},
    );
    return HealthConnectionState.fromJson(data as Map<String, dynamic>);
  }

  Future<void> sync({int? steps, int? activeMinutes, int? sleepMinutes, String? date}) async {
    await _api.post(
      '$_prefix/sync',
      body: {'steps': steps, 'active_minutes': activeMinutes, 'sleep_minutes': sleepMinutes, 'date': date},
    );
  }

  Future<DashboardData> dashboardToday() async {
    final data = await _api.get('${AppConstants.apiV1Prefix}/dashboard/today');
    return DashboardData.fromJson(data as Map<String, dynamic>);
  }

  Future<BaselineInfo> baseline() async {
    final data = await _api.get('${AppConstants.apiV1Prefix}/dashboard/baseline');
    return BaselineInfo.fromJson(data as Map<String, dynamic>);
  }
}