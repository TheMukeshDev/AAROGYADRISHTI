/// Phase 5 models: "What Works For Me" personal learning profile.
///
/// Mirrors `app/schemas/learning.py`. Every record is an observed correlation,
/// never a proof of cause and effect.
library;

class PersonalLearning {
  final int id;
  final int userId;
  final String patternType;
  final String intervention;
  final String? targetMetric;
  final String state; // proposed | confirmed | dismissed
  final String evidenceLevel;
  final String evidenceState; // positive | mixed | neutral | negative | insufficient
  final double? consistencyScore;
  final int sampleSize;
  final String? hypothesis;
  final String? summary;
  final bool causalityProven;
  final DateTime createdAt;
  final DateTime updatedAt;

  const PersonalLearning({
    required this.id,
    required this.userId,
    required this.patternType,
    required this.intervention,
    required this.targetMetric,
    required this.state,
    required this.evidenceLevel,
    required this.evidenceState,
    required this.consistencyScore,
    required this.sampleSize,
    required this.hypothesis,
    required this.summary,
    required this.causalityProven,
    required this.createdAt,
    required this.updatedAt,
  });

  factory PersonalLearning.fromJson(Map<String, dynamic> json) => PersonalLearning(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        patternType: json['pattern_type'] as String,
        intervention: json['intervention'] as String,
        targetMetric: json['target_metric'] as String?,
        state: json['state'] as String? ?? 'proposed',
        evidenceLevel: json['evidence_level'] as String? ?? 'INSUFFICIENT',
        evidenceState: json['evidence_state'] as String? ?? 'insufficient',
        consistencyScore: (json['consistency_score'] as num?)?.toDouble(),
        sampleSize: json['sample_size'] as int? ?? 0,
        hypothesis: json['hypothesis'] as String?,
        summary: json['summary'] as String?,
        causalityProven: json['causality_proven'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );
}

class PersonalLearningEvidence {
  final int id;
  final int? experimentId;
  final String source;
  final String evidenceLevel;
  final String direction;
  final double? effectMagnitude;
  final Map<String, dynamic>? observedChange;
  final DateTime createdAt;

  const PersonalLearningEvidence({
    required this.id,
    required this.experimentId,
    required this.source,
    required this.evidenceLevel,
    required this.direction,
    required this.effectMagnitude,
    required this.observedChange,
    required this.createdAt,
  });

  factory PersonalLearningEvidence.fromJson(Map<String, dynamic> json) => PersonalLearningEvidence(
        id: json['id'] as int,
        experimentId: json['experiment_id'] as int?,
        source: json['source'] as String? ?? 'candidate',
        evidenceLevel: json['evidence_level'] as String,
        direction: json['direction'] as String? ?? 'no_change',
        effectMagnitude: (json['effect_magnitude'] as num?)?.toDouble(),
        observedChange: json['observed_change'] as Map<String, dynamic>?,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class PersonalLearningDetail {
  final PersonalLearning learning;
  final List<PersonalLearningEvidence> evidence;

  const PersonalLearningDetail({required this.learning, required this.evidence});

  factory PersonalLearningDetail.fromJson(Map<String, dynamic> json) => PersonalLearningDetail(
        learning: PersonalLearning.fromJson(json),
        evidence: (json['evidence'] as List<dynamic>? ?? [])
            .map((e) => PersonalLearningEvidence.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class PersonalLearningList {
  final List<PersonalLearning> learnings;
  final int count;

  const PersonalLearningList({required this.learnings, required this.count});

  factory PersonalLearningList.fromJson(Map<String, dynamic> json) => PersonalLearningList(
        learnings: (json['learnings'] as List<dynamic>? ?? [])
            .map((e) => PersonalLearning.fromJson(e as Map<String, dynamic>))
            .toList(),
        count: json['count'] as int? ?? 0,
      );
}

class PersonalLearningSummary {
  final int total;
  final int proposed;
  final int confirmed;
  final int dismissed;
  final PersonalLearning? topLearning;

  const PersonalLearningSummary({
    required this.total,
    required this.proposed,
    required this.confirmed,
    required this.dismissed,
    required this.topLearning,
  });

  factory PersonalLearningSummary.fromJson(Map<String, dynamic> json) => PersonalLearningSummary(
        total: json['total'] as int? ?? 0,
        proposed: json['proposed'] as int? ?? 0,
        confirmed: json['confirmed'] as int? ?? 0,
        dismissed: json['dismissed'] as int? ?? 0,
        topLearning: json['top_learning'] == null
            ? null
            : PersonalLearning.fromJson(json['top_learning'] as Map<String, dynamic>),
      );
}

class PersonalLearningRecalc {
  final bool recomputed;
  final int count;
  final List<PersonalLearning> learnings;

  const PersonalLearningRecalc({required this.recomputed, required this.count, required this.learnings});

  factory PersonalLearningRecalc.fromJson(Map<String, dynamic> json) => PersonalLearningRecalc(
        recomputed: json['recomputed'] as bool? ?? false,
        count: json['count'] as int? ?? 0,
        learnings: (json['learnings'] as List<dynamic>? ?? [])
            .map((e) => PersonalLearning.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class DismissReopenResponse {
  final String state;
  final String message;

  const DismissReopenResponse({required this.state, required this.message});

  factory DismissReopenResponse.fromJson(Map<String, dynamic> json) => DismissReopenResponse(
        state: json['state'] as String? ?? '',
        message: json['message'] as String? ?? '',
      );
}