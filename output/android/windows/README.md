# Grove & Stone: Android on Windows

An **emulator** is a virtual Android phone displayed in a window on your computer. The APK runs inside it. Expo Orbit is optional; this setup launches the emulator directly.

## On the computer already configured

Double-click **Grove & Stone Android** on the desktop. Wait for the phone to start; Grove & Stone opens automatically. Use the mouse to tap and drag, and the keyboard to enter text. Close the emulator window when finished to free memory.

Setup checked on **19 September 2026**:

| Item | Configuration |
| --- | --- |
| SDK | `%USERPROFILE%\Android\Sdk` |
| Virtual phone | `Grove_Stone_API_30`, Android 11 / API 30, x86_64 |
| Device data | `%USERPROFILE%\.android\avd` |
| Memory and processor | 1,536 MB RAM; two CPU cores |
| Display | 720 × 1280, density 320 |
| Acceleration | Windows Hypervisor Platform, verified usable |
| ADB device | `emulator-5556` |

The computer has approximately 8 GB RAM. Close unused applications if it feels slow. Internet is required for the shared live catalog and customer account.

## What the launcher does

[Open-Grove-and-Stone.cmd](Open-Grove-and-Stone.cmd) checks acceleration, starts the virtual phone if needed, waits for Android, installs the APK when the app is missing, and launches `com.groveandstone.app`. It uses Android Debug Bridge (**ADB**) to communicate with the virtual phone. It does not install the SDK or create a virtual phone on a new computer.

The repository copy expects `Grove-and-Stone-Android-1.0.0.apk` **in this folder**, or accepts its full path as an argument:

```bat
Open-Grove-and-Stone.cmd "C:\path\to\Grove-and-Stone-Android-1.0.0.apk"
```

The existing desktop shortcut uses the local launcher beside the project output files; keep its folder and the saved APK in place. No PowerShell execution-policy change is needed.

## On another Windows computer

1. Follow Google's [Android emulator setup](https://developer.android.com/studio/run/emulator) and [Windows acceleration instructions](https://developer.android.com/studio/run/emulator-acceleration). Install the SDK emulator, platform-tools and an Android system image. Android Studio's Device Manager can create and start a phone for you.
2. Download the signed APK using [the phone/build guide](../README.md).
3. Start your virtual phone and drag the APK onto its window to install it, or use `adb install` with that emulator selected. Open Grove & Stone from its app list.
4. To use the supplied command-file launcher, its SDK path and virtual-device name must match your setup. The values at the top of the file and the `-avd` argument describe this computer's configuration.

## What was checked

APK installation, welcome screen and Skip action, home page, Cart navigation, and repeat launch passed in the emulator. The app remained running with no recorded crash during that check. Physical-phone testing, full sign-in/checkout testing and Google Play publication are separate release steps. Live payments remain deferred; see [the owner guide](../../../OWNER_GUIDE.md).
