/// Experiments tab (Phase 3): recommendation, active experiment and history.
///
/// Recommendation comes from the deterministic analytics engine - it is a
/// correlation observation to test, never a medical recommendation.
library;

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../core/utils/date_utils.dart';
import '../../models/experiment.dart';
import '../../repositories/experiment_repository.dart';
import '../learning/learning_screen.dart';
import 'experiment_detail_screen.dart';

class ExperimentsScreen extends StatefulWidget {
  const ExperimentsScreen({super.key});

  @override
  State<ExperimentsScreen> createState() => _ExperimentsScreenState();
}

class _ExperimentsScreenState extends State<ExperimentsScreen> {
  final ExperimentRepository _repo = ExperimentRepository(AppServices.instance.api);

  RecommendationResponse? _recommendation;
  ActiveExperimentResponse? _active;
  List<ExperimentHistoryItem> _history = const [];
  bool _loading = true;
  bool _starting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait([
        _repo.recommended(),
        _repo.active(),
        _repo.history(),
      ]);
      if (!mounted) return;
      setState(() {
        _recommendation = results[0] as RecommendationResponse;
        _active = results[1] as ActiveExperimentResponse;
        _history = (results[2] as List<ExperimentHistoryItem>);
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _startRecommended(ExperimentRecommendation rec) async {
    setState(() => _starting = true);
    try {
      await _repo.start(rec.experimentType);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Experiment started. Keep logging daily!')),
          );
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _starting = false);
    }
  }

  Future<void> _openDetail(int experimentId) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ExperimentDetailScreen(experimentId: experimentId)),
    );
    if (mounted) _load();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final active = _active?.experiment;
    final rec = _recommendation?.recommendation;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Experiments'),
        actions: [
          IconButton(
            icon: const Icon(Icons.psychology_outlined),
            tooltip: 'What works for me',
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const LearningScreen()),
              );
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off, size: 40),
                      const SizedBox(height: 12),
                      Text(_error!),
                      const SizedBox(height: 12),
                      FilledButton(onPressed: _load, child: const Text('Retry')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.all(20),
                    children: [
                      if (active != null) ...[
                        _ActiveCard(
                          experiment: active,
                          progressPercent: 0,
                          onTap: () => _openDetail(active.id),
                        ),
                        const SizedBox(height: 16),
                      ],
                      if (_recommendation != null && rec != null) ...[
                        Text('Suggested next test', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: scheme.onSurfaceVariant)),
                        const SizedBox(height: 8),
                        _RecommendationCard(
                          recommendation: rec,
                          starting: _starting,
                          onStart: () => _startRecommended(rec),
                        ),
                        const SizedBox(height: 16),
                      ],
                      if (rec == null && _recommendation != null && active == null) ...[
                        _EmptyRecommendation(reason: _recommendation!.reason),
                        const SizedBox(height: 16),
                      ],
                      Text(
                        'Past experiments',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: scheme.onSurfaceVariant),
                      ),
                      const SizedBox(height: 8),
                      if (_history.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 24),
                          child: Center(
                            child: Text(
                              'No experiments yet. When you have at least a few days of check-ins, you will get a suggestion to test a pattern.',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: scheme.onSurfaceVariant),
                            ),
                          ),
                        )
                      else
                        ..._history.map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: _HistoryTile(item: item, onTap: () => _openDetail(item.experiment.id)),
                          ),
                        ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
    );
  }
}

class _ActiveCard extends StatelessWidget {
  const _ActiveCard({required this.experiment, required this.progressPercent, required this.onTap});

  final Experiment experiment;
  final int progressPercent;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.primaryContainer,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.science_outlined, color: scheme.onPrimaryContainer),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(experiment.title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: scheme.onPrimaryContainer)),
                  ),
                  const SizedBox(width: 8),
                  Text(experiment.status, style: TextStyle(color: scheme.onPrimaryContainer)),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Intervention: ${experiment.intervention}',
                style: TextStyle(color: scheme.onPrimaryContainer),
              ),
              const SizedBox(height: 4),
              Text(
                '${AppDateUtils.shortDay(experiment.startDate)} - ${AppDateUtils.shortDay(experiment.endDate)}',
                style: TextStyle(color: scheme.onPrimaryContainer.withValues(alpha: 0.7)),
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(value: progressPercent / 100),
              const SizedBox(height: 6),
              Text(
                'Open to log today',
                style: TextStyle(fontSize: 12, color: scheme.onPrimaryContainer.withValues(alpha: 0.7)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({required this.recommendation, required this.starting, required this.onStart});

  final ExperimentRecommendation recommendation;
  final bool starting;
  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(recommendation.title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text(recommendation.why, style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
            const SizedBox(height: 10),
            _row(context, Icons.flag_outlined, 'Try: ${recommendation.intervention}'),
            _row(
              context,
              Icons.calendar_month_outlined,
              '${recommendation.durationDays} days, watch ${recommendation.metrics.join(', ')}',
            ),
            if (recommendation.learningContext.hasLearning)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  'Known from your history: ${recommendation.learningContext.note ?? 'a similar pattern was observed before.'}',
                  style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: scheme.onSurfaceVariant),
                ),
              ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: starting ? null : onStart,
                child: starting
                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Start experiment'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _row(BuildContext context, IconData icon, String text) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: scheme.primary),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 13.5))),
        ],
      ),
    );
  }
}

class _EmptyRecommendation extends StatelessWidget {
  const _EmptyRecommendation({required this.reason});

  final String? reason;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.insights_outlined, color: scheme.primary),
            const SizedBox(height: 8),
            Text(
              reason ?? 'Not enough data yet to suggest an experiment. Keep logging your daily check-ins.',
              style: TextStyle(color: scheme.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({required this.item, required this.onTap});

  final ExperimentHistoryItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final exp = item.experiment;
    final evidence = item.result?.evidenceLevel ?? 'NO_EVIDENCE';
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(exp.title, style: const TextStyle(fontWeight: FontWeight.w700)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: scheme.secondaryContainer,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      exp.status,
                      style: TextStyle(fontSize: 11, color: scheme.onSecondaryContainer),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                exp.intervention,
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13),
              ),
              const SizedBox(height: 4),
              Text(
                '${AppDateUtils.shortDay(exp.startDate)} - ${AppDateUtils.shortDay(exp.endDate)}',
                style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant.withValues(alpha: 0.7)),
              ),
              if (item.result != null) ...[
                const SizedBox(height: 8),
                _evidenceChip(scheme, evidence),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _evidenceChip(ColorScheme scheme, String level) {
    return Row(
      children: [
        Icon(Icons.fact_check_outlined, size: 16, color: scheme.primary),
        const SizedBox(width: 6),
        Text(
          'Evidence: ${level.replaceAll('_', ' ')}',
          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: scheme.onSurfaceVariant),
        ),
      ],
    );
  }
}