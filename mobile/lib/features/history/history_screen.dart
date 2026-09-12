/// History screen - simple chronological list of previous check-ins.
library;

import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../models/daily_log.dart';
import '../../repositories/daily_log_repository.dart';
import '../../app.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<DailyLog> _logs = [];
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
      if (mounted) setState(() => _logs = logs);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (e) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.historyTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
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
              : _logs.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.edit_note, size: 44),
                          const SizedBox(height: 12),
                          Text(
                            AppStrings.historyEmpty,
                            style: TextStyle(color: scheme.onSurfaceVariant),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        itemCount: _logs.length,
                        itemBuilder: (context, index) => _LogTile(log: _logs[index]),
                      ),
                    ),
    );
  }
}

class _LogTile extends StatelessWidget {
  const _LogTile({required this.log});
  final DailyLog log;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.calendar_today, size: 16, color: scheme.primary),
                const SizedBox(width: 6),
                Text(log.displayDate, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                if (log.isDemo) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: scheme.secondaryContainer,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text('Demo', style: TextStyle(fontSize: 10, color: scheme.onSecondaryContainer)),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _badge('Sleep', log.sleepHours == null ? '\u2014' : '${log.sleepHours!.toStringAsFixed(1)} h', scheme),
                _badge('Steps', log.steps?.toString() ?? '\u2014', scheme),
                _badge('Energy', log.energy?.toString() ?? '\u2014', scheme),
                _badge('Stress', log.stress?.toString() ?? '\u2014', scheme),
                _badge('Mood', log.mood?.label ?? '\u2014', scheme),
                _badge('Food', log.mealQuality?.label ?? '\u2014', scheme),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _badge(String label, String value, ColorScheme scheme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text.rich(
        TextSpan(children: [
          TextSpan(
            text: '$label ',
            style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant, fontWeight: FontWeight.w500),
          ),
          TextSpan(
            text: value,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
          ),
        ]),
      ),
    );
  }
}