/// Experiment engine + evaluation repository (Phase 3 + Phase 4).
library;

import '../../core/constants/app_constants.dart';
import '../../core/network/api_client.dart';
import '../../core/utils/date_utils.dart';
import '../models/experiment.dart';

class ExperimentRepository {
  ExperimentRepository(this._api);
  final ApiClient _api;

  String get _prefix => '${AppConstants.apiV1Prefix}/experiments';
  String get _candidatesPrefix => '${AppConstants.apiV1Prefix}/learning-candidates';

  Future<List<ExperimentTemplate>> templates() async {
    final data = await _api.get('${AppConstants.apiV1Prefix}/experiment-templates');
    return (data as List<dynamic>)
        .map((e) => ExperimentTemplate.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RecommendationResponse> recommended() async {
    final data = await _api.get('$_prefix/recommended');
    return RecommendationResponse.fromJson(data as Map<String, dynamic>);
  }

  Future<Experiment> start(String experimentType) async {
    final data = await _api.post(_prefix, body: {'experiment_type': experimentType});
    return Experiment.fromJson(data as Map<String, dynamic>);
  }

  Future<ActiveExperimentResponse> active() async {
    final data = await _api.get('$_prefix/active');
    return ActiveExperimentResponse.fromJson(data as Map<String, dynamic>);
  }

  Future<List<ExperimentHistoryItem>> history() async {
    final data = await _api.get('$_prefix/history');
    return (data as List<dynamic>)
        .map((e) => ExperimentHistoryItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ExperimentDetail> detail(int experimentId) async {
    final data = await _api.get('$_prefix/$experimentId');
    return ExperimentDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<ExperimentDailyLog> recordDailyLog(
    int experimentId, {
    DateTime? date,
    bool completed = true,
    bool? targetMet,
    String? notes,
    Map<String, dynamic>? metrics,
  }) async {
    final body = <String, dynamic>{
      'date': date == null ? AppDateUtils.todayIso() : AppDateUtils.toIso(date),
      'completed': completed,
      if (targetMet != null) 'target_met': targetMet,
      if (notes != null && notes.trim().isNotEmpty) 'notes': notes.trim(),
      if (metrics != null && metrics.isNotEmpty) 'metrics': metrics,
    };
    final data = await _api.post('$_prefix/$experimentId/daily-log', body: body);
    return ExperimentDailyLog.fromJson(data as Map<String, dynamic>);
  }

  Future<ExperimentResult> complete(int experimentId) async {
    final data = await _api.post('$_prefix/$experimentId/complete');
    return ExperimentResult.fromJson(data as Map<String, dynamic>);
  }

  Future<Experiment> cancel(int experimentId) async {
    final data = await _api.post('$_prefix/$experimentId/cancel');
    return Experiment.fromJson(data as Map<String, dynamic>);
  }

  Future<ExperimentResult> result(int experimentId) async {
    final data = await _api.get('$_prefix/$experimentId/result');
    return ExperimentResult.fromJson(data as Map<String, dynamic>);
  }

  Future<ExperimentResult> evaluate(int experimentId) async {
    final data = await _api.post('$_prefix/$experimentId/evaluate');
    return ExperimentResult.fromJson(data as Map<String, dynamic>);
  }

  Future<List<MetricComparison>> metrics(int experimentId) async {
    final data = await _api.get('$_prefix/$experimentId/metrics');
    return (data as List<dynamic>)
        .map((e) => MetricComparison.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ExperimentEvidence?> evidence(int experimentId) async {
    try {
      final data = await _api.get('$_prefix/$experimentId/evidence');
      return ExperimentEvidence.fromJson(data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<LearningCandidate?> learningCandidateFor(int experimentId) async {
    try {
      final data = await _api.get('$_prefix/$experimentId/learning-candidate');
      if (data == null) return null;
      return LearningCandidate.fromJson(data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<LearningCandidateList> candidates() async {
    final data = await _api.get(_candidatesPrefix);
    return LearningCandidateList.fromJson(data as Map<String, dynamic>);
  }

  Future<MessageResponse> acceptCandidate(int candidateId) async {
    final data = await _api.post('$_candidatesPrefix/$candidateId/accept');
    return MessageResponse.fromJson(data as Map<String, dynamic>);
  }

  Future<MessageResponse> rejectCandidate(int candidateId) async {
    final data = await _api.post('$_candidatesPrefix/$candidateId/reject');
    return MessageResponse.fromJson(data as Map<String, dynamic>);
  }
}