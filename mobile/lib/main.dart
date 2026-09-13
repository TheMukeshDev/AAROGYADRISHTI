import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  await GoogleSignIn.instance.initialize(
    serverClientId: '601323736761-0vu3uk6gkgoq4j5ldicsuojb014fcapk.apps.googleusercontent.com',
  );
  runApp(const AarogyaDrishtiApp());
}