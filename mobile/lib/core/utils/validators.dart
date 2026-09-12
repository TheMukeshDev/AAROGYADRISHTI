/// Input validation helpers returning human-friendly error messages.
library;

class Validators {
  Validators._();

  static String? email(String? value) {
    final v = value?.trim() ?? '';
    if (v.isEmpty) return 'Please enter your email.';
    final ok = RegExp(r'^\S+@\S+\.\S+$').hasMatch(v);
    return ok ? null : 'Enter a valid email address.';
  }

  static String? password(String? value, {int minLength = 8}) {
    final v = value ?? '';
    if (v.isEmpty) return 'Please enter a password.';
    if (v.length < minLength) return 'Use at least $minLength characters.';
    if (v.isAlphaNumericOnly) return 'Mix letters, numbers or symbols.';
    return null;
  }

  static String? name(String? value) {
    final v = value?.trim() ?? '';
    if (v.isEmpty) return 'Please enter your name.';
    return null;
  }

  static String? required(String? value, String field) {
    final v = value?.trim() ?? '';
    return v.isEmpty ? 'Please select $field.' : null;
  }

  /// 1-10 style number picker.
  static String? rating(int? value, int min, int max) {
    if (value == null) return 'Please choose a value.';
    if (value < min || value > max) return 'Choose between $min and $max.';
    return null;
  }
}

extension _AlphaNumeric on String {
  bool get isAlphaNumericOnly => startsWith(RegExp(r'[a-zA-Z0-9]'));
}