/// ProfileScreen widget test: selections persist to the controller (so the
/// flow's Continue button works) without any network call.
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:mobile/features/onboarding/onboarding_controller.dart';
import 'package:mobile/features/onboarding/profile_screen.dart';
import 'package:mobile/models/app_enums.dart';

Widget wrap(OnboardingController c) => MaterialApp(
      home: Scaffold(
        body: ChangeNotifierProvider<OnboardingController>.value(
          value: c,
          child: const ProfileScreen(),
        ),
      ),
    );

void main() {
  testWidgets('renders sections and persists age group + activity level', (tester) async {
    final ctrl = OnboardingController();
    await tester.pumpWidget(wrap(ctrl));

    expect(find.text('Tell us a little about yourself'), findsOneWidget);
    expect(find.text('Age group'), findsOneWidget);
    expect(find.text('Daily activity level'), findsOneWidget);

    // Choose an age group.
    await tester.tap(find.text('25 - 34'));
    await tester.pump();
    expect(ctrl.ageGroup, '25_34');

    // Choose activity level; controller must update so Continue enables.
    await tester.tap(find.text('Moderately active'));
    await tester.pump();
    expect(ctrl.activityLevel, ActivityLevel.moderatelyActive);
    expect(ctrl.profileValid, isFalse); // goal still missing

    // Choose a gender.
    await tester.ensureVisible(find.text('Female'));
    await tester.tap(find.text('Female'));
    await tester.pump();
    expect(ctrl.gender, 'female');
  });

  testWidgets('goal missing keeps profileValid false even with activity set', (tester) async {
    final ctrl = OnboardingController()..setGoal(PrimaryGoal.moreEnergy);
    await tester.pumpWidget(wrap(ctrl));
    await tester.tap(find.text('Mostly sedentary'));
    await tester.pump();
    expect(ctrl.profileValid, isTrue);
  });
}