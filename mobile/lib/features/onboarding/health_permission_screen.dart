/// Health Connect permission screen (Phase 1: optional, can be declined).
library;

import 'package:flutter/material.dart';
import 'package:health/health.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../services/health_connect_service.dart';
import '../../widgets/checkin_option.dart';
import '../../widgets/primary_button.dart';
import 'onboarding_controller.dart';

class HealthPermissionScreen extends StatefulWidget {
  const HealthPermissionScreen({super.key});

  @override
  State<HealthPermissionScreen> createState() => _HealthPermissionScreenState();
}

class _HealthPermissionScreenState extends State<HealthPermissionScreen> {
  bool _loading = true;
  bool _supported = false;
  bool _requesting = false;
  String? _status;
  String? _error;

  final _service = HealthConnectService.instance;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final avail = await _service.setup();
    setState(() {
      _supported = avail == HealthConnectAvailability.supported;
      _loading = false;
    });
  }

  Future<void> _request() async {
    setState(() {
      _requesting = true;
      _error = null;
    });
    try {
      final types = [
        HealthDataType.STEPS,
        HealthDataType.SLEEP_ASLEEP,
        HealthDataType.MOVE_MINUTES,
      ];
      final granted = await _service.requestPermissions(types);
      if (!granted) {
        setState(() {
          _status = AppStrings.permissionDenied;
          _requesting = false;
        });
        return;
      }
      // Tell the server which categories were consented to.
      final healthRepo = context.read<OnboardingController>();
      healthRepo.setHealthSelection([
        const HealthDataTypeWrapper(
          type: HealthDataType.STEPS,
          title: 'Steps',
          description: 'Steps from your device',
          granted: true,
        ),
      ]);
      context.read<OnboardingController>().next();
    } catch (_) {
      setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _requesting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: scheme.primaryContainer,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(Icons.phone_android, size: 40, color: scheme.primary),
          ),
          const SizedBox(height: 22),
          const Text(
            AppStrings.healthPermissionTitle,
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 12),
          Text(
            AppStrings.healthPermissionBody,
            style: TextStyle(fontSize: 15, height: 1.45, color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 22),
          if (_supported) ...[
            const Text(
              'Data we can read automatically:',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            const CheckinOption(label: 'Steps', subtitle: 'Your daily step count', selected: true),
            const SizedBox(height: 8),
            const CheckinOption(label: 'Sleep', subtitle: 'Sleep duration and quality', selected: true),
            const SizedBox(height: 8),
            const CheckinOption(label: 'Activity', subtitle: 'Active and exercise minutes', selected: true),
            const SizedBox(height: 16),
            if (_error != null)
              Text(_error!, style: TextStyle(color: scheme.error, fontSize: 14)),
            PrimaryButton(
              label: 'Allow health data access',
              icon: Icons.health_and_safety,
              loading: _requesting,
              onPressed: _request,
            ),
          ] else ...[
            if (_service.availability == HealthConnectAvailability.notInstalled)
              Text(
                'Health Connect is not installed on this device. You can still '
                'track manually and add Health Connect later.',
                style: TextStyle(fontSize: 15, color: scheme.onSurfaceVariant),
              )
            else
              Text(
                AppStrings.healthConnectUnavailable,
                style: TextStyle(fontSize: 15, color: scheme.onSurfaceVariant),
              ),
          ],
          const SizedBox(height: 12),
          if (_status != null) ...[
            Text(_status!, style: TextStyle(color: scheme.primary, fontSize: 14)),
            const SizedBox(height: 8),
          ],
          TextButton(
            onPressed: () => context.read<OnboardingController>().next(),
            child: const Text(AppStrings.continueWithManual),
          ),
        ],
      ),
    );
  }
}