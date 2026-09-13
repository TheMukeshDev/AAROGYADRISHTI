/// Error message & dismissible banner components.
library;

import 'package:flutter/material.dart';

/// Inline error text shown directly below a form field / section.
class ErrorMessage extends StatelessWidget {
  const ErrorMessage(this.message, {super.key});

  final String? message;

  @override
  Widget build(BuildContext context) {
    if (message == null || message!.isEmpty) return const SizedBox.shrink();
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.error_outline, size: 16, color: scheme.error),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              message!,
              style: TextStyle(fontSize: 13, height: 1.35, color: scheme.error),
            ),
          ),
        ],
      ),
    );
  }
}

/// Dismissible error banner for backend / network failures.
class DismissibleErrorBanner extends StatefulWidget {
  const DismissibleErrorBanner({super.key, this.message, this.onDismiss});

  final String? message;
  final VoidCallback? onDismiss;

  @override
  State<DismissibleErrorBanner> createState() => _DismissibleErrorBannerState();
}

class _DismissibleErrorBannerState extends State<DismissibleErrorBanner> {
  bool _hidden = false;

  @override
  Widget build(BuildContext context) {
    if (_hidden || widget.message == null || widget.message!.isEmpty) {
      return const SizedBox.shrink();
    }
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 8, 12),
      decoration: BoxDecoration(
        color: scheme.errorContainer,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: Icon(Icons.cloud_off_outlined, size: 18, color: scheme.onErrorContainer),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              widget.message!,
              style: TextStyle(fontSize: 13.5, height: 1.4, color: scheme.onErrorContainer),
            ),
          ),
          IconButton(
            onPressed: () {
              setState(() => _hidden = true);
              widget.onDismiss?.call();
            },
            visualDensity: VisualDensity.compact,
            icon: Icon(Icons.close, size: 18, color: scheme.onErrorContainer),
          ),
        ],
      ),
    );
  }
}

/// Shows a brief floating snackbar.
void showAppSnack(BuildContext context, String message, {bool error = false}) {
  final scheme = Theme.of(context).colorScheme;
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              error ? Icons.error_outline : Icons.check_circle_outline,
              size: 18,
              color: error ? scheme.errorContainer : scheme.inverseSurface,
            ),
            const SizedBox(width: 10),
            Expanded(child: Text(message)),
          ],
        ),
      ),
    );
}