# Grove & Stone Android app

**Version 1.0.0, build 1 — signed APK built successfully on 18 September 2026.**

[Open the Expo build and download/install the APK](https://expo.dev/accounts/saispandanatumu/projects/grove-and-stone/builds/422635f0-b38b-49c9-9df1-a0b043b4250f)

## Install on your Android phone

You need **Android 8.0 or newer**, internet access and space for the 86.9 MiB download plus the installed app.

1. Open the build link above in Chrome **on your Android phone**. Sign in to your Expo account if requested; this is separate from a shop customer account.
2. Select **Install** and download the **APK**. Do not choose **Open with Orbit**; that option is for computer/device tools.
3. Open the downloaded `.apk` from Chrome's Downloads or your phone's Files app.
4. If Android asks, open the installation settings and allow **Install unknown apps / Allow from this source** for the browser or Files app you used. Approve this yourself for this APK, then return and tap **Install**. Button names vary by phone. You can turn that source permission off again afterward.
5. Tap **Open**, or find **Grove & Stone** among your apps. Skip or complete the welcome screens. Browse as a guest, or use **Account → Create account / Log in** for your shop account.

**You do not need Orbit, Expo Go, Android Studio or a running computer.** This is a standalone signed app connecting to the deployed HTTPS API, with the same customer accounts as the website. It is not yet listed on Google Play.

### If the Expo download does not open

Copy the saved `Grove-and-Stone-Android-1.0.0.apk` from your computer's project `outputs` folder to your phone using a USB cable and Android's **File transfer** mode. Open it in the phone's Files app and follow steps 4–5. No Expo login is needed for the copied APK. This path also works if the hosted build expires.

### Using and updating the app

- Tap to select products and tabs; swipe to scroll and change hero slides. Use the Android Back button/gesture to return.
- A website deployment does not automatically replace an installed APK. Native app changes require a newly built APK (or a separately configured update system). Install future APKs signed with the same project key as an update; avoid uninstalling just to update because it clears local app data.
- If a download is incomplete or Android reports a parsing error, download it again and check the Android version. If it says **App not installed** or an update conflicts, keep the message and phone model/version for troubleshooting rather than deleting your existing installation.
- A slow first catalog request can occur when the free API host wakes up. The bundled fruit images do not require that API download. The store's delivery/ordering notice reflects its current owner configuration.

## Windows computer

Windows cannot directly run an APK. On the configured computer, double-click the desktop shortcut **Grove & Stone Android**. It opens the Android emulator and launches this APK. See [the Windows setup guide and launcher](windows/README.md).

## Build and verification

A local copy is saved beside the source ZIP as `Grove-and-Stone-Android-1.0.0.apk`. The binary is separate from Git and the source ZIP. EAS artifacts can expire; retain the local copy for installation and rebuild from `mobile/` for future releases.

Size: **91,093,565 bytes (86.9 MiB)**. SHA-256:

```text
294f88b158b0b7f481d412997492f218669ebef7cbeaf3444891028690afae4b
```

The cloud build succeeded and the downloaded archive passed integrity checks. On **19 September 2026**, the APK installed and launched in an Android 11 Windows emulator. The welcome screen/Skip, home page, Cart navigation and repeated launch were checked. **Physical-phone testing and Google Play publication have not been completed.** Live payments and other business launch requirements remain as described in [the owner guide](../../OWNER_GUIDE.md). Installing the app does not enable ordering while the owner has paused the store.

See [build metadata](build.json) and [Android architecture and performance](../../ANDROID_AND_PERFORMANCE.md).

Installation reference: [Expo's Android internal distribution guide](https://docs.expo.dev/build/internal-distribution/).
