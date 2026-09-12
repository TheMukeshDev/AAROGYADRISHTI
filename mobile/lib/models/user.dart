/// Authenticated user model (mirrors backend `UserResponse`).
library;

class User {
  final int id;
  final String email;
  final String? name;
  final bool emailVerified;
  final DateTime? createdAt;

  const User({
    required this.id,
    required this.email,
    this.name,
    this.emailVerified = false,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as int,
        email: json['email'] as String,
        name: json['name'] as String?,
        emailVerified: json['email_verified'] as bool? ?? false,
        createdAt: json['created_at'] != null ? DateTime.tryParse(json['created_at'] as String) : null,
      );
}

/// Auth session (access + refresh + user) returned by register/login/refresh.
class AuthSession {
  final String accessToken;
  final String refreshToken;
  final User user;

  const AuthSession({required this.accessToken, required this.refreshToken, required this.user});
}