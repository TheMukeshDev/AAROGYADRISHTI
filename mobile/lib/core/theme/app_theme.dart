/// AarogyaDrishti design system (Material 3).
///
/// Visual language: premium, calm, trustworthy, privacy-first wellness.
/// - Deep teal primary, emerald accent, soft mint containers
/// - Off-white surfaces, dark charcoal text, muted gray secondary
/// - 16-24px card radius, thin subtle borders, 8px spacing system
library;

import 'package:flutter/material.dart';

import '../constants/app_constants.dart';

class AppTheme {
  AppTheme._();

  /// Teal-green seed - energy + wellness, not clinical white/blue.
  static const Color _seed = AppColors.deepTeal;

  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(
      seedColor: _seed,
      brightness: Brightness.light,
    ).copyWith(
      primary: AppColors.deepTeal,
      onPrimary: Colors.white,
      primaryContainer: AppColors.mint,
      onPrimaryContainer: const Color(0xFF06312A),
      secondary: AppColors.emerald,
      onSecondary: Colors.white,
      secondaryContainer: const Color(0xFFD3F5E8),
      onSecondaryContainer: const Color(0xFF0A3B2E),
      tertiary: const Color(0xFF2F7D6B),
      surface: AppColors.offWhite,
      onSurface: AppColors.charcoal,
      onSurfaceVariant: AppColors.mutedGray,
      surfaceContainer: const Color(0xFFF2F7F5),
      surfaceContainerLow: const Color(0xFFF6FAF8),
      surfaceContainerHigh: const Color(0xFFE6EDEA),
      surfaceContainerHighest: const Color(0xFFDDE7E3),
      outline: const Color(0xFFB7C6C0),
      outlineVariant: const Color(0xFFDDE7E3),
      error: const Color(0xFFBA1A1A),
      onError: Colors.white,
      errorContainer: const Color(0xFFFFDAD6),
      onErrorContainer: const Color(0xFF410002),
      scrim: const Color(0xFF111816),
    );
    return _base(scheme, Brightness.light);
  }

  static ThemeData dark() {
    final scheme = ColorScheme.fromSeed(
      seedColor: _seed,
      brightness: Brightness.dark,
    ).copyWith(
      primary: const Color(0xFF78D8C5),
      onPrimary: const Color(0xFF082018),
      primaryContainer: const Color(0xFF0D443B),
      onPrimaryContainer: const Color(0xFFA8F2E1),
      secondary: const Color(0xFF71D8AF),
      onSecondary: const Color(0xFF06301F),
      secondaryContainer: const Color(0xFF0E4A33),
      onSecondaryContainer: const Color(0xFFB0F2CE),
      tertiary: const Color(0xFF8FD9C5),
      surface: const Color(0xFF101615),
      onSurface: const Color(0xFFE3E9E6),
      onSurfaceVariant: const Color(0xFFA6B5AF),
      surfaceContainer: const Color(0xFF1B2220),
      surfaceContainerLow: const Color(0xFF171D1B),
      surfaceContainerHigh: const Color(0xFF262D2B),
      surfaceContainerHighest: const Color(0xFF313936),
      outline: const Color(0xFF6E7D77),
      outlineVariant: const Color(0xFF2E3733),
      error: const Color(0xFFFFB4AB),
      onError: const Color(0xFF690005),
      errorContainer: const Color(0xFF93000A),
      onErrorContainer: const Color(0xFFFFDAD6),
      scrim: const Color(0xFF000000),
    );
    return _base(scheme, Brightness.dark);
  }

  static ThemeData _base(ColorScheme scheme, Brightness brightness) {
    InputDecorationTheme inputTheme() {
      final fill = scheme.surfaceContainerHighest.withValues(alpha: 0.55);
      final border = OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: BorderSide.none,
      );
      return InputDecorationTheme(
        filled: true,
        fillColor: fill,
        border: border,
        enabledBorder: border,
        errorBorder: border,
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide(color: scheme.error, width: 1.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide(color: scheme.primary, width: 1.6),
        ),
        floatingLabelStyle: TextStyle(color: scheme.primary, fontWeight: FontWeight.w600),
        labelStyle: TextStyle(color: scheme.onSurfaceVariant),
        hintStyle: TextStyle(color: scheme.onSurfaceVariant.withValues(alpha: 0.8)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
        prefixIconColor: scheme.onSurfaceVariant,
        suffixIconColor: scheme.onSurfaceVariant,
      );
    }

    final cardShape = RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(20),
      side: BorderSide(color: scheme.outlineVariant.withValues(alpha: 0.9), width: 1),
    );

    final textTheme = Typography.material2021(platform: TargetPlatform.android)
        .black
        .apply(
          bodyColor: scheme.onSurface,
          displayColor: scheme.onSurface,
          fontSizeFactor: 1.0,
        )
        .copyWith(
          displaySmall: TextStyle(
            fontSize: 36,
            height: 1.12,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.5,
            color: scheme.onSurface,
          ),
          headlineMedium: TextStyle(
            fontSize: 28,
            height: 1.18,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.3,
            color: scheme.onSurface,
          ),
          titleLarge: TextStyle(
            fontSize: 22,
            height: 1.22,
            fontWeight: FontWeight.w700,
            color: scheme.onSurface,
          ),
          titleMedium: TextStyle(
            fontSize: 16,
            height: 1.3,
            fontWeight: FontWeight.w600,
            color: scheme.onSurface,
          ),
          bodyLarge: TextStyle(
            fontSize: 16,
            height: 1.5,
            color: scheme.onSurface,
          ),
          bodyMedium: TextStyle(
            fontSize: 14.5,
            height: 1.45,
            color: scheme.onSurface,
          ),
          labelLarge: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scheme.surface,
      splashFactory: InkSparkle.splashFactory,
      visualDensity: VisualDensity.standard,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        centerTitle: false,
        elevation: 0,
        scrolledUnderElevation: 0,
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: textTheme.titleLarge,
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: scheme.surfaceContainerLow,
        shape: cardShape,
        margin: EdgeInsets.zero,
        clipBehavior: Clip.antiAlias,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(54),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(54),
          side: BorderSide(color: scheme.primary, width: 1.4),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
          foregroundColor: scheme.primary,
        ),
      ),
      inputDecorationTheme: inputTheme(),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: scheme.surfaceContainer,
        indicatorColor: scheme.primaryContainer,
        height: 64 + 8,
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(
            color: selected ? scheme.primary : scheme.onSurfaceVariant,
            size: 24,
          );
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? scheme.primary : scheme.onSurfaceVariant,
          );
        }),
      ),
      dividerTheme: DividerThemeData(color: scheme.outlineVariant, thickness: 1, space: 1),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: scheme.inverseSurface,
        contentTextStyle: TextStyle(color: scheme.onInverseSurface, fontSize: 14.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: scheme.surfaceContainerHighest,
        selectedColor: scheme.primaryContainer,
        labelStyle: TextStyle(color: scheme.onSurface, fontWeight: FontWeight.w600, fontSize: 14),
        secondaryLabelStyle: TextStyle(color: scheme.onPrimaryContainer, fontWeight: FontWeight.w600, fontSize: 14),
        side: BorderSide(color: scheme.outlineVariant),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: scheme.primary,
        inactiveTrackColor: scheme.surfaceContainerHighest,
        thumbColor: scheme.primary,
        overlayColor: scheme.primary.withValues(alpha: 0.12),
        trackHeight: 6,
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? scheme.primary
              : scheme.onSurfaceVariant,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? scheme.primaryContainer
              : scheme.surfaceContainerHighest,
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        titleTextStyle: textTheme.titleLarge,
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        showDragHandle: true,
      ),
      // Give the Material color scheme a subtle surface tint for cards.
      // (kept explicit and subtle: no gradient overdose)
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith(
          (states) => states.contains(WidgetState.selected)
              ? scheme.primary
              : Colors.transparent,
        ),
        side: BorderSide(color: scheme.onSurfaceVariant, width: 1.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(5)),
      ),
    );
  }

  /// Standard card title style.
  static const TextStyle cardTitle =
      TextStyle(fontSize: 17, fontWeight: FontWeight.w700, height: 1.25);
}