/// Home dashboard screen.
///
/// Phase 1 shows only observed values; NO fake AI score or disease risk.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../../core/utils/date_utils.dart';
import '../../models/health_data.dart';
import '../../repositories/health_repository.dart';
import '../../services/health_connect_service.dart';
import '../../widgets/metric_card.dart';
import '../../widgets/progress_card.dart';
import '../../app.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

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
      _loading = true;
      _error = null;
    });
    try {
      final svc = AppServices.instance;
      final repo = HealthRepository(svc.api);
      final data = await repo.dashboardToday();
      if (mounted) setState(() => _dashboard = data);
    } catch (e) {
      if (mounted) setState(() => _error = 'Could not load dashboard.');
    } finally {
      if (mounted) setState(() => _loading = false);
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
      if (dayData.steps == null && dayData.activeMinutes == null && dayData.sleepMinutes == null) return;

      await healthRepo.sync(
        steps: dayData.steps,
        activeMinutes: dayData.activeMinutes,
        sleepMinutes: dayData.sleepMinutes,
      );
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

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final s = _dashboard?.summary;

    return RefreshIndicator(
      onRefresh: _load,
      child: CustomScrollView(
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            sliver: SliverToBoxAdapter(
              child: Text(
                "$_greeting \ud83d\udc4b",
                style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
            sliver: SliverToBoxAdapter(
              child: Text(
                AppStrings.dashboardTitle,
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: scheme.onSurfaceVariant),
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
                    Text(_error!),
                    const SizedBox(height: 12),
                    FilledButton(onPressed: _load, child: const Text('Retry')),
                  ],
                ),
              ),
            )
          else ...[
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
              sliver: SliverToBoxAdapter(
                child: _dashboard!.hasData
                    ? Text(
                        'Data for ${AppDateUtils.shortDay(s!.date)}',
                        style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant),
                      )
                    : Text(
                        AppStrings.baselineLearning,
                        style: TextStyle(fontSize: 14, color: scheme.onSurfaceVariant),
                      ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 0),
              sliver: SliverGrid.count(
                crossAxisCount: 2,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: 1.55,
                children: [
                  MetricCard(title: 'Sleep', value: s?.sleepHours?.toStringAsFixed(1) ?? '\u2014', unit: 'h', icon: Icons.nightlight_round, isEmpty: s?.sleepHours == null),
                  MetricCard(title: 'Steps', value: s?.steps != null ? '${s!.steps!.toString()}' : '\u2014', icon: Icons.directions_walk, isEmpty: s?.steps == null),
                  MetricCard(title: 'Activity', value: s?.activeMinutes?.toString() ?? '\u2014', unit: 'min', icon: Icons.timer, isEmpty: s?.activeMinutes == null),
                  MetricCard(title: 'Energy', value: s?.energy?.toString() ?? '\u2014', unit: '/10', icon: Icons.bolt, isEmpty: s?.energy == null),
                  MetricCard(title: 'Stress', value: s?.stress?.toString() ?? '\u2014', unit: '/5', icon: Icons.psychology, isEmpty: s?.stress == null),
                  MetricCard(title: 'Water', value: s?.waterLiters?.toStringAsFixed(1) ?? '\u2014', unit: 'L', icon: Icons.water_drop, isEmpty: s?.waterLiters == null),
                ],
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
              sliver: SliverToBoxAdapter(
                child: ProgressCard(baseline: _dashboard!.baseline),
              ),
            ),
          ],
          const SliverToBoxAdapter(child: SizedBox(height: 30)),
        ],
      ),
    );
  }
}