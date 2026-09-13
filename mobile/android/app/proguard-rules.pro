# Add project specific ProGuard rules here.
# Required for release builds (isMinifyEnabled = true).
#
# Flutter engine classes are loaded reflectively and must not be renamed.
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

# Google Mobile Services / Firebase (safety net - the Firebase and Play
# Services artifacts ship their own consumer rules, these are a fallback).
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.auth.** { *; }
-dontwarn com.google.android.gms.**

# Health Connect API surface is invoked through reflection by the health plugin.
-keep class androidx.health.connect.client.** { *; }

# Play Core is only referenced by Flutter's optional deferred-components engine
# code, which this app does not use. Suppress R8's missing-class check for it.
-dontwarn com.google.android.play.core.**