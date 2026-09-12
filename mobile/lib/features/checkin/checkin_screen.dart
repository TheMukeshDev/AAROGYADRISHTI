/// Daily check-in screen - designed to complete in 30-60 seconds.
///
/// Fields are deliberately simple single-tap choices. Subjective inputs
/// (energy, stress, mood, food, water, exercise) + optional caffeine and
/// late-night screen.
/// Phase 1 has NO calorie counting.
library;

import 'package:flutter/material.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../core/utils/date_utils.dart';
import '../../models/app_enums.dart';
import '../../repositories/daily_log_repository.dart';
import '../../widgets/checkin_option.dart';
import '../../widgets/primary_button.dart';
import '../../app.dart';

class CheckinScreen extends StatefulWidget {
  const CheckinScreen({super.key});

  @override
  State<CheckinScreen> createState() => _CheckinScreenState();
}

class _CheckinScreenState extends State<CheckinScreen> {
  final _energy = _RatingSelection(1, 10);
  final _stress = _RatingSelection(1, 5);

  ExerciseLevel? _exercise;
  MealQuality? _food;
  WaterIntake? _water;
  MoodLevel? _mood;
  double? _sleepHours;
  SleepQuality? _sleepQuality;
  CaffeineLevel? _caffeine;
  bool? _lateNightScreen;

  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadToday();
  }

  Future<void> _loadToday() async {
    try {
      final repo = DailyLogRepository(AppServices.instance.api);
      final existing = await repo.getByDate(AppDateUtils.todayIso());
      if (existing != null && mounted) {
        _apply(existing);
      }
    } catch (_) {
      // Fresh check-in otherwise.
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _apply(dynamic log) {
    _energy.value = log.energy;
    _stress.value = log.stress;
    _exercise = log.exerciseLevel;
    _food = log.mealQuality;
    _water = _waterFromWire('${log.waterLiters}');
    _mood = log.mood;
    _sleepHours = log.sleepHours;
    _sleepQuality = log.sleepQuality;
    _caffeine = log.caffeine;
    _lateNightScreen = log.lateNightScreen;
  }

  WaterIntake? _waterFromWire(String value) {
    final liters = double.tryParse(value);
    if (liters == null) return null;
    if (liters < 1) return WaterIntake.low;
    if (liters < 2) return WaterIntake.medium;
    if (liters < 3) return WaterIntake.high;
    return WaterIntake.veryHigh;
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });

    final body = <String, dynamic>{
      'date': AppDateUtils.todayIso(),
      'energy': _energy.value,
      'stress': _stress.value,
      'exercise_level': _exercise?.wire,
      'exercise_minutes': _exercise?.minutes,
      'meal_quality': _food?.wire,
      'water_liters': _waterLitres,
      'mood': _mood?.wire,
      'sleep_hours': _sleepHours,
      'sleep_quality': _sleepQuality?.wire,
      'caffeine': _caffeine?.wire,
      'late_night_screen': _lateNightScreen,
      'source': 'manual',
    };

    try {
      final repo = DailyLogRepository(AppServices.instance.api);
      final existing = await repo.getByDate(AppDateUtils.todayIso());
      if (existing != null) {
        body.remove('date');
        await repo.update(AppDateUtils.todayIso(), body);
      } else {
        await repo.create(body);
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text(AppStrings.checkInSaved)),
        );
      }
    } on RequestFailedException catch (e) {
      if (mounted) setState(() => _error = e.code == 'conflict' ? AppStrings.duplicateCheckIn : e.message);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  double? get _waterLitres {
    switch (_water) {
      case WaterIntake.low:
        return 0.5;
      case WaterIntake.medium:
        return 1.5;
      case WaterIntake.high:
        return 2.5;
      case WaterIntake.veryHigh:
        return 3.5;
      default:
        return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.checkInTitle),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Text(
                AppStrings.checkInSubtitle,
                style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant),
              ),
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _section('1. Energy today', widget: _energySlider(scheme)),
                        const SizedBox(height: 20),
                        _section('2. Stress today', widget: _stressSlider(scheme)),
                        const SizedBox(height: 20),
                        _section('3. Sleep last night', widget: _sleepPicker(scheme)),
                        const SizedBox(height: 20),
                        _section('4. Exercise today', widget: _exercisePicker()),
                        const SizedBox(height: 20),
                        _section('5. Food today', widget: _foodPicker()),
                        const SizedBox(height: 20),
                        _section('6. Water intake', widget: _waterPicker()),
                        const SizedBox(height: 20),
                        _section('7. Mood', widget: _moodPicker()),
                        const SizedBox(height: 20),
                        _section('Optional', widget: _optionalPicker(scheme)),
                        const SizedBox(height: 8),
                        if (_error != null)
                          Text(_error!, style: TextStyle(color: scheme.error, fontSize: 14)),
                      ],
                    ),
                  ),
                ),
                SafeArea(
                  top: false,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                    child: PrimaryButton(
                      label: AppStrings.saveCheckIn,
                      icon: Icons.check,
                      loading: _saving,
                      onPressed: _save,
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _section(String title, {required Widget widget}) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          const SizedBox(height: 10),
          widget,
        ],
      );

  Widget _energySlider(ColorScheme scheme) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('1 (low)', style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant)),
            Text(_energy.value == null ? 'Select' : '${_energy.value}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            Text('10 (high)', style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant)),
          ],
        ),
        Slider(
          value: (_energy.value ?? 5).toDouble(),
          min: 1,
          max: 10,
          divisions: 9,
          label: '${_energy.value}',
          onChanged: (v) => setState(() => _energy.value = v.round()),
        ),
      ],
    );
  }

  Widget _stressSlider(ColorScheme scheme) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('1 (calm)', style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant)),
            Text(_stress.value == null ? 'Select' : '${_stress.value}', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            Text('5 (high)', style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant)),
          ],
        ),
        Slider(
          value: (_stress.value ?? 3).toDouble(),
          min: 1,
          max: 5,
          divisions: 4,
          label: '${_stress.value}',
          onChanged: (v) => setState(() => _stress.value = v.round()),
        ),
      ],
    );
  }

  Widget _sleepPicker(ColorScheme scheme) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('Hours of sleep', style: TextStyle(fontWeight: FontWeight.w600)),
            Text(
              _sleepHours == null ? '0.0 h' : '${_sleepHours!.toStringAsFixed(1)} h',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
            ),
          ],
        ),
        Slider(
          value: (_sleepHours ?? 7).clamp(3, 12),
          min: 3,
          max: 12,
          divisions: 18,
          onChanged: (v) {
            final halfSteps = (v * 2).round();
            setState(() => _sleepHours = halfSteps / 2);
          },
        ),
        Text('Sleep quality (optional)', style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
        const SizedBox(height: 8),
        Row(
          children: SleepQuality.values.map((q) => Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 3),
                  child: ChoiceChip(
                    label: Text(q.label),
                    selected: _sleepQuality == q,
                    onSelected: (_) => setState(() => _sleepQuality = q),
                  ),
                ),
              )).toList(),
        ),
      ],
    );
  }

  Widget _exercisePicker() => Column(
        children: ExerciseLevel.values.map((e) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: CheckinOption(
                label: e.label,
                selected: _exercise == e,
                onTap: () => setState(() => _exercise = _exercise == e ? null : e),
              ),
            )).toList(),
      );

  Widget _foodPicker() => Column(
        children: MealQuality.values.map((m) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: CheckinOption(
                label: m.label,
                selected: _food == m,
                onTap: () => setState(() => _food = _food == m ? null : m),
              ),
            )).toList(),
      );

  Widget _waterPicker() => Column(
        children: WaterIntake.values.map((w) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: CheckinOption(
                label: w.label,
                selected: _water == w,
                onTap: () => setState(() => _water = _water == w ? null : w),
              ),
            )).toList(),
      );

  Widget _moodPicker() => Column(
        children: MoodLevel.values.map((m) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: CheckinOption(
                label: m.label,
                selected: _mood == m,
                onTap: () => setState(() => _mood = _mood == m ? null : m),
              ),
            )).toList(),
      );

  Widget _optionalPicker(ColorScheme scheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Caffeine', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: CaffeineLevel.values.map((c) => ChoiceChip(
                label: Text(c.label),
                selected: _caffeine == c,
                onSelected: (_) => setState(() => _caffeine = _caffeine == c ? null : c),
              )).toList(),
        ),
        const SizedBox(height: 14),
        CheckinOption(
          label: 'Late night screen usage',
          subtitle: 'Using screen after midnight',
          selected: _lateNightScreen == true,
          onTap: () => setState(() => _lateNightScreen = _lateNightScreen == true ? null : true),
        ),
      ],
    );
  }
}

class _RatingSelection {
  _RatingSelection(this.min, this.max);
  final int min;
  final int max;
  int? value;
}