/// Phase 3 + Phase 4 models: experiment engine, evaluation and learning candidates.
///
/// Mirrors the backend wire shapes in `app/schemas/experiment.py`. Missing
/// analytics values stay `null` - never fabricated.
library;

import '../core/utils/date_utils.dart';

class ExperimentTemplate {
  final int id;
  final String experimentType;
  final String title;
  final String description;
  final String hypothesisTemplate;
  final String intervention;
  final int durationDays;
  final List<String> requiredMetrics;
  final bool active;

  const ExperimentTemplate({
    required this.id,
    required this.experimentType,
    required this.title,
    required this.description,
    required this.hypothesisTemplate,
    required this.intervention,
    required this.durationDays,
    required this.requiredMetrics,
    required this.active,
  });

  factory ExperimentTemplate.fromJson(Map<String, dynamic> json) => ExperimentTemplate(
        id: json['id'] as int,
        experimentType: json['experiment_type'] as String,
        title: json['title'] as String,
        description: json['description'] as String,
        hypothesisTemplate: json['hypothesis_template'] as String,
        intervention: json['intervention'] as String,
        durationDays: json['duration_days'] as int,
        requiredMetrics: (json['required_metrics'] as List<dynamic>).cast<String>(),
        active: json['active'] as bool? ?? true,
      );
}

class PatternSnapshot {
  final String patternId;
  final String featureLabel;
  final String targetLabel;
  final String? direction;
  final double? correlation;
  final int sampleSize;
  final String strength;
  final String strengthLabel;
  final String why;

  const PatternSnapshot({
    required this.patternId,
    required this.featureLabel,
    required this.targetLabel,
    required this.direction,
    required this.correlation,
    required this.sampleSize,
    required this.strength,
    required this.strengthLabel,
    required this.why,
  });

  factory PatternSnapshot.fromJson(Map<String, dynamic> json) => PatternSnapshot(
        patternId: json['pattern_id'] as String,
        featureLabel: json['feature_label'] as String,
        targetLabel: json['target_label'] as String,
        direction: json['direction'] as String?,
        correlation: (json['correlation'] as num?)?.toDouble(),
        sampleSize: json['sample_size'] as int? ?? 0,
        strength: json['strength'] as String? ?? 'none',
        strengthLabel: json['strength_label'] as String? ?? 'Not enough data',
        why: json['why'] as String? ?? '',
      );
}

class LearningContext {
  final bool hasLearning;
  final String? evidenceLevel;
  final String? evidenceState;
  final String? note;

  const LearningContext({required this.hasLearning, this.evidenceLevel, this.evidenceState, this.note});

  factory LearningContext.fromJson(Map<String, dynamic> json) => LearningContext(
        hasLearning: json['has_learning'] as bool? ?? false,
        evidenceLevel: json['evidence_level'] as String?,
        evidenceState: json['evidence_state'] as String?,
        note: json['note'] as String?,
      );
}

class ExperimentRecommendation {
  final String experimentType;
  final String title;
  final String why;
  final PatternSnapshot pattern;
  final String hypothesis;
  final String intervention;
  final int durationDays;
  final List<String> metrics;
  final LearningContext learningContext;

  const ExperimentRecommendation({
    required this.experimentType,
    required this.title,
    required this.why,
    required this.pattern,
    required this.hypothesis,
    required this.intervention,
    required this.durationDays,
    required this.metrics,
    required this.learningContext,
  });

  factory ExperimentRecommendation.fromJson(Map<String, dynamic> json) => ExperimentRecommendation(
        experimentType: json['experiment_type'] as String,
        title: json['title'] as String,
        why: json['why'] as String,
        pattern: PatternSnapshot.fromJson(json['pattern'] as Map<String, dynamic>),
        hypothesis: json['hypothesis'] as String,
        intervention: json['intervention'] as String,
        durationDays: json['duration_days'] as int,
        metrics: (json['metrics'] as List<dynamic>).cast<String>(),
        learningContext: LearningContext.fromJson(json['learning_context'] as Map<String, dynamic>? ?? const {}),
      );
}

class RecommendationResponse {
  final ExperimentRecommendation? recommendation;
  final bool hasActiveExperiment;
  final int? activeExperimentId;
  final String? reason;

  const RecommendationResponse({
    required this.recommendation,
    required this.hasActiveExperiment,
    required this.activeExperimentId,
    required this.reason,
  });

  factory RecommendationResponse.fromJson(Map<String, dynamic> json) => RecommendationResponse(
        recommendation: json['recommendation'] == null
            ? null
            : ExperimentRecommendation.fromJson(json['recommendation'] as Map<String, dynamic>),
        hasActiveExperiment: json['has_active_experiment'] as bool? ?? false,
        activeExperimentId: json['active_experiment_id'] as int?,
        reason: json['reason'] as String?,
      );
}

