/// Validator tests.
library;

import 'package:flutter_test/flutter_test.dart';
import 'package:aarogyadrishti/core/utils/validators.dart';

void main() {
  group('Validators.email', () {
    test('rejects empty', () {
      expect(Validators.email(''), isNotNull);
      expect(Validators.email(null), isNotNull);
    });
    test('rejects malformed', () {
      expect(Validators.email('a@b'), isNotNull);
      expect(Validators.email('nope'), isNotNull);
    });
    test('accepts valid', () {
      expect(Validators.email(' a@b.com '), isNull);
    });
  });

  group('Validators.password', () {
    test('rejects short / empty', () {
      expect(Validators.password(''), isNotNull);
      expect(Validators.password('abc123'), isNotNull);
    });
    test('accepts >= 8 chars', () {
      expect(Validators.password('abcdefg1'), isNull);
      expect(Validators.password('abcdef1!'), isNull);
    });
  });

  group('Validators.rating', () {
    test('bounds', () {
      expect(Validators.rating(null, 1, 10), isNotNull);
      expect(Validators.rating(0, 1, 10), isNotNull);
      expect(Validators.rating(11, 1, 10), isNotNull);
      expect(Validators.rating(7, 1, 10), isNull);
    });
  });
}