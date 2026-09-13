/// Coach chat screen (Phase 6): message list + composer + quick actions.
///
/// Messages come from the backend which builds context from aggregates only.
/// The backend sanitises replies (strips doses/phone-ish runs) and always ends
/// with a "not a doctor" disclaimer.
library;

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../models/coach.dart';
import '../../repositories/coach_repository.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key, required this.conversationId});

  final int conversationId;

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final CoachRepository _repo = CoachRepository(AppServices.instance.api);
  final TextEditingController _composer = TextEditingController();

  List<CoachMessage> _messages = const [];
  bool _loading = true;
  bool _sending = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _composer.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _repo.messages(widget.conversationId);
      if (mounted) setState(() => _messages = data.messages);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = AppStrings.somethingWentWrong);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send([String? preset]) async {
    final text = (preset ?? _composer.text).trim();
    if (text.isEmpty || _sending) return;
    _composer.clear();
    setState(() => _sending = true);
    final optimistic = CoachMessage(
      id: -DateTime.now().millisecondsSinceEpoch,
      conversationId: widget.conversationId,
      role: 'user',
      content: text,
      provider: 'user',
      safetyApplied: false,
      createdAt: DateTime.now(),
    );
    setState(() => _messages = [..._messages, optimistic]);
    try {
      final reply = await _repo.send(widget.conversationId, text);
      if (!mounted) return;
      setState(() => _messages = [..._messages, reply.reply]);
    } on ApiException catch (e) {
      if (mounted) {
        setState(() => _messages = [..._messages, CoachMessage(
          id: -DateTime.now().millisecondsSinceEpoch,
          conversationId: widget.conversationId,
          role: 'assistant',
          content: e.message,
          provider: 'error',
          safetyApplied: false,
          createdAt: DateTime.now(),
        )]);
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Coach chat')),
      body: Column(
        children: [
          Expanded(
            child: _loading
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
                    : _messages.isEmpty
                        ? _EmptyChat(onAskNext: () => _send('What should I do next?'), onWeekly: () => _send('Give me a weekly summary'))
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            reverse: true,
                            itemCount: _messages.length,
                            itemBuilder: (context, index) {
                              final msg = _messages[_messages.length - 1 - index];
                              return _MessageBubble(message: msg);
                            },
                          ),
          ),
          if (!_loading && _messages.isEmpty) ...[
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Wrap(
                spacing: 8,
                children: [
                  ActionChip(
                    avatar: const Icon(Icons.track_changes, size: 16),
                    label: const Text('What should I do next?'),
                    onPressed: _sending ? null : () => _send('What should I do next?'),
                  ),
                  ActionChip(
                    avatar: const Icon(Icons.calendar_view_week_outlined, size: 16),
                    label: const Text('Weekly summary'),
                    onPressed: _sending ? null : () => _send('Give me a weekly summary'),
                  ),
                ],
              ),
            ),
          ],
          const Divider(height: 1),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _composer,
                      minLines: 1,
                      maxLines: 4,
                      maxLength: 4000,
                      textInputAction: TextInputAction.newline,
                      decoration: InputDecoration(
                        hintText: 'Ask about your habits...',
                        counterText: '',
                        filled: true,
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      ),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _sending ? null : _send,
                    icon: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptyChat extends StatelessWidget {
  const _EmptyChat({required this.onAskNext, required this.onWeekly});

  final VoidCallback onAskNext;
  final VoidCallback onWeekly;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.psychology_alt_outlined, size: 52, color: scheme.primary),
            const SizedBox(height: 12),
            Text(
              'Ask me about your lifestyle patterns. I answer from the aggregates in your data - your raw check-ins are never sent to me.',
              textAlign: TextAlign.center,
              style: TextStyle(color: scheme.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final CoachMessage message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final isUser = message.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isUser ? scheme.primaryContainer : scheme.surfaceContainerLow,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
        ),
        child: Column(
          crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            SelectableText(
              message.content,
              style: TextStyle(
                fontSize: 14.5,
                height: 1.35,
                color: isUser ? scheme.onPrimaryContainer : scheme.onSurface,
              ),
            ),
            if (message.provider == 'openai_compatible' || message.safetyApplied || message.provider == 'deterministic') ...[
              const SizedBox(height: 6),
              Text(
                _providerMeta(),
                style: TextStyle(fontSize: 10, color: (isUser ? scheme.onPrimaryContainer : scheme.onSurfaceVariant).withValues(alpha: 0.7)),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _providerMeta() {
    if (message.provider == 'openai_compatible') return 'AI-assisted · sanitised';
    if (message.safetyApplied) return 'sanitised by safety guard';
    return 'personal coach (offline)';
  }
}