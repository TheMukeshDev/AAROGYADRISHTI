/// Forgot password screen.
///
/// Phase 1 has no SMTP; the backend issues a reset token in development. The
/// UI guides the user through requesting a reset link.
library;

import 'package:flutter/material.dart';

import '../../core/constants/app_strings.dart';
import '../../core/network/api_exception.dart';
import '../../core/utils/validators.dart';
import '../../widgets/primary_button.dart';
import '../../app.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _email = TextEditingController();
  bool _submitting = false;
  String? _status;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final emailError = Validators.email(_email.text);
    if (emailError != null) {
      setState(() => _status = emailError);
      return;
    }
    setState(() {
      _submitting = true;
      _status = null;
    });
    try {
      await AppServices.instance.authRepository.forgotPassword(_email.text.trim());
      if (!mounted) return;
      setState(() => _status = 'If this account exists, a reset link has been issued.');
      _email.clear();
    } catch (e) {
      String msg;
      if (e is NetworkException) {
        msg = AppStrings.noInternet;
      } else if (e is ApiException) {
        msg = e.message;
      } else {
        msg = AppStrings.somethingWentWrong;
      }
      if (mounted) setState(() => _status = msg);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.forgotPassword)),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              Text(
                'Enter your account email and we will issue a reset link.',
                style: TextStyle(fontSize: 16, color: scheme.onSurfaceVariant),
              ),
              const SizedBox(height: 28),
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: AppStrings.emailHint,
                  prefixIcon: Icon(Icons.mail_outline),
                ),
              ),
              if (_status != null) ...[
                const SizedBox(height: 16),
                Text(_status!, style: TextStyle(color: _isError(_status!) ? scheme.error : scheme.primary)),
              ],
              const SizedBox(height: 24),
              PrimaryButton(
                label: 'Send reset link',
                loading: _submitting,
                onPressed: _submit,
              ),
            ],
          ),
        ),
      ),
    );
  }

  bool _isError(String s) => s.startsWith('If this') == false;
}