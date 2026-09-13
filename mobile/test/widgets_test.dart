/// Reusable widget tests (CheckinOption, MetricCard).
library;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:aarogyadrishti/widgets/checkin_option.dart';
import 'package:aarogyadrishti/widgets/metric_card.dart';

void main() {
  testWidgets('CheckinOption shows label, subtitle and tap callback', (tester) async {
    var tapped = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: CheckinOption(
            label: 'Light',
            subtitle: '15 min',
            onTap: () => tapped++,
          ),
        ),
      ),
    );

    expect(find.text('Light'), findsOneWidget);
    expect(find.text('15 min'), findsOneWidget);

    await tester.tap(find.byType(CheckinOption));
    expect(tapped, 1);
  });

  testWidgets('CheckinOption shows check icon when selected', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: CheckinOption(label: 'Selected', selected: true),
        ),
      ),
    );
    expect(find.byIcon(Icons.check), findsOneWidget);
    expect(find.text('Selected'), findsOneWidget);
  });

  testWidgets('MetricCard renders em-dash when empty', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: MetricCard(title: 'Sleep', value: '\u2014', icon: Icons.nightlight_round, isEmpty: true),
        ),
      ),
    );
    expect(find.text('Sleep'), findsOneWidget);
    expect(find.text('\u2014'), findsOneWidget);
  });
}