class Experiment {
  final int id;
  final String? patternId;
  final String experimentType;
  final String title;
  final String hypothesis;
  final String intervention;
  final int durationDays;
  final DateTime startDate;
  final DateTime endDate;
  final String status; // running | completed | cancelled
  final DateTime? completedAt;
  final DateTime createdAt;

  const Experiment({
    required this.id,
    required this.patternId,
    required this.experimentType,
    required this.title,
    required this.hypothesis,
    required this.intervention,
    required this.durationDays,
    required this.startDate,
    required this.endDate,
    required this.status,
    required this.completedAt,
    required this.createdAt,
  });

  factory Experiment.fromJson(Map<String, dynamic> json) => Experiment(
        id: json['id'] as int,
        patternId: json['pattern_id'] as String?,
        experimentType: json['experiment_type'] as String,
        title: json['title'] as String,
        hypothesis: json['hypothesis'] as String,
        intervention: json['intervention'] as String,
        durationDays: json['duration_days'] as int,
        startDate: AppDateUtils.fromIso(json['start_date'] as String),
        endDate: AppDateUtils.fromIso(json['end_date'] as String),
        status: json['status'] as String,
        completedAt: json['completed_at'] == null ? null : DateTime.parse(json['completed_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class ActiveExperimentResponse {
  final Experiment? experiment;

  const ActiveExperimentResponse({required this.experiment});

  factory ActiveExperimentResponse.fromJson(Map<String, dynamic> json) => ActiveExperimentResponse(
        experiment: json['experiment'] == null
            ? null
            : Experiment.fromJson(json['experiment'] as Map<String, dynamic>),
      );
}

class ExperimentDailyLog {
  final int id;
  final int experimentId;
  final DateTime date;
  final bool completed;
  final bool? targetMet;
  final String? notes;
  final int? dayNumber;

  const ExperimentDailyLog({
    required this.id,
    required this.experimentId,
    required this.date,
    required this.completed,
    required this.targetMet,
    required this.notes,
    required this.dayNumber,
  });

  factory ExperimentDailyLog.fromJson(Map<String, dynamic> json) => ExperimentDailyLog(
        id: json['id'] as int,
        experimentId: json['experiment_id'] as int,
        date: AppDateUtils.fromIso(json['date'] as String),
        completed: json['completed'] as bool? ?? true,
        targetMet: json['target_met'] as bool?,
        notes: json['notes'] as String?,
        dayNumber: json['day_number'] as int?,
      );
}

class ExperimentDetail {
  final Experiment experiment;
  final List<ExperimentDailyLog> dailyLogs;
  final String? target;
  final DateTime today;
  final int daysInto;
  final int progressPercent;

  const ExperimentDetail({
    required this.experiment,
    required this.dailyLogs,
    required this.target,
    required this.today,
    required this.daysInto,
    required this.progressPercent,
  });

  factory ExperimentDetail.fromJson(Map<String, dynamic> json) => ExperimentDetail(
        experiment: Experiment.fromJson(json['experiment'] as Map<String, dynamic>),
        dailyLogs: (json['daily_logs'] as List<dynamic>? ?? [])
            .map((e) => ExperimentDailyLog.fromJson(e as Map<String, dynamic>))
            .toList(),
        target: json['target'] as String?,
        today: AppDateUtils.fromIso(json['today'] as String),
        daysInto: json['days_into'] as int? ?? 0,
        progressPercent: json['progress_percent'] as int? ?? 0,
      );
}

class MetricComparison {
  final String metric;
  final double? baselineMean;
  final double? experimentMean;
  final double? baselineMedian;
  final double? experimentMedian;
  final double? difference;
  final double? percentageChange;
  final int sampleSize;
  final int validObservations;
  final String direction; // improved | worsened | no_change

  const MetricComparison({
    required this.metric,
    required this.baselineMean,
    required this.experimentMean,
    required this.baselineMedian,
    required this.experimentMedian,
    required this.difference,
    required this.percentageChange,
    required this.sampleSize,
    required this.validObservations,
    required this.direction,
  });

  factory MetricComparison.fromJson(Map<String, dynamic> json) => MetricComparison(
        metric: json['metric'] as String,
        baselineMean: (json['baseline_mean'] as num?)?.toDouble(),
        experimentMean: (json['experiment_mean'] as num?)?.toDouble(),
        baselineMedian: (json['baseline_median'] as num?)?.toDouble(),
        experimentMedian: (json['experiment_median'] as num?)?.toDouble(),
        difference: (json['difference'] as num?)?.toDouble(),
        percentageChange: (json['percentage_change'] as num?)?.toDouble(),
        sampleSize: json['sample_size'] as int? ?? 0,
        validObservations: json['valid_observations'] as int? ?? 0,
        direction: json['direction'] as String? ?? 'no_change',
      );
}

class ExperimentResult {
  final int experimentId;
  final String status;
  final List<MetricComparison> metrics;
  final double dataCompleteness;
  final int sampleSize;
  final double? targetAdherence;
  final String? targetAdherenceText;
  final double? consistencyScore;
  final String evidenceLevel;
  final bool causalityProven;
  final String summary;
  final String limitations;
  final Map<String, dynamic> learning;

  const ExperimentResult({
    required this.experimentId,
    required this.status,
    required this.metrics,
    required this.dataCompleteness,
    required this.sampleSize,
    required this.targetAdherence,
    required this.targetAdherenceText,
    required this.consistencyScore,
    required this.evidenceLevel,
    required this.causalityProven,
    required this.summary,
    required this.limitations,
    required this.learning,
  });

  factory ExperimentResult.fromJson(Map<String, dynamic> json) => ExperimentResult(
        experimentId: json['experiment_id'] as int,
        status: json['status'] as String? ?? 'completed',
        metrics: (json['metrics'] as List<dynamic>? ?? [])
            .map((e) => MetricComparison.fromJson(e as Map<String, dynamic>))
            .toList(),
        dataCompleteness: (json['data_completeness'] as num?)?.toDouble() ?? 0,
        sampleSize: json['sample_size'] as int? ?? 0,
        targetAdherence: (json['target_adherence'] as num?)?.toDouble(),
        targetAdherenceText: json['target_adherence_text'] as String?,
        consistencyScore: (json['consistency_score'] as num?)?.toDouble(),
        evidenceLevel: json['evidence_level'] as String? ?? 'INSUFFICIENT',
        causalityProven: json['causality_proven'] as bool? ?? false,
        summary: json['summary'] as String? ?? '',
        limitations: json['limitations'] as String? ?? '',
        learning: json['learning'] as Map<String, dynamic>? ?? const {},
      );
}

class ExperimentHistoryItem {
  final Experiment experiment;
  final ExperimentResult? result;

  const ExperimentHistoryItem({required this.experiment, required this.result});

  factory ExperimentHistoryItem.fromJson(Map<String, dynamic> json) => ExperimentHistoryItem(
        experiment: Experiment.fromJson(json['experiment'] as Map<String, dynamic>),
        result: json['result'] == null
            ? null
            : ExperimentResult.fromJson(json['result'] as Map<String, dynamic>),
      );
}

class LearningCandidate {
  final int id;
  final int userId;
  final int experimentId;
  final String patternType;
  final String intervention;
  final Map<String, dynamic> observedChange;
  final String evidenceLevel;
  final String status; // candidate | accepted | rejected | superseded
  final bool causalityProven;
  final DateTime createdAt;

  const LearningCandidate({
    required this.id,
    required this.userId,
    required this.experimentId,
    required this.patternType,
    required this.intervention,
    required this.observedChange,
    required this.evidenceLevel,
    required this.status,
    required this.causalityProven,
    required this.createdAt,
  });

  factory LearningCandidate.fromJson(Map<String, dynamic> json) => LearningCandidate(
        id: json['id'] as int,
        userId: json['user_id'] as int,
        experimentId: json['experiment_id'] as int,
        patternType: json['pattern_type'] as String,
        intervention: json['intervention'] as String,
        observedChange: json['observed_change'] as Map<String, dynamic>? ?? const {},
        evidenceLevel: json['evidence_level'] as String,
        status: json['status'] as String? ?? 'candidate',
        causalityProven: json['causality_proven'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class LearningCandidateList {
  final List<LearningCandidate> candidates;

  const LearningCandidateList({required this.candidates});

  factory LearningCandidateList.fromJson(Map<String, dynamic> json) => LearningCandidateList(
        candidates: (json['candidates'] as List<dynamic>? ?? [])
            .map((e) => LearningCandidate.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class ExperimentEvidence {
  final int id;
  final int experimentId;
  final double dataCompleteness;
  final double? targetAdherence;
  final double? consistencyScore;
  final String evidenceLevel;
  final String reason;
  final String limitations;
  final bool causalityProven;

  const ExperimentEvidence({
    required this.id,
    required this.experimentId,
    required this.dataCompleteness,
    required this.targetAdherence,
    required this.consistencyScore,
    required this.evidenceLevel,
    required this.reason,
    required this.limitations,
    required this.causalityProven,
  });

  factory ExperimentEvidence.fromJson(Map<String, dynamic> json) => ExperimentEvidence(
        id: json['id'] as int,
        experimentId: json['experiment_id'] as int,
        dataCompleteness: (json['data_completeness'] as num?)?.toDouble() ?? 0,
        targetAdherence: (json['target_adherence'] as num?)?.toDouble(),
        consistencyScore: (json['consistency_score'] as num?)?.toDouble(),
        evidenceLevel: json['evidence_level'] as String,
        reason: json['reason'] as String? ?? '',
        limitations: json['limitations'] as String? ?? '',
        causalityProven: json['causality_proven'] as bool? ?? false,
      );
}

class MessageResponse {
  final String message;

  const MessageResponse({required this.message});

  factory MessageResponse.fromJson(Map<String, dynamic> json) =>
      MessageResponse(message: json['message'] as String? ?? '');
}