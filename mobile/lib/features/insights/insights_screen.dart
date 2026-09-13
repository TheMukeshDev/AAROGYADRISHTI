/// Insights screen - real-data pattern discovery.
///
/// Everything shown here is aggregated ONLY from the user's own daily logs.
/// No fabricated trends: until at least two logged dates appear in the chosen
/// window, the screen shows the "Not enough data yet" state instead.
library;

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../models/daily_log.dart';
import '../../repositories/daily_log_repository.dart';
import '../../widgets/section_header.dart';

/// Period choices for the trend window.
enum _Range { week('7 days', 7), fortnight('14 days', 14), month('30 days', 30);

  const _Range(this.label, this.days);
  final String label;
  final int days;
}

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  List<DailyLog> _logs = const [];
  _Range _range = _Range.week;
  bool _loading = true;
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
      final repo = DailyLogRepository(AppServices.instance.api);
      final logs = await repo.list(limit: 90);
      if (mounted) setState(() => _logs = List.unmodifiable(logs.reversed));
    } on NetworkException {
      if (mounted) setState(() => _error = AppStrings.noInternet);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<DailyLog> get _window {
    final cutoff = DateTime.now().subtract(Duration(days: _range.days));
    return _logs.where((l) => !l.date.isBefore(cutoff)).toList();
  }

  /// Number of distinct logged dates; charts need >= 2 real points.
  bool get _hasEnough => _window.length >= 2;

  double? _avg(double? Function(DailyLog) pick) {
    final values = _window.map(pick).whereType<double>().toList();
    if (values.isEmpty) return null;
    return values.reduce((a, b) => a + b) / values.length;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SafeArea(
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
            sliver: SliverToBoxAdapter(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          AppStrings.insightsTitle,
                          style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, height: 1.15),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          AppStrings.insightsSubtitle,
                          style: TextStyle(fontSize: 15.5, color: scheme.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: 'Refresh',
                    onPressed: _load,
                    icon: const Icon(Icons.refresh_rounded),
                  ),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
            sliver: SliverToBoxAdapter(
              child: Row(
                children: [
                  for (final r in _Range.values) ...[
                    _RangeChip(
                      label: r.label,
                      selected: _range == r,
                      onTap: () => setState(() => _range = r),
                    ),
                    if (r != _Range.values.last) const SizedBox(width: 8),
                  ],
                  const Spacer(),
                ],
              ),
            ),
          ),
          if (_loading)
            const SliverFillRemaining(hasScrollBody: false, child: Center(child: CircularProgressIndicator()))
          else if (_error != null)
            SliverFillRemaining(
              hasScrollBody: false,
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_off, size: 40),
                    const SizedBox(height: 12),
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    FilledButton(onPressed: _load, child: const Text('Retry')),
                  ],
                ),
              ),
            )
          else if (!_hasEnough)
            ..._notEnoughState(scheme)
          else
            ..._chartState(scheme),
          const SliverToBoxAdapter(child: SizedBox(height: 32)),
        ],
      ),
    );
  }

  List<Widget> _notEnoughState(ColorScheme scheme) {
    return [
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(24, 28, 24, 0),
        sliver: SliverToBoxAdapter(
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: scheme.surfaceContainerLow,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: scheme.outlineVariant, width: 1),
                ),
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: scheme.primaryContainer,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.show_chart_rounded, size: 30, color: scheme.primary),
                    ),
                    const SizedBox(height: 14),
                    Text(
                      AppStrings.notEnoughData,
                      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      AppStrings.notEnoughDataHint,
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 14, color: scheme.onSurfaceVariant, height: 1.45),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
        sliver: SliverToBoxAdapter(
          child: SectionHeader(
            title: 'What you will see here',
            subtitle: 'Your personal patterns, built only from data you share.',
          ),
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(24, 4, 24, 0),
        sliver: SliverList.list(
          children: const [
            _InfoRow(icon: Icons.nightlight_round, text: 'Sleep trends over time'),
            _InfoRow(icon: Icons.mood_rounded, text: 'Energy and mood patterns'),
            _InfoRow(icon: Icons.water_drop_outlined, text: 'Hydration consistency'),
            _InfoRow(icon: Icons.self_improvement_outlined, text: 'Stress level changes'),
          ],
        ),
      ),
    ];
  }

  List<Widget> _chartState(ColorScheme scheme) {
    final window = _window;
    final avgSleep = _avg((l) => l.sleepHours);
    final avgEnergy = _avg((l) => l.energy?.toDouble());

    List<({String label, double? value})> points(double? Function(DailyLog) pick) {
      return window
          .map((l) => (label: l.displayDate, value: pick(l)))
          .toList();
    }

    return [
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
        sliver: SliverToBoxAdapter(
          child: Row(
            children: [
              Expanded(
                child: _SummaryTile(
                  icon: Icons.bedtime_outlined,
                  label: 'Avg sleep',
                  value: avgSleep?.toStringAsFixed(1) ?? '\u2014',
                  unit: 'h',
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _SummaryTile(
                  icon: Icons.bolt_outlined,
                  label: 'Avg energy',
                  value: avgEnergy?.toStringAsFixed(1) ?? '\u2014',
                  unit: '/10',
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _SummaryTile(
                  icon: Icons.edit_calendar_rounded,
                  label: 'Check-ins',
                  value: '${window.length}',
                ),
              ),
            ],
          ),
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
        sliver: SliverToBoxAdapter(
          child: SectionHeader(
            title: AppStrings.yourPatterns,
            subtitle: 'Averages across your last ${window.length} check-ins.',
          ),
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(24, 12, 24, 0),
        sliver: SliverToBoxAdapter(
          child: _TrendChart(
            title: 'Sleep',
            icon: Icons.nightlight_round,
            points: points((l) => l.sleepHours),
            unit: 'h',
          ),
        ),
      ),
      const SliverToBoxAdapter(child: SizedBox(height: 14)),
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        sliver: SliverToBoxAdapter(
          child: _TrendChart(
            title: 'Steps',
            icon: Icons.directions_walk_rounded,
            points: points((l) => l.steps?.toDouble()),
          ),
        ),
      ),
      const SliverToBoxAdapter(child: SizedBox(height: 14)),
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        sliver: SliverToBoxAdapter(
          child: _TrendChart(
            title: 'Energy',
            icon: Icons.bolt_rounded,
            points: points((l) => l.energy?.toDouble()),
            unit: '/10',
          ),
        ),
      ),
      const SliverToBoxAdapter(child: SizedBox(height: 14)),
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 24),
        sliver: SliverToBoxAdapter(
          child: _TrendChart(
            title: 'Stress',
            icon: Icons.spa_outlined,
            points: points((l) => l.stress?.toDouble()),
            unit: '/5',
          ),
        ),
      ),
    ];
  }
}

