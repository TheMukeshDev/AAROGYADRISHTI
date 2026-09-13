# Publish the Flutter app

Vercel hosts the FastAPI backend only. It does not build or distribute the
Flutter Android application. Use Google Play for the normal public release or
GitHub Releases for a direct APK download.

## Option 1: Google Play (recommended)

1. Create a Google Play Console developer account and an application.
2. Create a release keystore and keep it outside Git:

   ```powershell
   keytool -genkeypair -v -keystore aarogya-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias aarogya
   ```

3. Create `mobile/android/key.properties` with the keystore values. This file
   is ignored by Git.
4. Add Firebase `google-services.json` to `mobile/android/app/` and register
   the release keystore SHA-1 and SHA-256 fingerprints in Firebase.
5. Build an Android App Bundle with the deployed API URL:

   ```powershell
   cd mobile
   flutter pub get
   flutter build appbundle --release --dart-define=API_BASE_URL=https://api.example.com
   ```

6. Upload `build/app/outputs/bundle/release/app-release.aab` to a Play Console
   internal test, closed test, or production release.

Google Play provides installation, updates, signing, device compatibility,
and a stable link that users can open from any device.

## Option 2: GitHub Releases (direct APK)

Use this for hackathon demos or users who need an APK without the Play Store:

```powershell
cd mobile
flutter build apk --release --dart-define=API_BASE_URL=https://api.example.com
```

Create a GitHub Release and upload:

```text
mobile/build/app/outputs/flutter-apk/app-release.apk
```

Users can download the APK from the release page. They may need to allow
installation from their browser or file manager, and they will not receive
automatic updates. Never distribute a release APK signed with the debug key.

## Optional Firebase App Distribution

Firebase App Distribution is useful for testers, not public users. Add tester
emails in Firebase Console and upload the signed APK from the release build.

## Release checklist

- The API uses a stable HTTPS custom domain.
- `API_BASE_URL` points to that domain without a trailing slash.
- The release APK/AAB is signed with the release keystore.
- The release keystore SHA fingerprints are registered in Firebase.
- `google-services.json` matches package `com.themukeshdev`.
- Production Vercel variables and database migrations are complete.