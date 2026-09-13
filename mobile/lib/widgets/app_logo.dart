/// AarogyaDrishti brand mark + wordmark.
///
/// The mark is drawn as a vector (CustomPainter) so it renders crisply at any
/// size with no background square - consistent with the adapative launcher
/// icon and safe for light/dark surfaces.
library;

import 'package:flutter/material.dart';

import '../../core/constants/app_constants.dart';

/// Draws the brand glyph: an eye (Drishti = sight) holding a heartbeat pulse.
class LogoMarkPainter extends CustomPainter {
  const LogoMarkPainter({
    this.backgroundColor,
    this.foregroundColor,
    this.roundCorners = true,
  });

  final Color? backgroundColor;
  final Color? foregroundColor;
  final bool roundCorners;

  @override
  void paint(Canvas canvas, Size size) {
    final bg = backgroundColor ?? AppColors.deepTeal;
    final fg = foregroundColor ?? Colors.white;

    final w = size.width;
    final rect = Offset.zero & size;

    // Rounded plate.
    final path = Path()
      ..moveTo(0, size.height * 0.5)
      ..lineTo(0, size.height - size.height * 0.24)
      ..quadraticBezierTo(0, size.height, size.width * 0.24, size.height)
      ..lineTo(size.width - size.width * 0.24, size.height)
      ..quadraticBezierTo(size.width, size.height, size.width, size.height - size.height * 0.24)
      ..lineTo(size.width, size.height * 0.24)
      ..quadraticBezierTo(size.width, 0, size.width - size.width * 0.24, 0)
      ..lineTo(size.width * 0.24, 0)
      ..quadraticBezierTo(0, 0, 0, size.height * 0.24)
      ..close();
    canvas.drawPath(roundCorners ? path : Path()..addRect(rect), Paint()..color = bg);

    // --- Eye ---
    final paint = Paint()
      ..color = fg
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.055
      ..strokeCap = StrokeCap.round;

    final rectL = Rect.fromCenter(
      center: Offset(w * 0.5, w * 0.5),
      width: w * 0.62,
      height: w * 0.34,
    );
    // Almond shape: upper lid + lower lid arcs.
    final upperPath = Path()
      ..moveTo(rectL.left, rectL.center.dy)
      ..quadraticBezierTo(
        rectL.center.dx,
        rectL.top - w * 0.03,
        rectL.right,
        rectL.center.dy,
      );
    final lowerPath = Path()
      ..moveTo(rectL.left, rectL.center.dy)
      ..quadraticBezierTo(
        rectL.center.dx,
        rectL.bottom - w * 0.02,
        rectL.right,
        rectL.center.dy,
      );
    canvas.drawPath(upperPath, paint);
    canvas.drawPath(lowerPath, paint);

    // Pupil.
    canvas.drawCircle(rectL.center, w * 0.075, Paint()..color = fg);

    // --- Heartbeat pulse inside the eye ---
    final pulse = Paint()
      ..color = fg
      ..style = PaintingStyle.stroke
      ..strokeWidth = w * 0.05
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    final cx = w * 0.5;
    final cy = w * 0.5;
    final half = w * 0.16;
    final sigAmp = w * 0.13;
    final pulsePath = Path()
      ..moveTo(cx - half, cy)
      ..lineTo(cx - half * 0.45, cy)
      ..lineTo(cx - half * 0.15, cy - sigAmp)
      ..lineTo(cx + half * 0.15, cy + sigAmp * 0.85)
      ..lineTo(cx + half * 0.5, cy)
      ..lineTo(cx + half, cy);
    canvas.drawPath(pulsePath, pulse);
  }

  @override
  bool shouldRepaint(covariant LogoMarkPainter old) =>
      old.backgroundColor != backgroundColor ||
      old.foregroundColor != foregroundColor ||
      old.roundCorners != roundCorners;
}

/// The brand mark as a widget.
class LogoMark extends StatelessWidget {
  const LogoMark({super.key, this.size = 56, this.backgroundColor, this.foregroundColor});

  final double size;
  final Color? backgroundColor;
  final Color? foregroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      color: backgroundColor,
      clipBehavior: Clip.hardEdge,
      child: Transform.translate(
        offset: Offset(0, -size * 0.22),
        child: Transform.scale(
          scale: 1.55,
          child: Image.asset(
            'assets/images/AarogyaDrishti.png',
            width: size,
            height: size,
            fit: BoxFit.fill,
            color: foregroundColor,
            colorBlendMode: foregroundColor == null ? null : BlendMode.srcIn,
            errorBuilder: (_, __, ___) => CustomPaint(
              painter: LogoMarkPainter(
                backgroundColor: backgroundColor,
                foregroundColor: foregroundColor,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Brand wordmark + optional tagline, optionally paired with [LogoMark].
class AppLogo extends StatelessWidget {
  const AppLogo({
    super.key,
    this.size = 72,
    this.showMark = true,
    this.showTagline = false,
    this.logoBackground,
    this.logoForeground,
    this.textColor,
    this.titleFontSize = 26,
  });

  final double size;
  final bool showMark;
  final bool showTagline;
  final Color? logoBackground;
  final Color? logoForeground;
  final Color? textColor;
  final double titleFontSize;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final color = textColor ?? scheme.onSurface;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (showMark) ...[
          LogoMark(
            size: size,
            backgroundColor: logoBackground,
            foregroundColor: logoForeground,
          ),
          const SizedBox(height: 18),
        ],
        Text(
          AppConstants.appName,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: color,
            fontSize: titleFontSize,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.3,
            height: 1.1,
          ),
        ),
        if (showTagline) ...[
          const SizedBox(height: 8),
          Text(
            AppConstants.tagline,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: color.withValues(alpha: 0.78),
              fontSize: 15,
              fontWeight: FontWeight.w500,
              letterSpacing: 0.4,
            ),
          ),
        ],
      ],
    );
  }
}