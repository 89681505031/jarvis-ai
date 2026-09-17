package com.jarvis.phone

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.Settings
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var router: PhoneCommandRouter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        router = PhoneCommandRouter(this)
        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            webViewClient = WebViewClient()
            addJavascriptInterface(AndroidBridge(), "AndroidJarvis")
            loadUrl("file:///android_asset/index.html")
        }
        setContentView(webView)
        requestRuntimePermissions()
    }

    private fun requestRuntimePermissions() {
        val permissions = mutableListOf(
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.READ_CALL_LOG,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.RECORD_AUDIO
        )
        if (android.os.Build.VERSION.SDK_INT >= 33) permissions += Manifest.permission.POST_NOTIFICATIONS
        val missing = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isNotEmpty()) ActivityCompat.requestPermissions(this, missing.toTypedArray(), 100)
    }

    fun openAccessibilitySettings() {
        startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
    }

    fun openNotificationSettings() {
        startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
    }

    private fun notificationReply(): String {
        val messages = JarvisNotificationService.latest(10)
        if (messages.isEmpty()) {
            return "Пока нет новых сообщений в уведомлениях WhatsApp или Telegram. Проверьте, что доступ к уведомлениям J.A.R.V.I.S. включён."
        }
        return buildString {
            append("Последние сообщения:\n")
            messages.forEach { message ->
                val appName = when (message.packageName) {
                    JarvisNotificationService.WHATSAPP -> "WhatsApp"
                    JarvisNotificationService.TELEGRAM -> "Telegram"
                    else -> message.packageName
                }
                append("• ").append(appName)
                if (message.title.isNotBlank()) append(" — ").append(message.title)
                if (message.text.isNotBlank()) append(": ").append(message.text)
                append('\n')
            }
        }.trim()
    }

    inner class AndroidBridge {
        @JavascriptInterface
        fun command(text: String): String {
            val normalized = text.trim().lowercase()
            if (
                normalized.contains("кто мне написал") ||
                normalized.contains("прочитай сообщения") ||
                normalized.contains("прочитай сообщение") ||
                normalized.contains("новые сообщения")
            ) {
                return notificationReply()
            }
            return router.execute(text)
        }

        @JavascriptInterface
        fun listApps(): String {
            val array = JSONArray()
            router.launcherApps().forEach {
                array.put(JSONObject().apply {
                    put("label", it.label)
                    put("packageName", it.packageName)
                    put("allowed", router.isAppAllowed(it.packageName))
                })
            }
            return array.toString()
        }

        @JavascriptInterface
        fun setAppAllowed(packageName: String, allowed: Boolean): String {
            router.setAppAllowed(packageName, allowed)
            return if (allowed) "Приложение добавлено в JARVIS." else "Приложение удалено из JARVIS."
        }

        @JavascriptInterface
        fun enableAccessibility(): String {
            openAccessibilitySettings()
            return "Откройте J.A.R.V.I.S. в специальных возможностях Android и включите доступ."
        }

        @JavascriptInterface
        fun enableNotifications(): String {
            openNotificationSettings()
            return "Откройте доступ к уведомлениям для J.A.R.V.I.S. и вернитесь в приложение."
        }

        @JavascriptInterface
        fun clearMessages(): String {
            JarvisNotificationService.clear()
            return "История уведомлений J.A.R.V.I.S. очищена."
        }

        @JavascriptInterface
        fun toast(text: String) {
            runOnUiThread {
                Toast.makeText(this@MainActivity, text, Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onDestroy() {
        webView.removeJavascriptInterface("AndroidJarvis")
        webView.destroy()
        super.onDestroy()
    }
}
