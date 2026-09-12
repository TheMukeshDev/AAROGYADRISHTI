/// Phase 6 models: AI preventive lifestyle coach.
///
/// Mirrors `app/schemas/coach.py`. The coach only ever sees aggregate data;
/// `safetyApplied` flags whether the provider sanitised the reply.
library;

class CoachConversation {
  final int id;
  final int userId;
  final String title;
  final DateTime createdAt;

  const CoachConversation({required this.id, required this.userId, required this.title, required this.createdAt});

  factory CoachConversation.fromJson(Map<String, dynamic> json) => CoachConversation(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        title: json['title'] as String? ?? 'Coach chat',
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class CoachConversationList {
  final List<CoachConversation> conversations;
  final int count;

  const CoachConversationList({required this.conversations, required this.count});

  factory CoachConversationList.fromJson(Map<String, dynamic> json) => CoachConversationList(
        conversations: (json['conversations'] as List<dynamic>? ?? [])
            .map((e) => CoachConversation.fromJson(e as Map<String, dynamic>))
            .toList(),
        count: json['count'] as int? ?? 0,
      );
}

class CoachMessage {
  final int id;
  final int conversationId;
  final String role; // user | assistant
  final String content;
  final String provider;
  final bool safetyApplied;
  final DateTime createdAt;

  const CoachMessage({
    required this.id,
    required this.conversationId,
    required this.role,
    required this.content,
    required this.provider,
    required this.safetyApplied,
    required this.createdAt,
  });

  bool get isUser => role == 'user';

  factory CoachMessage.fromJson(Map<String, dynamic> json) => CoachMessage(
        id: json['id'] as int,
        conversationId: json['conversation_id'] as int,
        role: json['role'] as String,
        content: json['content'] as String,
        provider: json['provider'] as String? ?? 'deterministic',
        safetyApplied: json['safety_applied'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class CoachMessageList {
  final List<CoachMessage> messages;
  final int count;

  const CoachMessageList({required this.messages, required this.count});

  factory CoachMessageList.fromJson(Map<String, dynamic> json) => CoachMessageList(
        messages: (json['messages'] as List<dynamic>? ?? [])
            .map((e) => CoachMessage.fromJson(e as Map<String, dynamic>))
            .toList(),
        count: json['count'] as int? ?? 0,
      );
}

class CoachReply {
  final int conversationId;
  final CoachMessage reply;
  final String provider;

  const CoachReply({required this.conversationId, required this.reply, required this.provider});

  factory CoachReply.fromJson(Map<String, dynamic> json) => CoachReply(
        conversationId: json['conversation_id'] as int,
        reply: CoachMessage.fromJson(json['reply'] as Map<String, dynamic>),
        provider: json['provider'] as String? ?? 'deterministic',
      );
}

class NextAction {
  final String actionType;
  final String heading;
  final String reason;

  const NextAction({required this.actionType, required this.heading, required this.reason});

  factory NextAction.fromJson(Map<String, dynamic> json) => NextAction(
        actionType: json['action_type'] as String,
        heading: json['heading'] as String? ?? '',
        reason: json['reason'] as String? ?? '',
      );
}

class WeeklySummary {
  final int windowDays;
  final int daysTracked;
  final double completionRate;
  final Map<String, dynamic> averages;
  final int experimentsCompletedTotal;
  final String generatedOn;
  final String narrative;

  const WeeklySummary({
    required this.windowDays,
    required this.daysTracked,
    required this.completionRate,
    required this.averages,
    required this.experimentsCompletedTotal,
    required this.generatedOn,
    required this.narrative,
  });

  factory WeeklySummary.fromJson(Map<String, dynamic> json) => WeeklySummary(
        windowDays: json['window_days'] as int? ?? 0,
        daysTracked: json['days_tracked'] as int? ?? 0,
        completionRate: (json['completion_rate'] as num?)?.toDouble() ?? 0,
        averages: json['averages'] as Map<String, dynamic>? ?? const {},
        experimentsCompletedTotal: json['experiments_completed_total'] as int? ?? 0,
        generatedOn: json['generated_on'] as String? ?? '',
        narrative: json['narrative'] as String? ?? '',
      );
}