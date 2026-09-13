/// Goals editing screen - reusable multi-select picker shared with onboarding.
///
/// Loads previously saved goals from StorageService and persists the updated
/// selection both locally (all goals) and on the backend (first goal as
/// primary).
library;

import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../models/app_enums.dart';
import '../../repositories/profile_repository.dart';
import '../../widgets/primary_button.dart';
import '../../widgets/selection_card.dart';
import '../../app.dart';
import '../../core/storage/storage_service.dart';
import '../onboarding/onboarding_controller.dart';

class GoalsEditScreen extends StatefulWidget {
  const GoalsEditScreen({super.key});

  @override
  State<GoalsEditScreen> createState() => _GoalsEditScreenState();
}

class _GoalsEditScreenState extends State<GoalsEditScreen> {
  late final Set<PrimaryGoal> _selected;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _selected = {};
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    try {
      final raw = await StorageService.instance.getString(AppConstantsKeys.selectedGoalsKey);
      if (raw != null && raw.isNotEmpty) {
        _selected.addAll(
          raw.split(',').map((w) => PrimaryGoal.fromWire(w)).whereType<PrimaryGoal>(),
        );
      }
    } catch (_) {
      // Fresh selection otherwise.
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggle(PrimaryGoal goal) {
    setState(() {
      if (_selected.contains(goal)) {
        _selected.remove(goal);
      } else {
        _selected.add(goal);
      }
    });
  }

  Future<void> _save() async {
    if (_saving) return;
    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      // Persist multi-select goals locally.
      final storage = StorageService.instance;
      final wires = _selected.map((g) => g.wire).toList();
      await storage.setString(
        AppConstantsKeys.selectedGoalsKey,
        wires.isEmpty ? '' : wires.join(','),
      );

      // Update backend primary goal (only the first is stored server-side).
      if (_selected.isNotEmpty) {
        final repo = ProfileRepository(AppServices.instance.api);
        await repo.update(primaryGoalWire: _selected.first.wire);
      }

      if (mounted) Navigator.of(context).pop(true);
    } on NetworkException {
      if (mounted) setState(() => _error = AppStrings.noInternet);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: Text(AppStrings.myGoals),
        automaticallyImplyLeading: !_saving,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Expanded(
                  child: SingleChildScrollView(
                    keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                    padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          AppStrings.goalTitle,
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, height: 1.2),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          AppStrings.goalSubtitle,
                          style: TextStyle(fontSize: 14.5, color: scheme.onSurfaceVariant, height: 1.45),
                        ),
                        const SizedBox(height: 16),
                        for (final goal in PrimaryGoal.values) ...[
                          SelectionCard(
                            icon: goal.icon,
                            label: goal.label,
                            selected: _selected.contains(goal),
                            onTap: () => _toggle(goal),
                          ),
                          const SizedBox(height: 10),
                        ],
                      ],
                    ),
                  ),
                ),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: scheme.errorContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        _error!,
                        style: TextStyle(color: scheme.onErrorContainer, fontSize: 13),
                      ),
                    ),
                  ),
                SafeArea(
                  top: false,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                    child: PrimaryButton(
                      label: 'Save goals',
                      icon: Icons.check_rounded,
                      loading: _saving,
                      onPressed: _selected.isNotEmpty ? _save : null,
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}