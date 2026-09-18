package com.jarvis.phone

import android.app.Application
import android.content.Intent
import androidx.core.content.ContextCompat

class JarvisApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, Intent(this, JarvisWakeService::class.java))
        } else {
            startService(Intent(this, JarvisWakeService::class.java))
        }
    }
}
