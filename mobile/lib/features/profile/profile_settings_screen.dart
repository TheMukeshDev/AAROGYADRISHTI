/// Profile / Settings screen.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/constants/app_strings.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/primary_button.dart';
import '../../app.dart';
import '../auth/welcome_screen.dart';

class ProfileSettingsScreen extends StatelessWidget {
  const ProfileSettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.profileTitle)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // User header
          CircleAvatar(
            radius: 36,
            backgroundColor: scheme.primaryContainer,
            child: Icon(Icons.person, size: 36, color: scheme.primary),
          ),
          const SizedBox(height: 12),
          Text(
            auth.user?.name ?? auth.user?.email ?? '',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            auth.user?.email ?? '',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 14, color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 24),

          _sectionTitle('Connected health sources', scheme),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.health_and_safety),
            title: const Text('Health Connect'),
            subtitle: const Text('Manage data source permissions'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Health source settings coming soon.')),
              );
            },
          ),
          const Divider(),

          _sectionTitle('Data & privacy', scheme),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.security),
            title: const Text('Permissions & consent'),
            subtitle: const Text('Review and revoke health data access'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {},
          ),
          const Divider(),

          _sectionTitle('Actions', scheme),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(Icons.delete_outline, color: scheme.error),
            title: Text(AppStrings.deleteAccount, style: TextStyle(color: scheme.error)),
            onTap: () => _confirmDelete(context),
          ),
          const SizedBox(height: 24),

          PrimaryButton(
            label: AppStrings.logout,
            onPressed: () async {
              await auth.logout();
              if (!context.mounted) return;
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const WelcomeScreen()),
                (_) => false,
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text, ColorScheme scheme) => Padding(
        padding: const EdgeInsets.only(bottom: 8, top: 12),
        child: Text(
          text,
          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: scheme.onSurfaceVariant),
        ),
      );

  void _confirmDelete(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete account?'),
        content: Text(
          'This action is not yet available in Phase 1. It will be implemented in a future update.',
          style: TextStyle(color: scheme.onSurfaceVariant),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Cancel')),
        ],
      ),
    );
  }
}