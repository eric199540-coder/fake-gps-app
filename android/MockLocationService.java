package com.fakegps;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.location.Criteria;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.IBinder;
import android.os.SystemClock;
import android.util.Log;

/**
 * Foreground service that injects mock GPS coordinates into the Android
 * LocationManager.  Python calls the static helper methods via Pyjnius.
 *
 * Requirements: 1.3, 5.1, 5.2
 */
public class MockLocationService extends Service {

    private static final String TAG              = "MockLocationService";
    private static final String PROVIDER         = LocationManager.GPS_PROVIDER;
    private static final String CHANNEL_ID       = "fake_gps_channel";
    private static final int    NOTIFICATION_ID  = 1001;

    // Shared state written by Python, read by the service loop
    private static volatile double  sLat      = 0.0;
    private static volatile double  sLng      = 0.0;
    private static volatile float   sAccuracy = 5.0f;
    private static volatile boolean sRunning  = false;

    private LocationManager mLocationManager;
    private Thread          mUpdateThread;

    // -----------------------------------------------------------------------
    // Static API called from Python via Pyjnius
    // -----------------------------------------------------------------------

    /** Start the service and begin injecting the given coordinates. */
    public static void startMock(Context context, double lat, double lng) {
        sLat     = lat;
        sLng     = lng;
        sRunning = true;
        Intent intent = new Intent(context, MockLocationService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(intent);
        } else {
            context.startService(intent);
        }
        Log.d(TAG, "startMock: " + lat + ", " + lng);
    }

    /** Update the injected coordinates while the service is running. */
    public static void setLocation(double lat, double lng) {
        sLat = lat;
        sLng = lng;
    }

    /** Update coordinates with explicit accuracy. */
    public static void setLocation(double lat, double lng, float accuracy) {
        sLat      = lat;
        sLng      = lng;
        sAccuracy = accuracy;
    }

    /** Stop the service and remove the mock provider. */
    public static void stopMock(Context context) {
        sRunning = false;
        context.stopService(new Intent(context, MockLocationService.class));
        Log.d(TAG, "stopMock called");
    }

    // -----------------------------------------------------------------------
    // Service lifecycle
    // -----------------------------------------------------------------------

    @Override
    public void onCreate() {
        super.onCreate();
        mLocationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        registerMockProvider();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startForeground(NOTIFICATION_ID, buildNotification());
        startUpdateLoop();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        sRunning = false;
        if (mUpdateThread != null) {
            mUpdateThread.interrupt();
        }
        removeMockProvider();
        super.onDestroy();
        Log.d(TAG, "Service destroyed");
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;  // Not a bound service
    }

    // -----------------------------------------------------------------------
    // Mock provider management
    // -----------------------------------------------------------------------

    private void registerMockProvider() {
        try {
            mLocationManager.addTestProvider(
                PROVIDER,
                false,  // requiresNetwork
                false,  // requiresSatellite
                false,  // requiresCell
                false,  // hasMonetaryCost
                true,   // supportsAltitude
                true,   // supportsSpeed
                true,   // supportsBearing
                Criteria.POWER_LOW,
                Criteria.ACCURACY_FINE
            );
            mLocationManager.setTestProviderEnabled(PROVIDER, true);
            Log.d(TAG, "Mock provider registered");
        } catch (SecurityException e) {
            Log.e(TAG, "Permission denied for mock location: " + e.getMessage());
        } catch (IllegalArgumentException e) {
            // Provider already exists — update it
            Log.w(TAG, "Provider already exists: " + e.getMessage());
            mLocationManager.setTestProviderEnabled(PROVIDER, true);
        }
    }

    private void removeMockProvider() {
        try {
            mLocationManager.setTestProviderEnabled(PROVIDER, false);
            mLocationManager.removeTestProvider(PROVIDER);
            Log.d(TAG, "Mock provider removed");
        } catch (Exception e) {
            Log.w(TAG, "Could not remove mock provider: " + e.getMessage());
        }
    }

    private void pushLocation(double lat, double lng, float accuracy) {
        try {
            Location loc = new Location(PROVIDER);
            loc.setLatitude(lat);
            loc.setLongitude(lng);
            loc.setAccuracy(accuracy);
            loc.setAltitude(0.0);
            loc.setTime(System.currentTimeMillis());
            loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
                loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
            }
            mLocationManager.setTestProviderLocation(PROVIDER, loc);
        } catch (Exception e) {
            Log.e(TAG, "setTestProviderLocation failed: " + e.getMessage());
        }
    }

    // -----------------------------------------------------------------------
    // Update loop (500 ms interval)
    // -----------------------------------------------------------------------

    private void startUpdateLoop() {
        if (mUpdateThread != null && mUpdateThread.isAlive()) return;
        mUpdateThread = new Thread(() -> {
            while (sRunning && !Thread.currentThread().isInterrupted()) {
                pushLocation(sLat, sLng, sAccuracy);
                try {
                    Thread.sleep(500);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }, "MockLocationThread");
        mUpdateThread.setDaemon(true);
        mUpdateThread.start();
    }

    // -----------------------------------------------------------------------
    // Foreground notification
    // -----------------------------------------------------------------------

    private Notification buildNotification() {
        createNotificationChannel();

        // Tap notification to bring app to foreground
        Intent launchIntent = getPackageManager()
            .getLaunchIntentForPackage(getPackageName());
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder builder;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            builder = new Notification.Builder(this, CHANNEL_ID);
        } else {
            builder = new Notification.Builder(this);
        }

        return builder
            .setContentTitle("Fake GPS 運行中")
            .setContentText("模擬定位已啟動，點擊返回應用程式")
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Fake GPS Service",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("模擬 GPS 定位服務通知");
            NotificationManager nm =
                (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm != null) {
                nm.createNotificationChannel(channel);
            }
        }
    }
}
