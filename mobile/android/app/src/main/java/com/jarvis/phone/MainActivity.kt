package com.jarvis.phone

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import java.util.concurrent.Executors

class MainActivity : Activity() {
    companion object {
        private const val GITHUB_RELEASES = "https://api.github.com/repos/89681505031/jarvis-ai/releases?per_page=20"
        private const val APK_ASSET_NAME = "jarvis-phone.apk"
    }

    private lateinit var webView: WebView
    private lateinit var router: PhoneCommandRouter
    private lateinit var gigaChat: GigaChatClient
    private var speechRecognizer: SpeechRecognizer? = null
    private var tts: TextToSpeech? = null
    private var selectedPersona = "J.A.R.V.I.S."
    private lateinit var fishAudioTts: FishAudioTts
    private lateinit var memory: JarvisMemory
    private var wakeListening = false
    private var manualListening = false
    private val prefs by lazy { getSharedPreferences("jarvis_settings", MODE_PRIVATE) }
    private val backgroundExecutor = Executors.newFixedThreadPool(3)
    private val mainHandler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        router = PhoneCommandRouter(this)
        gigaChat = GigaChatClient(this)
        selectedPersona = prefs.getString("persona", "J.A.R.V.I.S.") ?: "J.A.R.V.I.S."
        fishAudioTts = FishAudioTts(this)
        memory = JarvisMemory(this)
        tts = TextToSpeech(this) { status ->
            if (status == TextToSpeech.SUCCESS) tts?.language = Locale("ru", "RU")
        }
        setupSpeechRecognizer()

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            webViewClient = WebViewClient()
            addJavascriptInterface(AndroidBridge(), "AndroidJarvis")
            loadUrl("file:///android_asset/index.html")
        }
        setContentView(webView)
        requestRuntimePermissions()
        mainHandler.postDelayed({ checkForUpdates(false) }, 1800)
    }

    private fun setupSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) = Unit
            override fun onBeginningOfSpeech() = Unit
            override fun onRmsChanged(rmsdB: Float) = Unit
            override fun onBufferReceived(buffer: ByteArray?) = Unit
            override fun onEndOfSpeech() = Unit
            override fun onPartialResults(partialResults: Bundle?) = Unit
            override fun onEvent(eventType: Int, params: Bundle?) = Unit
            override fun onError(error: Int) {
                val wasManual = manualListening
                manualListening = false
                restartWakeListening()
                if (wasManual) {
                    runOnUiThread {
                        if (::webView.isInitialized) webView.evaluateJavascript("window.onJarvisSpeechResult && window.onJarvisSpeechResult('')", null)
                    }
                }
            }
            override fun onResults(results: Bundle?) {
                val text = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull() ?: return
                manualListening = false
                val escaped = JSONObject.quote(text)
                restartWakeListening()
                runOnUiThread {
                    if (::webView.isInitialized) webView.evaluateJavascript("window.onJarvisSpeechResult && window.onJarvisSpeechResult($escaped)", null)
                }
            }
        })
    }

    private fun startListening() {
        wakeListening = false
        // Отмена фонового распознавания может вызвать onError. Это не ошибка ручного ввода.
        manualListening = false
        speechRecognizer?.cancel()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestRuntimePermissions()
            return
        }
        if (speechRecognizer == null) {
            Toast.makeText(this, "Голосовой ввод недоступен на этом устройстве.", Toast.LENGTH_SHORT).show()
            return
        }
        manualListening = true
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ru-RU")
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ru-RU")
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
        }
        speechRecognizer?.startListening(intent)
    }

    private fun speak(text: String) {
        if (text.isBlank()) return
        val apiKey = prefs.getString("fish_api_key", "").orEmpty()
        val fishVoice = FishAudioTts.voiceIdFor(selectedPersona)
        if (apiKey.isNotBlank() && !fishVoice.isNullOrBlank()) {
            fishAudioTts.speak(text, selectedPersona) { _ ->
                runOnUiThread {
                    tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "jarvis-response-fallback")
                    Toast.makeText(this, "Fish Audio недоступен — использую системный голос.", Toast.LENGTH_SHORT).show()
                }
            }
        } else {
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "jarvis-response")
        }
    }

    private fun requestRuntimePermissions() {
        val permissions = mutableListOf(
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.READ_CALL_LOG,
            Manifest.permission.CALL_PHONE,
            Manifest.permission.RECORD_AUDIO
        )
        if (android.os.Build.VERSION.SDK_INT >= 33) permissions += Manifest.permission.POST_NOTIFICATIONS
        val missing = permissions.filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
        if (missing.isNotEmpty()) ActivityCompat.requestPermissions(this, missing.toTypedArray(), 100)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 100 && grantResults.any { it == PackageManager.PERMISSION_GRANTED }) {
            mainHandler.postDelayed({ startWakeListening() }, 500)
        }
    }

    fun openAccessibilitySettings() { startActivity(Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
    fun openNotificationSettings() { startActivity(Intent(android.provider.Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }

    private fun notificationReply(): String {
        val messages = JarvisNotificationService.latest(10)
        if (messages.isEmpty()) return "Пока нет новых сообщений в уведомлениях WhatsApp или Telegram. Проверьте, что доступ к уведомлениям J.A.R.V.I.S. включён."
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

    private fun sendToGigaChat(text: String) {
        backgroundExecutor.execute {
            val answer = gigaChat.ask(text, selectedPersona, memory.memoryContext())
            memory.rememberTurn(text, answer)
            runOnUiThread {
                if (::webView.isInitialized) {
                    val escaped = JSONObject.quote(answer)
                    webView.evaluateJavascript("window.onGigaChatResult && window.onGigaChatResult($escaped)", null)
                }
                speak(answer)
            }
        }
    }

    private fun rememberUserName(text: String) {
        val s = text.trim()
        val lower = s.lowercase(Locale("ru", "RU"))
        val marker = when { lower.startsWith("меня зовут ") -> "меня зовут "; lower.startsWith("моё имя ") -> "моё имя "; lower.startsWith("мое имя ") -> "мое имя "; else -> "" }
        if (marker.isNotEmpty()) memory.setUserName(s.substring(marker.length).trim().split(" ").firstOrNull().orEmpty())
    }

    private fun startWakeListening() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) return
        if (speechRecognizer == null || wakeListening) return
        wakeListening = true
        try {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ru-RU")
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            }
            speechRecognizer?.startListening(intent)
        } catch (_: Exception) { wakeListening = false }
    }

    private fun restartWakeListening() {
        wakeListening = false
        mainHandler.postDelayed({ startWakeListening() }, 350)
    }

    override fun onResume() {
        super.onResume()
        startWakeListening()
    }

    override fun onPause() {
        wakeListening = false
        speechRecognizer?.cancel()
        super.onPause()
    }

    private fun checkForUpdates(manual: Boolean) {
        backgroundExecutor.execute {
            try {
                val connection = (URL(GITHUB_RELEASES).openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    connectTimeout = 10000
                    readTimeout = 15000
                    setRequestProperty("Accept", "application/vnd.github+json")
                    setRequestProperty("User-Agent", "JARVIS-Android")
                }
                val code = connection.responseCode
                val body = connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
                connection.disconnect()
                if (code !in 200..299) throw IllegalStateException("HTTP $code")

                val releases = org.json.JSONArray(body)
                var newestCode = BuildConfig.VERSION_CODE
                var newestRelease: JSONObject? = null
                var newestDownloadUrl = ""

                for (i in 0 until releases.length()) {
                    val candidate = releases.optJSONObject(i) ?: continue
                    if (candidate.optBoolean("draft") || candidate.optBoolean("prerelease")) continue
                    val assets = candidate.optJSONArray("assets") ?: continue
                    val asset = (0 until assets.length()).map { assets.optJSONObject(it) }.firstOrNull {
                        it?.optString("name") == APK_ASSET_NAME
                    } ?: continue
                    val tag = candidate.optString("tag_name")
                    val code = tag.substringAfterLast(".").toIntOrNull() ?: continue
                    if (code > newestCode) {
                        newestCode = code
                        newestRelease = candidate
                        newestDownloadUrl = asset.optString("browser_download_url")
                    }
                }

                if (newestRelease != null && newestDownloadUrl.isNotBlank()) {
                    val release = newestRelease!!
                    mainHandler.post {
                        showUpdateDialog(
                            release.optString("name", "Новая версия J.A.R.V.I.S."),
                            newestDownloadUrl
                        )
                    }
                } else if (manual) {
                    mainHandler.post {
                        Toast.makeText(this, "У вас установлена последняя версия J.A.R.V.I.S.", Toast.LENGTH_SHORT).show()
                    }
                }
            } catch (_: Exception) {
                if (manual) mainHandler.post {
                    Toast.makeText(this, "Не удалось проверить обновления.", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun showUpdateDialog(title: String, downloadUrl: String) {
        AlertDialog.Builder(this)
            .setTitle("Доступно обновление")
            .setMessage("$title\n\nТекущая версия: ${BuildConfig.VERSION_NAME}\nНовая версия доступна на GitHub.")
            .setNegativeButton("Позже", null)
            .setPositiveButton("Обновить") { _, _ -> downloadAndInstall(downloadUrl) }
            .show()
    }

    private fun downloadAndInstall(downloadUrl: String) {
        Toast.makeText(this, "Скачиваю обновление…", Toast.LENGTH_LONG).show()
        backgroundExecutor.execute {
            val file = File(cacheDir, APK_ASSET_NAME)
            try {
                val connection = (URL(downloadUrl).openConnection() as HttpURLConnection).apply {
                    connectTimeout = 15000
                    readTimeout = 120000
                    instanceFollowRedirects = true
                    setRequestProperty("User-Agent", "JARVIS-Android")
                }
                connection.inputStream.use { input -> file.outputStream().use { output -> input.copyTo(output) } }
                connection.disconnect()

                val uri = FileProvider.getUriForFile(this, "${BuildConfig.APPLICATION_ID}.fileprovider", file)
                mainHandler.post {
                    val intent = Intent(Intent.ACTION_VIEW).apply {
                        setDataAndType(uri, "application/vnd.android.package-archive")
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    }
                    try {
                        startActivity(intent)
                    } catch (_: Exception) {
                        Toast.makeText(this, "Не удалось открыть установщик APK.", Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                mainHandler.post {
                    Toast.makeText(this, "Ошибка загрузки обновления: ${e.message ?: "неизвестная ошибка"}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    inner class AndroidBridge {
        @JavascriptInterface fun command(text: String): String {
            rememberUserName(text)
            memory.recordHabit(text)
            val normalized = text.trim().lowercase()
            if (
                normalized.contains("кто мне написал") ||
                normalized.contains("прочитай сообщения") ||
                normalized.contains("прочитай сообщение") ||
                normalized.contains("новые сообщения")
            ) return notificationReply()
            if (router.canHandle(text)) {
                val result = router.execute(text)
                memory.rememberTurn(text, result)
                return result
            }
            sendToGigaChat(text)
            return ""
        }

        @JavascriptInterface fun startListening() { runOnUiThread { this@MainActivity.startListening() } }
        @JavascriptInterface fun speak(text: String) { runOnUiThread { this@MainActivity.speak(text) } }
        @JavascriptInterface fun setPersona(name: String) { selectedPersona = name; prefs.edit().putString("persona", name).apply() }

        @JavascriptInterface fun getUserName(): String = memory.getUserName()
        @JavascriptInterface fun getMemorySummary(): String = memory.memoryContext()

        @JavascriptInterface
        fun setApiKeys(fish: String, giga: String): String {
            val editor = prefs.edit()
            if (fish.isNotBlank()) editor.putString("fish_api_key", fish)
            if (giga.isNotBlank()) editor.putString("gigachat_api_key", giga)
            editor.apply()
            return "Fish Audio: ${if (fish.isNotBlank() || prefs.getString("fish_api_key", "").orEmpty().isNotBlank()) "✓ настроен" else "не настроен"} · GigaChat: ${if (giga.isNotBlank() || prefs.getString("gigachat_api_key", "").orEmpty().isNotBlank()) "✓ настроен" else "не настроен"}"
        }

        @JavascriptInterface
        fun getApiKeyStatus(): String = JSONObject().apply {
            put("fish", prefs.getString("fish_api_key", "").orEmpty().isNotBlank())
            put("giga", prefs.getString("gigachat_api_key", "").orEmpty().isNotBlank())
        }.toString()

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

        @JavascriptInterface fun setAppAllowed(packageName: String, allowed: Boolean): String {
            router.setAppAllowed(packageName, allowed)
            return if (allowed) "Приложение добавлено в JARVIS." else "Приложение удалено из JARVIS."
        }

        @JavascriptInterface fun enableAccessibility(): String {
            openAccessibilitySettings()
            return "Откройте J.A.R.V.I.S. в специальных возможностях Android и включите доступ."
        }

        @JavascriptInterface fun enableNotifications(): String {
            openNotificationSettings()
            return "Откройте доступ к уведомлениям для J.A.R.V.I.S. и вернитесь в приложение."
        }

        @JavascriptInterface fun clearMessages(): String {
            JarvisNotificationService.clear()
            return "История уведомлений J.A.R.V.I.S. очищена."
        }

        @JavascriptInterface fun checkUpdates() { checkForUpdates(true) }
        @JavascriptInterface fun toast(text: String) { runOnUiThread { Toast.makeText(this@MainActivity, text, Toast.LENGTH_SHORT).show() } }
    }

    override fun onDestroy() {
        backgroundExecutor.shutdownNow()
        speechRecognizer?.destroy()
        tts?.stop()
        tts?.shutdown()
        fishAudioTts.release()
        if (::webView.isInitialized) {
            webView.removeJavascriptInterface("AndroidJarvis")
            webView.destroy()
        }
        super.onDestroy()
    }
}
