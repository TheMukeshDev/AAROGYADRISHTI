/// Secondary (outlined) button in the design system.
library;

import 'package:flutter/material.dart';

class SecondaryButton extends StatelessWidget {
  const SecondaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.loading = false,
    this.loadingLabel,
    this.icon,
    this.leading,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading;
  final String? loadingLabel;
  final IconData? icon;
  final Widget? leading;

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null && !loading;
    return OutlinedButton(
      onPressed: enabled ? onPressed : null,
      child: loading
          ? Row(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2.4)),
                if (loadingLabel != null) ...[
                  const SizedBox(width: 10),
                  Flexible(child: Text(loadingLabel!, maxLines: 1, overflow: TextOverflow.ellipsis)),
                ],
              ],
            )
          : Row(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (leading != null) ...[leading!, const SizedBox(width: 8)],
                if (icon != null) ...[
                  Icon(icon, size: 20),
                  const SizedBox(width: 8),
                ],
                Flexible(child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis)),
              ],
            ),
    );
  }
}

/// A filled white button used on brand-colored surfaces.
class OnSurfacePrimaryButton extends StatelessWidget {
  const OnSurfacePrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return FilledButton(
      onPressed: onPressed,
      style: FilledButton.styleFrom(
        backgroundColor: Colors.white,
        foregroundColor: scheme.primary,
        disabledBackgroundColor: Colors.white.withValues(alpha: 0.6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (icon != null) ...[Icon(icon, size: 20), const SizedBox(width: 8)],
          Flexible(child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis)),
        ],
      ),
    );
  }
}