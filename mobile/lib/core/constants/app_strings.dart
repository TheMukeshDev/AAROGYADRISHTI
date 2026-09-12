/// User-facing copy. Kept in one place so the entire product voice is
/// reviewable. Phase 1 language never makes medical or disease claims.
library;

class AppStrings {
  AppStrings._();

  // Brand
  static const String appName = 'AarogyaDrishti';
  static const String tagline = 'See Your Habits. Shape Your Health.';

  // Onboarding / welcome
  static const String welcomeTitle = 'Understand your everyday habits';
  static const String welcomeSubtitle =
      'Discover patterns that can help you build a healthier lifestyle - '
      'one small daily check-in at a time.';
  static const String getStarted = 'Get Started';
  static const String alreadyHaveAccount = 'Already have an account? Login';

  // Auth
  static const String login = 'Login';
  static const String signUp = 'Sign Up';
  static const String logout = 'Logout';
  static const String forgotPassword = 'Forgot password?';
  static const String emailHint = 'Email';
  static const String passwordHint = 'Password';
  static const String nameHint = 'Name';
  static const String createAccount = 'Create Account';
  static const String loginSubtitle =
      'Welcome back. Sign in to continue your lifestyle journey.';

  // Onboarding - goal
  static const String goalTitle = 'What would you like to improve?';
  static const String goalSubtitle =
      'Pick one primary focus. You can change it anytime.';

  // Health permission
  static const String healthPermissionTitle = 'Connect your health data';
  static const String healthPermissionBody =
      'AarogyaDrishti can use selected health data from your phone to reduce '
      'manual tracking. This is optional and you control what we can read.';
  static const String continueWithManual = 'Continue with manual tracking';

  // Dashboard
  static const String dashboardTitle = 'Your Lifestyle Snapshot';
  static const String morningHello = 'Good Morning';
  static const String afternoonHello = 'Good Afternoon';
  static const String eveningHello = 'Good Evening';
  static const String baselineLearning =
      'Keep checking in. We\u2019re learning your baseline.';
  static const String baselineReady = 'Your baseline is ready.';

  // Check-in
  static const String checkInTitle = 'Daily Check-in';
  static const String checkInSubtitle = 'Takes less than a minute.';
  static const String saveCheckIn = 'Save check-in';
  static const String checkInSaved = 'Check-in saved';

  // Errors / states
  static const String noInternet = 'No internet connection. Please try again.';
  static const String apiUnavailable =
      'We could not reach our servers. Please try again shortly.';
  static const String somethingWentWrong = 'Something went wrong. Please try again.';
  static const String sessionExpired = 'Your session has expired. Please sign in again.';
  static const String permissionDenied =
      'You can continue with manual tracking instead.';
  static const String healthConnectUnavailable =
      'Health Connect is not available on this device. You can continue with '
      'manual tracking.';
  static const String emptyHealthData =
      'No health data found for this period yet.';
  static const String duplicateCheckIn =
      'You already checked in for today. You can update it from History.';

  // History
  static const String historyTitle = 'History';
  static const String historyEmpty =
      'No check-ins yet. Your daily entries will show up here.';

  // Profile
  static const String profileTitle = 'Profile';
  static const String connectedHealthSources = 'Connected health sources';
  static const String permissions = 'Permissions';
  static const String deleteAccount = 'Delete account';
}