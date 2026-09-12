/// Onboarding state machine (goal -> profile -> health permission).
library;

import 'package:flutter/foundation.dart';

import '../../models/app_enums.dart';
import '../../models/health_data.dart';

class OnboardingController extends ChangeNotifier {
  int _step = 0;
  int get step => _step;
  bool get isLast => _step == 2;

  // Goal
  PrimaryGoal? _goal;
  PrimaryGoal? get goal => _goal;

  // Profile
  String? _ageGroup;
  String? _gender;
  double? _heightCm;
  double? _weightKg;
  ActivityLevel? _activityLevel;
  String? get ageGroup => _ageGroup;
  String? get gender => _gender;
  double? get heightCm => _heightCm;
  double? get weightKg => _weightKg;
  ActivityLevel? get activityLevel => _activityLevel;

  // Health permissions (empty = manual only)
  final List<HealthDataTypeWrapper> _selectedHealth = [];
  List<HealthDataTypeWrapper> get selectedHealth => List.unmodifiable(_selectedHealth);

  bool get profileValid {
    return _goal != null && _activityLevel != null;
  }

  void setGoal(PrimaryGoal? g) {
    _goal = g;
    notifyListeners();
  }

  void setProfile({
    String? ageGroup,
    String? gender,
    double? heightCm,
    double? weightKg,
    ActivityLevel? activityLevel,
  }) {
    _ageGroup = ageGroup;
    _gender = gender;
    _heightCm = heightCm;
    _weightKg = weightKg;
    _activityLevel = activityLevel;
    notifyListeners();
  }

  void setHealthSelection(List<HealthDataTypeWrapper> types) {
    _selectedHealth
      ..clear()
      ..addAll(types);
    notifyListeners();
  }

  void next() {
    if (_step < 2) {
      _step += 1;
      notifyListeners();
    }
  }

  void back() {
    if (_step > 0) {
      _step -= 1;
      notifyListeners();
    }
  }
}

/// Value-object wrapper (data type + permission granted flag) so the UI can
/// show what the user actually approved with Health Connect.
class HealthDataTypeWrapper {
  final dynamic type;
  final String title;
  final String description;
  final bool granted;

  const HealthDataTypeWrapper({required this.type, required this.title, required this.description, this.granted = false});
}