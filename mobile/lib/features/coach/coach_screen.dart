/// AI preventive lifestyle coach - conversation list (Phase 6).
///
/// The coach answers only from aggregate lifestyle data; it never diagnoses
/// or prescribes. Replies are sanitised by the backend safety guard.
library;

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../core/utils/date_utils.dart';
import '../../models/coach.dart';
import '../../repositories/coach_repository.dart';
import 'chat_screen.dart';

class CoachScreen extends StatefulWidget {
  const CoachScreen({super.key, this.onNavigateTab});

  /// Switches the root tab (e.g. Experiments -> tab 3, Insights -> tab 1).
  final ValueChanged<int>? onNavigateTab;

  @override
  State<CoachScreen> createState() => _CoachScreenState();
}

class _CoachScreenState extends State<CoachScreen> {
  final CoachRepository _repo = CoachRepository(AppServices.instance.api);

  List<CoachConversation> _conversations = const [];
  bool _loading = true;
  bool _creating = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _repo.conversations();
      if (mounted) setState(() => _conversations = data.conversations);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _newChat() async {
    setState(() => _creating = true);
    try {
      final convo = await _repo.createConversation();
      if (!mounted) return;
      await _openChat(convo.id);
      await _load();
    } on ApiException catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
    } finally {
      if (mounted) setState(() => _creating = false);
    }
  }

  Future<void> _openChat(int conversationId) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ChatScreen(conversationId: conversationId)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Lifestyle Coach'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _creating ? null : _newChat,
        icon: _creating
            ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.chat_bubble_outline),
        label: const Text('New chat'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off, size: 40),
                      const SizedBox(height: 12),
                      Text(_error!),
                      const SizedBox(height: 12),
                      FilledButton(onPressed: _load, child: const Text('Retry')),
                    ],
                  ),
                )
              : _conversations.isEmpty
                  ? _EmptyCoach(
                      onTryExperiment: widget.onNavigateTab == null ? null : () => widget.onNavigateTab!(3),
                      onViewInsights: widget.onNavigateTab == null ? null : () => widget.onNavigateTab!(1),
                      onNewChat: _newChat,
                      creating: _creating,
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        itemCount: _conversations.length,
                        itemBuilder: (context, index) {
                          final c = _conversations[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 10),
                            child: ListTile(
                              leading: const Icon(Icons.chat_outlined),
                              title: Text(c.title),
                              subtitle: Text(AppDateUtils.shortDay(c.createdAt.toLocal())),
                              onTap: () => _openChat(c.id),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}

class _EmptyCoach extends StatelessWidget {
  const _EmptyCoach({
    required this.onTryExperiment,
    required this.onViewInsights,
    required this.onNewChat,
    required this.creating,
  });

  final VoidCallback? onTryExperiment;
  final VoidCallback? onViewInsights;
  final VoidCallback onNewChat;
  final bool creating;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: scheme.primaryContainer,
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.psychology_alt_outlined, size: 36, color: scheme.primary),
            ),
            const SizedBox(height: 16),
            Text(
              'Your coach is ready when you are',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              'Chat about your lifestyle patterns to see honest, data-backed observations.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, height: 1.45, color: scheme.onSurfaceVariant),
            ),
            const SizedBox(height: 20),
            if (onTryExperiment != null) ...[
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: onTryExperiment,
                  icon: const Icon(Icons.science_outlined),
                  label: Text(AppStrings.tryExperiment),
                ),
              ),
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: onViewInsights,
                  icon: const Icon(Icons.insights_outlined),
                  label: Text(AppStrings.viewInsights),
                ),
              ),
              const SizedBox(height: 20),
            ],
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: scheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: scheme.outlineVariant, width: 1),
              ),
              child: Row(
                children: [
                  Icon(Icons.shield_outlined, size: 18, color: scheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      AppStrings.coachSafetyNote,
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.45,
                        color: scheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Tap New chat to get started',
              style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant.withValues(alpha: 0.8)),
            ),
          ],
        ),
      ),
    );
  }
}