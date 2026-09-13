/// Forgot password screen - email request with clear success/error states.
library;

import 'package:flutter/material.dart';

import '../../app.dart';
import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../core/utils/validators.dart';
import '../../widgets/auth_scaffold.dart';
import '../../widgets/error_message.dart';
import '../../widgets/primary_button.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  bool _submitting = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await AppServices.instance.authRepository.forgotPassword(_email.text.trim());
      if (!mounted) return;
      setState(() => _sent = true);
      _email.clear();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        if (e is NetworkException) {
          _error = AppStrings.noInternet;
        } else if (e is ApiException) {
          _error = e.message;
        } else {
          _error = AppStrings.somethingWentWrong;
        }
      });
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return AuthScaffold(
      title: 'Reset password',
      subtitle: 'Enter your account email and we will issue a reset link.',
      children: _sent
          ? [
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: scheme.secondaryContainer,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: Column(
                  children: [
                    Icon(Icons.mark_email_read_outlined, size: 40, color: scheme.primary),
                    const SizedBox(height: 12),
                    Text(
                      'Check your inbox',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: scheme.onSecondaryContainer),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'If an account exists for this email, we have issued a reset link. It expires after a short time.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: scheme.onSecondaryContainer, height: 1.5),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              PrimaryButton(
                label: 'Done',
                onPressed: () => Navigator.of(context).maybePop(),
              ),
            ]
          : [
              Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (_error != null) ...[
                      DismissibleErrorBanner(
                        message: _error!,
                        onDismiss: () => setState(() => _error = null),
                      ),
                      const SizedBox(height: 16),
                    ],
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.done,
                      autocorrect: false,
                      onFieldSubmitted: (_) => _submitting ? null : _submit(),
                      autovalidateMode: AutovalidateMode.onUserInteraction,
                      validator: Validators.email,
                      decoration: const InputDecoration(
                        labelText: AppStrings.emailHint,
                        prefixIcon: Icon(Icons.mail_outline_rounded),
                      ),
                    ),
                    const SizedBox(height: 24),
                    PrimaryButton(
                      label: 'Send reset link',
                      loading: _submitting,
                      onPressed: _submit,
                    ),
                  ],
                ),
              ),
            ],
    );
  }
}