/// Global application constants.
///
/// Secrets and environment-specific values are read from `--dart-define`
/// overrides at build time so nothing sensitive is ever hardcoded. Example:
///
/// ```sh
/// flutter run \
///   --dart-define=API_BASE_URL=https://api.aarogyadrishti.in \
///   --dart-define=ENVIRONMENT=production
/// ```
class AppConstants {
  AppConstants._();

  static const String appName = 'AarogyaDrishti';
  static const String tagline = 'See Your Habits. Shape Your Health.';
  static const String phase = 'Phase 6';

  /// Base URL of the FastAPI backend. Default targets the local dev server.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const String apiV1Prefix = String.fromEnvironment(
    'API_V1_PREFIX',
    defaultValue: '/api/v1',
  );

  static const String environment = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: 'development',
  );

  static bool get isProduction => environment == 'production';

  /// Baseline window target (Phase 1 has no pattern detection).
  static const int baselineTargetDays = 7;
  static const int baselineWindowDays = 14;

  /// Local cache version - bump to force a client cache reset.
  static const int cacheVersion = 1;
}