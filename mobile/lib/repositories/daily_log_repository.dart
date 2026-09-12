/// Daily check-in repository.
library;

import '../../core/constants/app_constants.dart';
import '../../core/network/api_client.dart';
import '../../models/daily_log.dart';

class DailyLogRepository {
  DailyLogRepository(this._api);
  final ApiClient _api;

  String get _prefix => '${AppConstants.apiV1Prefix}/daily-logs';

  Future<DailyLog> create(Map<String, dynamic> fields) async {
    final data = await _api.post(_prefix, body: fields);
    return DailyLog.fromJson(data as Map<String, dynamic>);
  }

  Future<DailyLog> update(String date, Map<String, dynamic> fields) async {
    final data = await _api.put('$_prefix/$date', body: fields);
    return DailyLog.fromJson(data as Map<String, dynamic>);
  }

  Future<DailyLog?> getByDate(String date) async {
    try {
      final data = await _api.get('$_prefix/$date');
      return DailyLog.fromJson(data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<List<DailyLog>> list({int limit = 90, String? start, String? end}) async {
    final query = <String, dynamic>{'limit': limit};
    if (start != null) query['start'] = start;
    if (end != null) query['end'] = end;
    final data = await _api.get(_prefix, query: query);
    return (data as List<dynamic>)
        .map((e) => DailyLog.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}