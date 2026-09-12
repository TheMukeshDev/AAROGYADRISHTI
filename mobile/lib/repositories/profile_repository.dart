/// Profile repository: GET/POST/PUT profile endpoints.
library;

import '../../core/constants/app_constants.dart';
import '../../core/network/api_client.dart';
import '../../models/profile.dart';

class ProfileRepository {
  ProfileRepository(this._api);
  final ApiClient _api;

  String get _prefix => '${AppConstants.apiV1Prefix}/profile';

  Future<UserProfile> get() async {
    final data = await _api.get(_prefix);
    return UserProfile.fromJson(data as Map<String, dynamic>);
  }

  Future<UserProfile> update({
    String? name,
    String? ageGroup,
    String? gender,
    double? heightCm,
    double? weightKg,
    String? activityLevelWire,
    String? primaryGoalWire,
    bool? onboardingCompleted,
  }) async {
    final body = <String, dynamic>{};
    if (name != null) body['name'] = name;
    if (ageGroup != null) body['age_group'] = ageGroup;
    if (gender != null) body['gender'] = gender;
    if (heightCm != null) body['height_cm'] = heightCm;
    if (weightKg != null) body['weight_kg'] = weightKg;
    if (activityLevelWire != null) body['activity_level'] = activityLevelWire;
    if (primaryGoalWire != null) body['primary_goal'] = primaryGoalWire;
    if (onboardingCompleted != null) body['onboarding_completed'] = onboardingCompleted;

    final data = await _api.put(_prefix, body: body);
    return UserProfile.fromJson(data as Map<String, dynamic>);
  }
}