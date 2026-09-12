/// AI preventive lifestyle coach repository (Phase 6).
library;

import '../../core/constants/app_constants.dart';
import '../../core/network/api_client.dart';
import '../models/coach.dart';

class CoachRepository {
  CoachRepository(this._api);
  final ApiClient _api;

  String get _prefix => '${AppConstants.apiV1Prefix}/coach';

  Future<CoachConversation> createConversation({String title = 'Coach chat'}) async {
    final data = await _api.post('$_prefix/conversations', body: {'title': title});
    return CoachConversation.fromJson(data as Map<String, dynamic>);
  }

  Future<CoachConversationList> conversations() async {
    final data = await _api.get('$_prefix/conversations');
    return CoachConversationList.fromJson(data as Map<String, dynamic>);
  }

  Future<CoachMessageList> messages(int conversationId) async {
    final data = await _api.get('$_prefix/conversations/$conversationId/messages');
    return CoachMessageList.fromJson(data as Map<String, dynamic>);
  }

  Future<CoachReply> send(int conversationId, String content) async {
    final data = await _api.post('$_prefix/conversations/$conversationId/messages', body: {
      'content': content,
    });
    return CoachReply.fromJson(data as Map<String, dynamic>);
  }

  Future<NextAction> nextAction() async {
    final data = await _api.get('$_prefix/next-action');
    return NextAction.fromJson(data as Map<String, dynamic>);
  }

  Future<WeeklySummary> weeklySummary() async {
    final data = await _api.get('$_prefix/weekly-summary');
    return WeeklySummary.fromJson(data as Map<String, dynamic>);
  }
}