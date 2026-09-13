/// Daily check-in screen - quick, friendly lifestyle logging.
///
/// Structure follows the product spec:
/// 1. Mood (5 states)  2. Sleep  3. Energy  4. Stress  5. Hydration  6. Activity
/// Saves to the backend, then shows a confirmation state. Saving is guarded
/// against accidental double-submission.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/constants/app_constants.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../core/utils/date_utils.dart';
import '../../models/app_enums.dart';
import '../../models/daily_log.dart';
import '../../repositories/daily_log_repository.dart';
import '../../widgets/error_message.dart';
import '../../widgets/primary_button.dart';
import '../../app.dart';

class CheckinScreen extends StatefulWidget {
  const CheckinScreen({super.key});

  @override
  State<CheckinScreen> createState() => _CheckinScreenState();
}

class _CheckinScreenState extends State<CheckinScreen> {
  MoodLevel? _mood;
  double? _sleepHours;
  SleepQuality? _sleepQuality;
  _LevelChoice? _energy;
  _LevelChoice? _stress;
  int _cups = 0;
  int _stepsValue = 0;
  final _stepsCtrl = TextEditingController();
  ExerciseLevel? _exercise;
  MealQuality? _meal;
  CaffeineLevel? _caffeine;

  bool _loading = true;
  bool _saving = false;
  bool _saved = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadToday();
  }

  @override
  void dispose() {
    _stepsCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadToday() async {
    try {
      final repo = DailyLogRepository(AppServices.instance.api);
      final existing = await repo.getByDate(AppDateUtils.todayIso());
      if (existing != null && mounted) _apply(existing);
    } catch (_) {
      // Fresh check-in otherwise.
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _apply(DailyLog log) {
    _mood = log.mood;
    _sleepHours = log.sleepHours;
    _sleepQuality = log.sleepQuality;
    _energy = _LevelChoice.fromRating(log.energy);
    _stress = _LevelChoice.fromRating(log.stress, scale: 5);
    _cups = log.waterLiters == null ? 0 : (log.waterLiters! / 0.25).round();
    _stepsValue = log.steps ?? 0;
    _stepsCtrl.text = _stepsValue == 0 ? '' : '$_stepsValue';
    _exercise = log.exerciseLevel;
    _meal = log.mealQuality;
    _caffeine = log.caffeine;
  }

  Future<void> _save() async {
    if (_saving) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _saving = true;
      _error = null;
    });

    final body = <String, dynamic>{
      'date': AppDateUtils.todayIso(),
      'mood': _mood?.wire,
      'sleep_hours': _sleepHours,
      'sleep_quality': _sleepQuality?.wire,
      'energy': _energy?.energy,
      'stress': _stress?.stress,
      'water_liters': _cups * 0.25,
      'steps': _stepsValue > 0 ? _stepsValue : null,
      'exercise_level': _exercise?.wire,
      'exercise_minutes': _exercise?.minutes,
      'meal_quality': _meal?.wire,
      'caffeine': _caffeine?.wire,
      'late_night_screen': null,
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
      if (mounted) setState(() => _saved = true);
    } on RequestFailedException catch (e) {
      if (mounted) {
        setState(() => _error = e.code == 'conflict' ? AppStrings.duplicateCheckIn : e.message);
      }
    } on NetworkException {
      if (mounted) setState(() => _error = AppStrings.noInternet);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.errSignup);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: const Text(AppStrings.checkInTitle),
        automaticallyImplyLeading: !_saved,
        actions: [
          if (!_saved)
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
          : _saved
              ? _Confirmation(
                  onDone: () => Navigator.of(context).maybePop(),
                )
              : Column(
                  children: [
                    Expanded(
                      child: SingleChildScrollView(
                        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                        padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _sectionLabel(Icons.mood_outlined, AppStrings.moodQuestion, scheme),
                            const SizedBox(height: 10),
                            _moodPicker(scheme),
                            const SizedBox(height: 24),
                            _sectionLabel(Icons.bedtime_outlined, AppStrings.sleepQuestion, scheme),
                            const SizedBox(height: 6),
                            _sleepPicker(scheme),
                            const SizedBox(height: 24),
                            _sectionLabel(Icons.bolt_outlined, AppStrings.energyQuestion, scheme),
                            const SizedBox(height: 10),
                            _levelPicker(
                              selected: _energy,
                              onChanged: (v) => setState(() => _energy = v),
                            ),
                            const SizedBox(height: 24),
                            _sectionLabel(Icons.spa_outlined, AppStrings.stressQuestion, scheme),
                            const SizedBox(height: 10),
                            _levelPicker(
                              selected: _stress,
                              onChanged: (v) => setState(() => _stress = v),
                            ),
                            const SizedBox(height: 24),
                            _sectionLabel(Icons.water_drop_outlined, AppStrings.waterQuestion, scheme),
                            const SizedBox(height: 6),
                            _waterPicker(scheme),
                            const SizedBox(height: 24),
                            _sectionLabel(Icons.directions_run_rounded, AppStrings.activityQuestion, scheme),
                            const SizedBox(height: 4),
                            Text(
                              'Optional - you can also import this from Health Connect.',
                              style: TextStyle(fontSize: 12.5, color: scheme.onSurfaceVariant),
                            ),
                            const SizedBox(height: 10),
                            _activityPicker(scheme),
                            const SizedBox(height: 20),
                            _optionalExtras(scheme),
                            if (_error != null) ...[
                              const SizedBox(height: 16),
                              ErrorMessage(_error!),
                            ],
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
                          icon: Icons.check_rounded,
                          loading: _saving,
                          onPressed: _save,
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _sectionLabel(IconData icon, String label, ColorScheme scheme) {
    return Row(
      children: [
        Icon(icon, size: 18, color: scheme.primary),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
      ],
    );
  }

  // --- Mood: 5 distict states -------------------------------
  Widget _moodPicker(ColorScheme scheme) {
    const moods = <(MoodLevel, IconData)>[
      (MoodLevel.veryLow, Icons.sentiment_very_dissatisfied),
      (MoodLevel.low, Icons.sentiment_dissatisfied),
      (MoodLevel.okay, Icons.sentiment_neutral),
      (MoodLevel.good, Icons.sentiment_satisfied),
      (MoodLevel.great, Icons.sentiment_very_satisfied),
    ];
    return Row(
      children: [
        for (final (mood, icon) in moods) ...[
          Expanded(
            child: _MoodButton(
              icon: icon,
              label: mood.label,
              selected: _mood == mood,
              onTap: () => setState(() => _mood = _mood == mood ? null : mood),
            ),
          ),
          if (mood != moods.last.$1) const SizedBox(width: 6),
        ],
      ],
    );
  }

  // --- Sleep: hours slider + quality ------------------------
  Widget _sleepPicker(ColorScheme scheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Hours of sleep', style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
            Text(
              _sleepHours == null ? 'Select' : '${_sleepHours!.toStringAsFixed(1)} h',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
            ),
          ],
        ),
        Slider(
          value: (_sleepHours ?? 7).clamp(3, 12),
          min: 3,
          max: 12,
          divisions: 18,
          label: _sleepHours == null ? null : '${_sleepHours!.toStringAsFixed(1)} h',
          onChanged: (v) {
            final halfSteps = (v * 2).round();
            setState(() => _sleepHours = halfSteps / 2);
          },
        ),
        if (_sleepHours != null) ...[
          Text('Sleep quality', style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
          const SizedBox(height: 8),
          Row(
            children: SleepQuality.values.map((q) => Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: ChoiceChip(
                      label: Text(q.label),
                      selected: _sleepQuality == q,
                      onSelected: (_) => setState(() => _sleepQuality = _sleepQuality == q ? null : q),
                    ),
                  ),
                )).toList(),
          ),
        ],
      ],
    );
  }

  // --- Energy / Stress: Low | Medium | High -----------------
  Widget _levelPicker({required _LevelChoice? selected, required ValueChanged<_LevelChoice> onChanged}) {
    return Row(
      children: [
        for (final level in _LevelChoice.values) ...[
          Expanded(
            child: _LevelButton(
              label: level.label,
              selected: selected == level,
              onTap: () => onChanged(level),
            ),
          ),
          if (level != _LevelChoice.values.last) const SizedBox(width: 8),
        ],
      ],
    );
  }

  // --- Hydration: cups stepper ------------------------------
  Widget _waterPicker(ColorScheme scheme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: scheme.outlineVariant, width: 1),
      ),
      child: Row(
        children: [
          const Icon(Icons.local_drink_outlined, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _cups == 0 ? 'No water logged yet' : '$_cups cup${_cups == 1 ? '' : 's'}',
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                ),
                Text(
                  _cups == 0 ? 'Tap + when you finish a glass' : '${(_cups * 0.25).toStringAsFixed(1)} litres',
                  style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => setState(() => _cups = (_cups - 1).clamp(0, 16)),
            icon: const Icon(Icons.remove_circle_outline),
            tooltip: 'Remove cup',
          ),
          IconButton(
            onPressed: () => setState(() => _cups = (_cups + 1).clamp(0, 16)),
            icon: const Icon(Icons.add_circle, color: AppColors.deepTeal),
            tooltip: 'Add cup',
          ),
        ],
      ),
    );
  }

  // --- Activity: steps + exercise level ---------------------
  Widget _activityPicker(ColorScheme scheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _stepsCtrl,
          keyboardType: TextInputType.number,
          textInputAction: TextInputAction.done,
          inputFormatters: [
            _DigitsOnlyFormatter(),
          ],
          decoration: const InputDecoration(
            labelText: 'Steps (optional)',
            hintText: 'e.g. 8000',
            prefixIcon: Icon(Icons.directions_walk_rounded),
          ),
          onChanged: (v) => setState(() => _stepsValue = int.tryParse(v) ?? 0),
        ),
        const SizedBox(height: 12),
        Text('Exercise', style: TextStyle(fontSize: 13, color: scheme.onSurfaceVariant)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: ExerciseLevel.values.map((e) => ChoiceChip(
                label: Text(e.label),
                selected: _exercise == e,
                onSelected: (_) => setState(() => _exercise = _exercise == e ? null : e),
              )).toList(),
        ),
      ],
    );
  }

  Widget _optionalExtras(ColorScheme scheme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Anything else? (optional)',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: scheme.onSurface),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            ...MealQuality.values.map((m) => ChoiceChip(
                  avatar: const Icon(Icons.restaurant_outlined, size: 16),
                  label: Text(m.label),
                  selected: _meal == m,
                  onSelected: (_) => setState(() => _meal = _meal == m ? null : m),
                )),
            ...CaffeineLevel.values.map((c) => ChoiceChip(
                  avatar: const Icon(Icons.coffee_outlined, size: 16),
                  label: Text('Caffeine: ${c.label}'),
                  selected: _caffeine == c,
                  onSelected: (_) => setState(() => _caffeine = _caffeine == c ? null : c),
                )),
          ],
        ),
      ],
    );
  }
}

