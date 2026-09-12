/// Personal learning profile repository (Phase 5).
library;

import '../../core/constants/app_constants.dart';
import '../../core/network/api_client.dart';
import '../models/learning.dart';

class LearningRepository {
  LearningRepository(this._api);
  final ApiClient _api;

  String get _prefix => '${AppConstants.apiV1Prefix}/learnings/personal';

  Future<PersonalLearningSummary> summary() async {
    final data = await _api.get('$_prefix/summary');
    return PersonalLearningSummary.fromJson(data as Map<String, dynamic>);
  }

  Future<PersonalLearningList> list({bool includeDismissed = false}) async {
    final data = await _api.get(_prefix, query: {'include_dismissed': includeDismissed});
    return PersonalLearningList.fromJson(data as Map<String, dynamic>);
  }

  Future<PersonalLearningDetail> detail(int learningId) async {
    final data = await _api.get('$_prefix/$learningId');
    return PersonalLearningDetail.fromJson(data as Map<String, dynamic>);
  }

  Future<PersonalLearningRecalc> recalculate() async {
    final data = await _api.post(_prefix);
    return PersonalLearningRecalc.fromJson(data as Map<String, dynamic>);
  }

  Future<DismissReopenResponse> dismiss(int learningId) async {
    final data = await _api.delete('$_prefix/$learningId');
    return DismissReopenResponse.fromJson(data as Map<String, dynamic>);
  }

  Future<DismissReopenResponse> reopen(int learningId) async {
    final data = await _api.patch('$_prefix/$learningId');
    return DismissReopenResponse.fromJson(data as Map<String, dynamic>);
  }
}