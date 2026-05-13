[app]

# App metadata
title = Fake GPS
package.name = fakegps
package.domain = com.fakegps
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,java
source.include_patterns = kivy_garden/**,icons/**

version = 1.0.0

# Entry point
entrypoint = main.py

# Requirements
# kivy-garden.mapview removed — bundled directly in source instead
requirements = python3,kivy==2.3.0,pyjnius,android,requests

# Orientation
orientation = portrait

# Fullscreen (0 = show status bar)
fullscreen = 0

# Android permissions
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_MOCK_LOCATION,FOREGROUND_SERVICE,FOREGROUND_SERVICE_LOCATION

# Include the Java source for MockLocationService
android.add_src = android/

# Android API targets
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Architecture (arm64-v8a covers most modern devices; add armeabi-v7a for older)
android.archs = arm64-v8a, armeabi-v7a

# Gradle dependencies (none extra needed — LocationManager is in android.jar)
# android.gradle_dependencies =

# Allow backup
android.allow_backup = True

# App icon (place a 512x512 PNG at this path to customise)
# icon.filename = %(source.dir)s/assets/icon.png

# Presplash
# presplash.filename = %(source.dir)s/assets/presplash.png

# Android manifest extras — declare the Foreground Service
android.manifest.service = com.fakegps.MockLocationService:android:foregroundServiceType=location

[buildozer]

# Log level: 0=error, 1=info, 2=debug
log_level = 2

# Warn on root build
warn_on_root = 1
