/// Large-value metric card used on the dashboard.
///
/// Phase 1 explicitly does NOT render an AI/health score - only observed
/// values for a single day, with a gentle placeholder for missing data.
library;

import 'package:flutter/material.dart';

class MetricCard extends StatelessWidget {
  const MetricCard({
    super.key,
    required this.title,
    required this.value,
    this.unit,
    this.icon,
    this.valueColor,
    this.isEmpty = false,
  });

  final String title;
  final String value;
  final String? unit;
  final IconData? icon;
  final Color? valueColor;
  final bool isEmpty;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: scheme.outlineVariant, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              if (icon != null) ...[
                Icon(icon, size: 18, color: scheme.primary),
                const SizedBox(width: 6),
              ],
              Text(
                title,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          isEmpty
              ? Text(
                  '\u2014',
                  style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: scheme.outline),
                )
              : Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                        text: value,
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                          color: valueColor ?? scheme.onSurface,
                        ),
                      ),
                      if (unit != null)
                        TextSpan(
                          text: ' $unit',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: scheme.onSurfaceVariant,
                          ),
                        ),
                    ],
                  ),
                ),
        ],
      ),
    );
  }
}