/// Root auth/providers - the `AuthProvider` change notifier.
///
/// Responsibilities:
/// - hold the authenticated session,
/// - persist / restore tokens via StorageService,
/// - drive register / login / logout / demo access.
library;

import 'package:flutter/foundation.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase_auth;
import 'package:google_sign_in/google_sign_in.dart';

import '../core/network/api_exception.dart';
import '../core/storage/storage_service.dart';
import '../models/user.dart';
import '../repositories/auth_repository.dart';

enum AuthStatus { unknown, unauthenticated, authenticated }

class AuthProvider extends ChangeNotifier {
  AuthProvider(this._repository, {required StorageService storage}) : _storage = storage {
    restoreSession();
  }

  final AuthRepository _repository;
  final StorageService _storage;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  AuthStatus _status = AuthStatus.unknown;
  User? _user;
  String? _lastError;

  AuthStatus get status => _status;
  User? get user => _user;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  String? get lastError => _lastError;

  bool _restored = false;
  Future<void> restoreSession() async {
    if (_restored) return;
    _restored = true;
    final access = await _storage.accessToken;
    final refresh = await _storage.refreshToken;
    if (access != null && refresh != null) {
      _repository.restoreTokens(access: access, refresh: refresh);
      _status = AuthStatus.authenticated;
    } else {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<Null> _applySession(AuthSession session) async {
    _user = session.user;
    _status = AuthStatus.authenticated;
    await _storage.saveTokens(access: session.accessToken, refresh: session.refreshToken);
    notifyListeners();
    return null;
  }

  Future<Null> register(String name, String email, String password) async {
    _lastError = null;
    try {
      final session = await _repository.register(name, email, password);
      await _applySession(session);
    } catch (e) {
      _lastError = _friendly(e);
      rethrow;
    }
    return null;
  }

  Future<Null> login(String email, String password) async {
    _lastError = null;
    try {
      final session = await _repository.login(email, password);
      await _applySession(session);
    } catch (e) {
      _lastError = _friendly(e);
      rethrow;
    }
    return null;
  }

  Future<Null> loginWithGoogle() async {
    _lastError = null;
    try {
      final googleAccount = await _googleSignIn.signIn();
      if (googleAccount == null) return null;
      final googleAuthentication = await googleAccount.authentication;
      final credential = firebase_auth.GoogleAuthProvider.credential(
        accessToken: googleAuthentication.accessToken,
        idToken: googleAuthentication.idToken,
      );
      final credentialResult = await firebase_auth.FirebaseAuth.instance.signInWithCredential(credential);
      final firebaseUser = credentialResult.user;
      final firebaseIdToken = await firebaseUser?.getIdToken();
      if (firebaseIdToken == null || firebaseIdToken.isEmpty) {
        throw StateError('Firebase did not return an ID token.');
      }
      final session = await _repository.loginWithFirebase(firebaseIdToken);
      await _applySession(session);
    } catch (e) {
      _lastError = _friendly(e);
      rethrow;
    }
    return null;
  }

  Future<Null> loginWithDemo() async {
    _lastError = null;
    try {
      final session = await _repository.demoLogin();
      await _applySession(session);
    } catch (e) {
      _lastError = _friendly(e);
      rethrow;
    }
    return null;
  }

  Future<Null> logout() async {
    try {
      await _repository.logout();
    } catch (_) {
      // Server logout is best-effort; local logout always succeeds.
    }
    await _storage.clearTokens();
    await firebase_auth.FirebaseAuth.instance.signOut();
    await _googleSignIn.signOut();
    _repository.clearSession();
    _user = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
    return null;
  }

  String _friendly(Object e) {
    if (e is UnauthorizedException) return 'Incorrect email or password.';
    if (e is RequestFailedException) return e.message;
    if (e is NetworkException) return 'No internet connection. Please try again.';
    if (e is ServerException) return 'Our servers are busy. Please try again shortly.';
    if (e is ApiException) return e.message;
    return 'Something went wrong. Please try again.';
  }
}