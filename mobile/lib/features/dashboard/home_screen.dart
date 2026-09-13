/// Home dashboard screen.
///
/// Shows a lifestyle score computed ONLY from the user's own check-in data
/// (missing metrics keep a "no data yet" state - nothing is ever invented),
/// today's observed values, a daily check-in CTA and baseline progress.
library;

import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../../core/utils/date_utils.dart';
import '../../models/app_enums.dart';
import '../../models/dashboard.dart';
import '../../models/health_data.dart';
import '../../providers/auth_provider.dart';
import '../../repositories/health_repository.dart';
import '../../services/health_connect_service.dart';
import '../../widgets/app_logo.dart';
import '../../widgets/metric_card.dart';
import '../../widgets/progress_card.dart';
import '../../widgets/section_header.dart';
import '../../app.dart';
import '../checkin/checkin_screen.dart';
import '../history/history_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.onOpenProfile});

  /// Invoked when the user taps the profile header icon (switches tab).
  final VoidCallback? onOpenProfile;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  DashboardData? _dashboard;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
    _syncHealth();
  }

  Future<void> _load() async {
    setState(() {
      _loading = _dashboard == null;
      _error = null;
    });
    try {
      final svc = AppServices.instance;
      final repo = HealthRepository(svc.api);
      final data = await repo.dashboardToday();
      if (mounted) setState(() => _dashboard = data);
    } catch (_) {
      if (mounted && _dashboard == null) {
        setState(() => _error = AppStrings.apiUnavailable);
      }
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _syncHealth() async {
    try {
      final svc = AppServices.instance;
      final healthRepo = HealthRepository(svc.api);
      final conn = await healthRepo.getStatus();
      if (!conn.isConnected) return;

      final health = HealthConnectService.instance;
      final availability = health.availability ?? await health.setup();
      if (availability != HealthConnectAvailability.supported) return;

      final now = DateTime.now();
      final midnight = DateTime(now.year, now.month, now.day);
      final dayData = await health.readDay(midnight);
      if (dayData.steps == null && dayData.activeMinutes == null && dayData.sleepMinutes == null) {
        return;
      }

      await healthRepo.sync(
        steps: dayData.steps,
        activeMinutes: dayData.activeMinutes,
        sleepMinutes: dayData.sleepMinutes,
      );
      await _load();
    } catch (_) {
      // Health sync is best-effort; never block dashboard rendering.
    }
  }

  String get _greeting {
    final h = DateTime.now().hour;
    if (h < 12) return AppStrings.morningHello;
    if (h < 17) return AppStrings.afternoonHello;
    return AppStrings.eveningHello;
  }

  /// Transparent "lifestyle score": an average of the user's OWN recorded
  /// metrics only. Never shows a value when there is no data.
  ({double? score, String? label}) _score(DashboardSummary? s) {
    if (s == null) {
      return (score: null, label: null);
    }

    final parts = <double>[];
    final sleep = s.sleepHours;
    if (sleep != null) {
      parts.add((100 - (sleep - 7.5).abs() * 12.5).clamp(0, 100).toDouble());
    }
    final energy = s.energy;
    if (energy != null) parts.add((energy * 10).clamp(0, 100).toDouble());
    final stress = s.stress;
    if (stress != null) parts.add(((6 - stress) / 5 * 100).clamp(0, 100).toDouble());
    final steps = s.steps;
    if (steps != null) parts.add((steps / 8000 * 100).clamp(0, 100).toDouble());
    final active = s.activeMinutes;
    if (active != null) parts.add((active / 30 * 100).clamp(0, 100).toDouble());
    final water = s.waterLiters;
    if (water != null) parts.add((water / 2 * 100).clamp(0, 100).toDouble());

    if (parts.isEmpty) return (score: null, label: null);
    final avg = parts.reduce((a, b) => a + b) / parts.length;
    final label = avg >= 80
        ? 'Good'
        : avg >= 60
            ? 'Fair'
            : avg >= 40
                ? 'Needs attention'
                : 'Getting started';
    return (score: avg.roundToDouble(), label: label);
  }

  Future<void> _openCheckin() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const CheckinScreen()),
    );
    if (mounted) _load();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final auth = context.watch<AuthProvider>();
    final s = _dashboard?.summary;
    final score = _score(s);

    return RefreshIndicator(
      onRefresh: _load,
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          SliverSafeArea(
            sliver: SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              sliver: SliverToBoxAdapter(child: _header(scheme, auth)),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            sliver: SliverToBoxAdapter(
              child: _LifestyleScoreCard(
                score: score.score,
                label: score.label,
                hasAnyData: _dashboard?.hasData ?? false,
                loading: _loading,
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            sliver: SliverToBoxAdapter(
              child: _CheckinCtaCard(onTap: _openCheckin),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
            sliver: SliverToBoxAdapter(
              child: SectionHeader(
                title: AppStrings.todayOverview,
                subtitle: _dashboard?.hasData == true
                    ? 'Data for ${AppDateUtils.shortDay(s!.date)}'
                    : AppStrings.lifestyleScoreCaption,
              ),
            ),
          ),
          if (_loading)
            const SliverFillRemaining(child: Center(child: CircularProgressIndicator()))
          else if (_error != null)
            SliverFillRemaining(
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
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 0),
              sliver: SliverGrid.count(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.5,
                children: [
                  MetricCard(
                    title: 'Sleep',
                    value: s?.sleepHours?.toStringAsFixed(1) ?? '',
                    unit: 'h',
                    icon: Icons.bedtime_outlined,
                    isEmpty: s?.sleepHours == null,
                    status: SleepQuality.fromWire(s?.sleepQuality)?.label,
                  ),
                  MetricCard(
                    title: 'Steps',
                    value: s?.steps != null ? '${s!.steps}' : '',
                    icon: Icons.directions_walk_rounded,
                    isEmpty: s?.steps == null,
                    status: _stepsStatus(s?.steps),
                  ),
                  MetricCard(
                    title: 'Activity',
                    value: s?.activeMinutes?.toString() ?? '',
                    unit: 'min',
                    icon: Icons.directions_run_rounded,
                    isEmpty: s?.activeMinutes == null,
                  ),
                  MetricCard(
                    title: 'Energy',
                    value: s?.energy?.toString() ?? '',
                    unit: '/10',
                    icon: Icons.bolt_rounded,
                    isEmpty: s?.energy == null,
                    status: _levelStatus(s?.energy, 3, 7),
                  ),
                  MetricCard(
                    title: 'Stress',
                    value: s?.stress?.toString() ?? '',
                    unit: '/5',
                    icon: Icons.spa_outlined,
                    isEmpty: s?.stress == null,
                    status: _levelStatus(s?.stress, 3, 4, invert: true),
                  ),
                  MetricCard(
                    title: 'Hydration',
                    value: s?.waterLiters != null ? '${(s!.waterLiters! * 4).round()}' : '',
                    unit: 'cups',
                    icon: Icons.water_drop_outlined,
                    isEmpty: s?.waterLiters == null,
                  ),
                ],
              ),
            ),
          if (!_loading && _error == null) ...[
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
              sliver: SliverToBoxAdapter(
                child: ProgressCard(baseline: _dashboard!.baseline),
              ),
            ),
          ],
          const SliverToBoxAdapter(child: SizedBox(height: 32)),
        ],
      ),
    );
  }

  Widget _header(ColorScheme scheme, AuthProvider auth) {
    final firstName = (auth.user?.name ?? auth.user?.email ?? 'there').split(' ').first;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const LogoMark(size: 38),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$_greeting, $firstName \ud83d\udc4b',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, letterSpacing: -0.3),
              ),
              const SizedBox(height: 2),
              Text(
                AppStrings.dashboardTitle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 13.5, color: scheme.onSurfaceVariant),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        _HeaderIcon(
          icon: Icons.notifications_outlined,
          tooltip: AppStrings.notifications,
          onTap: () => Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => const HistoryScreen()),
          ),
        ),
        const SizedBox(width: 4),
        _HeaderIcon(
          icon: Icons.account_circle_outlined,
          tooltip: AppStrings.profileSheet,
          onTap: widget.onOpenProfile,
        ),
      ],
    );
  }

  String? _stepsStatus(int? steps) {
    if (steps == null) return null;
    return steps >= 8000 ? 'Good' : steps >= 5000 ? 'Moderate' : 'Low';
  }

  /// Derive a Low / Medium / High label from a 1..[maxScale] rating.
  String? _levelStatus(int? value, int lowCutoff, int highCutoff, {bool invert = false}) {
    if (value == null) return null;
    if (invert) {
      return value <= lowCutoff ? 'Low' : value <= highCutoff ? 'Medium' : 'High';
    }
    return value <= lowCutoff ? 'Low' : value <= highCutoff ? 'Medium' : 'High';
  }
}