/// Low / Medium / High choice mapped onto the numeric scales used by the API
/// (energy 1-10, stress 1-5).
enum _LevelChoice {
  low('Low', 4, 2),
  medium('Medium', 7, 3),
  high('High', 9, 5);

  const _LevelChoice(this.label, this.energy, this.stress);
  final String label;
  final int energy;
  final int stress;

  /// Maps a backend rating back to a choice. [scale] is 10 for energy,
  /// 5 for stress.
  static _LevelChoice? fromRating(int? value, {int scale = 10}) {
    if (value == null) return null;
    final lowCut = scale == 5 ? 2 : 4;
    final medCut = scale == 5 ? 3 : 7;
    if (value <= lowCut) return _LevelChoice.low;
    if (value <= medCut) return _LevelChoice.medium;
    return _LevelChoice.high;
  }
}

class _MoodButton extends StatelessWidget {
  const _MoodButton({required this.icon, required this.label, required this.selected, required this.onTap});

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 10),
        decoration: BoxDecoration(
          color: selected ? scheme.primaryContainer : scheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? scheme.primary : scheme.outlineVariant,
            width: selected ? 1.6 : 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 24, color: selected ? scheme.primary : scheme.onSurfaceVariant),
            const SizedBox(height: 6),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                color: selected ? scheme.primary : scheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LevelButton extends StatelessWidget {
  const _LevelButton({required this.label, required this.selected, required this.onTap});

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected ? scheme.primaryContainer : scheme.surfaceContainerLow,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? scheme.primary : scheme.outlineVariant,
            width: selected ? 1.6 : 1,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
              color: selected ? scheme.primary : scheme.onSurface,
            ),
          ),
        ),
      ),
    );
  }
}

class _Confirmation extends StatelessWidget {
  const _Confirmation({required this.onDone});

  final VoidCallback onDone;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(22),
                decoration: BoxDecoration(
                  color: scheme.secondaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.check_circle_rounded, size: 56, color: scheme.primary),
              ),
              const SizedBox(height: 22),
              Text(
                AppStrings.checkInSaved,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 10),
              Text(
                AppStrings.checkinConfirmBody,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 15, height: 1.5, color: scheme.onSurfaceVariant),
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                child: PrimaryButton(
                  label: 'Back to dashboard',
                  icon: Icons.arrow_back_rounded,
                  onPressed: onDone,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DigitsOnlyFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final digits = newValue.text.replaceAll(RegExp(r'[^0-9]'), '');
    if (digits.length > 6) return oldValue;
    return newValue.copyWith(
      text: digits,
      selection: TextSelection.collapsed(offset: digits.length),
    );
  }
}