class _RangeChip extends StatelessWidget {
  const _RangeChip({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onTap(),
      selectedColor: scheme.primary,
      labelStyle: TextStyle(
        color: selected ? scheme.onPrimary : scheme.onSurface,
        fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
        fontSize: 13,
      ),
    );
  }
}

class _SummaryTile extends StatelessWidget {
  const _SummaryTile({required this.icon, required this.label, required this.value, this.unit});

  final IconData icon;
  final String label;
  final String value;
  final String? unit;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: scheme.outlineVariant, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: scheme.primary),
          const SizedBox(height: 10),
          Text.rich(
            TextSpan(
              children: [
                TextSpan(
                  text: value,
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, height: 1.05),
                ),
                if (unit != null)
                  TextSpan(
                    text: ' $unit',
                    style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant, fontWeight: FontWeight.w500),
                  ),
              ],
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(fontSize: 11.5, color: scheme.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}

class _TrendChart extends StatelessWidget {
  const _TrendChart({required this.title, required this.icon, required this.points, this.unit});

  final String title;
  final IconData icon;
  final List<({String label, double? value})> points;
  final String? unit;

  static const double _barHeight = 88;
  static const int _maxBars = 14;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final max = points
        .map((p) => p.value)
        .whereType<double>()
        .fold(0.0, (a, b) => b > a ? b : a);
    final bars = points.length > _maxBars ? points.sublist(points.length - _maxBars) : points;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: scheme.outlineVariant, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 17, color: scheme.primary),
              const SizedBox(width: 8),
              Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
              const Spacer(),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            height: _barHeight,
            alignment: Alignment.bottomCenter,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                for (final p in bars) ...[
                  Expanded(child: _Bar(value: p.value, max: max, height: _barHeight, unit: unit)),
                ],
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              for (final p in bars)
                Expanded(
                  child: Text(
                    p.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 9, color: scheme.onSurfaceVariant),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _Bar extends StatelessWidget {
  const _Bar({required this.value, required this.max, required this.height, this.unit});

  final double? value;
  final double max;
  final double height;
  final String? unit;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    if (value == null) {
      return SizedBox(
        height: height,
        child: Center(
          child: Text('\u2014',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: scheme.outline,
              )),
        ),
      );
    }

    final fraction = max <= 0 ? 0.03 : (value! / max).clamp(0.03, 1.0);
    final barPixelHeight = height * fraction;

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        if (unit != null)
          Text(
            value!.toStringAsFixed(1),
            style: TextStyle(fontSize: 9, color: scheme.onSurfaceVariant),
          ),
        const SizedBox(height: 3),
        Container(
          height: barPixelHeight,
          decoration: BoxDecoration(
            color: scheme.primary,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(5)),
          ),
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(7),
            decoration: BoxDecoration(
              color: scheme.primaryContainer,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, size: 16, color: scheme.primary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: 14.5, color: scheme.onSurfaceVariant),
            ),
          ),
        ],
      ),
    );
  }
}