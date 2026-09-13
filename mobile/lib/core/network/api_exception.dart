/// Typed exceptions thrown by the network layer.
///
/// The FastAPI backend returns a stable error envelope:
///
/// ```json
/// {"error": {"code": "...", "message": "..."}}
/// ```
///
/// We map transport-level failures (no network, server down, HTTP status)
/// into friendly, actionable exceptions. Backend stack traces are never
/// surfaced to the user.
library;

class ApiException implements Exception {
  final String message;
  final String? code;
  final int? statusCode;
  final Map<String, dynamic>? details;

  const ApiException({required this.message, this.code, this.statusCode, this.details});

  @override
  String toString() => 'ApiException($code, $statusCode): $message';
}

/// No connectivity or the request could not reach the server at all.
class NetworkException extends ApiException {
  NetworkException(String message) : super(message: message);
}

/// The server responded but indicated the session is invalid.
class UnauthorizedException extends ApiException {
  UnauthorizedException(String message) : super(message: message);
}

/// The server responded with a 4xx validation/conflict.
class RequestFailedException extends ApiException {
  RequestFailedException(String message, {super.code, super.statusCode, super.details})
      : super(message: message);
}

/// The backend is up but returned 5xx.
class ServerException extends ApiException {
  ServerException(String message) : super(message: message);
}