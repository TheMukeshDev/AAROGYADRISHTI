/// Onboarding state machine (goals -> routine -> health permission).
library;

import 'package:flutter/foundation.dart';

import '../../core/storage/storage_service.dart';
import '../../models/app_enums.dart';

class OnboardingController extends ChangeNotifier {
  int _step = 0;
  int get step => _step;
  bool get isLast => _step == 2;

  // Goals (multi-select). At least one is required to continue.
  final List<PrimaryGoal> _goals = [];
  List<PrimaryGoal> get goals => List.unmodifiable(_goals);

  // Daily routine (all optional).
  double? _sleepHours;
  ActivityLevel? _activityLevel;
  WaterIntake? _waterIntake;
  MoodLevel? _stressLevel;

  double? get sleepHours => _sleepHours;
  ActivityLevel? get activityLevel => _activityLevel;
  WaterIntake? get waterIntake => _waterIntake;
  MoodLevel? get stressLevel => _stressLevel;

  // Health permissions (empty = manual only).
  final List<HealthDataTypeWrapper> _selectedHealth = [];
  List<HealthDataTypeWrapper> get selectedHealth => List.unmodifiable(_selectedHealth);

  bool get goalsSelected => _goals.isNotEmpty;

  bool get routineValid {
    return _activityLevel != null || _sleepHours != null || _waterIntake != null || _stressLevel != null;
  }

  bool get readyToFinish => goalsSelected;

  /// Toggle a goal; keep all selections (multi-select).
  void toggleGoal(PrimaryGoal goal) {
    if (_goals.contains(goal)) {
      _goals.remove(goal);
    } else {
      _goals.add(goal);
    }
    notifyListeners();
  }

  void setGoals(List<PrimaryGoal> goals) {
    _goals
      ..clear()
      ..addAll(goals);
    notifyListeners();
  }

  void setRoutine({
    double? sleepHours,
    ActivityLevel? activityLevel,
    WaterIntake? waterIntake,
    MoodLevel? stressLevel,
  }) {
    _sleepHours = sleepHours ?? _sleepHours;
    _activityLevel = activityLevel ?? _activityLevel;
    _waterIntake = waterIntake ?? _waterIntake;
    _stressLevel = stressLevel ?? _stressLevel;
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

  /// Persist the multi-select goals locally so preferences survive app
  /// restarts and are never silently overwritten later.
  Future<void> persistGoals() async {
    final storage = StorageService.instance;
    final wires = _goals.map((g) => g.wire).toList();
    await storage.setString(AppConstantsKeys.selectedGoalsKey, wires.isEmpty ? '' : wires.join(','));
  }

  Future<void> restoreSavedGoals() async {
    final storage = StorageService.instance;
    final raw = await storage.getString(AppConstantsKeys.selectedGoalsKey);
    if (raw == null || raw.isEmpty) return;
    final wires = raw.split(',').where((w) => w.isNotEmpty);
    final restored = wires
        .map(PrimaryGoal.fromWire)
        .whereType<PrimaryGoal>()
        .toList();
    if (restored.isNotEmpty && _goals.isEmpty) {
      setGoals(restored);
    }
  }
}

/// Internal key set for onboarding persistence.
class AppConstantsKeys {
  AppConstantsKeys._();

  static const String selectedGoalsKey = 'app.selected_goals';
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