class _HeaderIcon extends StatelessWidget {
  const _HeaderIcon({required this.icon, required this.tooltip, this.onTap});

  final IconData icon;
  final String tooltip;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerLow,
      shape: const CircleBorder(),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(9),
          child: Icon(icon, size: 22, color: scheme.onSurfaceVariant),
        ),
      ),
    );
  }
}

/// Hero Lifestyle Score card with a circular progress ring.
class _LifestyleScoreCard extends StatelessWidget {
  const _LifestyleScoreCard({
    required this.score,
    required this.label,
    required this.hasAnyData,
    required this.loading,
  });

  final double? score;
  final String? label;
  final bool hasAnyData;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    final showValue = hasAnyData && score != null;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.deepTeal,
            const Color(0xFF0E7A68),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: AppColors.deepTeal.withValues(alpha: 0.22),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.health_and_safety_outlined, color: Colors.white, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      AppStrings.lifestyleScore,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (loading)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14),
                    child: SizedBox(
                      height: 16,
                      width: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    ),
                  )
                else if (showValue)
                  Text(
                    '$score',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 44,
                      height: 1.05,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -1,
                    ),
                  )
                else ...[
                  Text(
                    '\u2014',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 40,
                      height: 1.05,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    AppStrings.noDataYet,
                    style: TextStyle(color: Colors.white70, fontSize: 13),
                  ),
                ],
                if (showValue) ...[
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      label!,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          if (showValue)
            SizedBox(
              height: 104,
              width: 104,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    height: 104,
                    width: 104,
                    child: CircularProgressIndicator(
                      value: (score! / 100).clamp(0.0, 1.0),
                      strokeWidth: 10,
                      strokeCap: StrokeCap.round,
                      backgroundColor: Colors.white.withValues(alpha: 0.18),
                      valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${score!.round()}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 26,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      Text(
                        '${math.max(1, (score! / 25).ceil())} of 4',
                        style: TextStyle(color: Colors.white60, fontSize: 10),
                      ),
                    ],
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// Daily check-in call-to-action card.
class _CheckinCtaCard extends StatelessWidget {
  const _CheckinCtaCard({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.primaryContainer.withValues(alpha: 0.6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: scheme.primary.withValues(alpha: 0.25), width: 1),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: scheme.primary,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(Icons.edit_calendar_rounded, color: Colors.white, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      AppStrings.dailyCheckinCta,
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15.5),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      AppStrings.dailyCheckinCtaSubtitle,
                      style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: scheme.primary),
            ],
          ),
        ),
      ),
    );
  }
}