/// Progress card showing baseline collection progress.
library;

import 'package:flutter/material.dart';

import '../models/health_data.dart';

class ProgressCard extends StatelessWidget {
  const ProgressCard({super.key, required this.baseline});

  final BaselineInfo baseline;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final progress = baseline.targetDays == 0
        ? 0.0
        : (baseline.daysRecorded / baseline.targetDays).clamp(0.0, 1.0);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [scheme.primaryContainer, scheme.secondaryContainer],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.insights, color: scheme.primary, size: 22),
              const SizedBox(width: 8),
              Text(
                'Baseline progress',
                style: TextStyle(fontWeight: FontWeight.w700, color: scheme.onPrimaryContainer),
              ),
              const Spacer(),
              Text(
                normalisedTrailing(progress),
                style: TextStyle(fontWeight: FontWeight.w700, color: scheme.primary),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: scheme.surfaceContainerHighest,
              color: scheme.primary,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            _message(scheme),
            style: TextStyle(fontSize: 13.5, color: scheme.onPrimaryContainer),
          ),
          Text(
            '${baseline.daysRecorded} day${baseline.daysRecorded == 1 ? '' : 's'} recorded',
            style: TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w600,
              color: scheme.onPrimaryContainer.withValues(alpha: 0.75),
            ),
          ),
        ],
      ),
    );
  }

  String normalisedTrailing(double p) => '${(p * 100).round()}%';

  String _message(ColorScheme scheme) =>
      baseline.message.isNotEmpty ? baseline.message : 'Keep checking in.';
}