/// Root scaffold with the 5-tab bottom navigation
/// (Home / Insights / Coach / Experiments / Profile).
library;

import 'package:flutter/material.dart';

import '../features/coach/coach_screen.dart';
import '../features/dashboard/home_screen.dart';
import '../features/experiments/experiments_screen.dart';
import '../features/insights/insights_screen.dart';
import '../features/profile/profile_settings_screen.dart';
import 'app_bottom_bar.dart';

class AppScaffold extends StatefulWidget {
  const AppScaffold({super.key});

  @override
  State<AppScaffold> createState() => _AppScaffoldState();
}

class _AppScaffoldState extends State<AppScaffold> {
  int _index = 0;

  late final List<Widget> _screens = [
    HomeScreen(onOpenProfile: () => setState(() => _index = 4)),
    const InsightsScreen(),
    CoachScreen(onNavigateTab: (i) => setState(() => _index = i)),
    const ExperimentsScreen(),
    const ProfileSettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: AppBottomBar(
        currentIndex: _index,
        onTap: (i) {
          setState(() => _index = i);
        },
      ),
    );
  }
}