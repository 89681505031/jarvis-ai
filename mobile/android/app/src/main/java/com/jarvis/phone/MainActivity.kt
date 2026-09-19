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
import android.speech.tts.UtteranceProgressListener
import android.text.Html
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
    private var ttsReady = false
    private var selectedPersona = "J.A.R.V.I.S."
    private lateinit var fishAudioTts: FishAudioTts
    private lateinit var memory: JarvisMemory
    private var wakeListening = false
    private var manualListening = false
    private var conversationUntil = 0L
    private var isSpeaking = false
    private var resumeListeningAfterSpeech = false
    private var activityResumed = false
    private val conversationResumeDurationMs = 12_000L
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
            ttsReady = status == TextToSpeech.SUCCESS
            if (ttsReady) {
                tts?.language = Locale("ru", "RU")
                tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                    override fun onStart(utteranceId: String?) { isSpeaking = true }
                    override fun onDone(utteranceId: String?) { finishSpeech() }
                    override fun onError(utteranceId: String?) { finishSpeech() }
                })
            }
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
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            speechRecognizer = null
            return
        }
        speechRecognizer?.destroy()
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
                if (isSpeaking) return

                val wasManual = manualListening
                val wasConversation = conversationUntil > System.currentTimeMillis()
                manualListening = false
                wakeListening = false

                if (error == SpeechRecognizer.ERROR_AUDIO ||
                    error == SpeechRecognizer.ERROR_CLIENT ||
                    error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY
                ) {
                    mainHandler.post {
                        if (!isFinishing && !isDestroyed) setupSpeechRecognizer()
                    }
                }

                if (wasManual || wasConversation) {
                    conversationUntil = 0L
                    runOnUiThread {
                        if (::webView.isInitialized) {
                            val message = when (error) {
                                SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ->
                                    "Нет доступа к микрофону. Разрешите J.A.R.V.I.S. доступ к микрофону."
                                SpeechRecognizer.ERROR_AUDIO ->
                                    "Не удалось открыть микрофон. Проверьте, не использует ли микрофон другое приложение."
                                SpeechRecognizer.ERROR_RECOGNIZER_BUSY ->
                                    "Микрофон занят другим распознавателем. Повторите попытку."
                                SpeechRecognizer.ERROR_NETWORK,
                                SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
                                    "Не удалось связаться с сервисом распознавания речи."
                                SpeechRecognizer.ERROR_NO_MATCH,
                                SpeechRecognizer.ERROR_SPEECH_TIMEOUT ->
                                    "Я вас не услышал."
                                else ->
                                    "Не удалось распознать речь. Попробуйте ещё раз."
                            }
                            webView.evaluateJavascript(
                                "window.onJarvisSpeechError && window.onJarvisSpeechError(${JSONObject.quote(message)})",
                                null
                            )
                        }
                    }
                    restartWakeListening()
                    return
                }

                restartWakeListening()
            }
            override fun onResults(results: Bundle?) {
                if (isSpeaking) return
                val wasConversation = conversationUntil > System.currentTimeMillis() || manualListening
                wakeListening = false
                manualListening = false
                conversationUntil = 0L
                val text = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.trim().orEmpty()
                if (text.isBlank()) {
                    restartWakeListening()
                    return
                }
                val escaped = JSONObject.quote(text)
                runOnUiThread {
                    if (::webView.isInitialized) {
                        webView.evaluateJavascript("window.onJarvisSpeechResult && window.onJarvisSpeechResult($escaped)", null)
                    }
                    mainHandler.postDelayed({
                        if (!isSpeaking && conversationUntil <= System.currentTimeMillis() && !manualListening) {
                            restartWakeListening()
                        }
                    }, if (wasConversation) 650L else 350L)
                }
            }
        })
    }

    private fun startListening() {
        startConversationListening(10_000)
    }

    private fun startConversationListening(durationMs: Long) {
        if (isSpeaking) {
            resumeListeningAfterSpeech = true
            return
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestRuntimePermissions()
            runOnUiThread {
                if (::webView.isInitialized) {
                    webView.evaluateJavascript(
                        "window.onJarvisSpeechError && window.onJarvisSpeechError(${JSONObject.quote("Разрешите J.A.R.V.I.S. доступ к микрофону.")})",
                        null
                    )
                }
            }
            return
        }
        if (speechRecognizer == null) {
            Toast.makeText(this, "На устройстве не найден сервис распознавания речи.", Toast.LENGTH_SHORT).show()
            runOnUiThread {
                if (::webView.isInitialized) {
                    webView.evaluateJavascript(
                        "window.onJarvisSpeechError && window.onJarvisSpeechError(${JSONObject.quote("На устройстве не найден сервис распознавания речи.")})",
                        null
                    )
                }
            }
            return
        }
        conversationUntil = System.currentTimeMillis() + durationMs
        wakeListening = false
        manualListening = false
        speechRecognizer?.cancel()
        mainHandler.postDelayed({
            if (conversationUntil > System.currentTimeMillis()) startConversationRecognition()
            else restartWakeListening()
        }, 180)
    }

    private fun startConversationRecognition() {
        if (!activityResumed || isSpeaking) return
        if (conversationUntil <= System.currentTimeMillis() || speechRecognizer == null) {
            conversationUntil = 0L
            restartWakeListening()
            return
        }
        manualListening = true
        try {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ru-RU")
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, "ru-RU")
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            }
            speechRecognizer?.startListening(intent)
        } catch (_: Exception) {
            manualListening = false
            restartConversationListening()
        }
    }

    private fun restartConversationListening() {
        if (isSpeaking) return
        manualListening = false
        if (conversationUntil <= System.currentTimeMillis()) {
            conversationUntil = 0L
            restartWakeListening()
            return
        }
        mainHandler.postDelayed({ startConversationRecognition() }, 250)
    }

    private fun stopRecognitionForSpeech(resumeAfter: Boolean) {
        resumeListeningAfterSpeech = resumeAfter
        isSpeaking = true
        wakeListening = false
        manualListening = false
        conversationUntil = 0L
        speechRecognizer?.cancel()
    }

    private fun finishSpeech() {
        runOnUiThread {
            isSpeaking = false
            val shouldResume = resumeListeningAfterSpeech
            resumeListeningAfterSpeech = false
            if (shouldResume && !isFinishing && !isDestroyed) {
                startConversationListening(conversationResumeDurationMs)
            }
        }
    }

    private fun speak(text: String, resumeAfterSpeech: Boolean = false) {
        if (text.isBlank()) return
        stopRecognitionForSpeech(resumeAfterSpeech)
        val apiKey = prefs.getString("fish_api_key", "").orEmpty()
        val fishVoice = FishAudioTts.voiceIdFor(selectedPersona)
        if (apiKey.isNotBlank() && !fishVoice.isNullOrBlank()) {
            fishAudioTts.speak(
                text,
                selectedPersona,
                onError = { _ ->
                    runOnUiThread {
                        val fallbackId = "jarvis-response-fallback-${System.currentTimeMillis()}"
                        val fallbackTts = tts
                        if (fallbackTts != null) {
                            val result = fallbackTts.speak(
                                text,
                                TextToSpeech.QUEUE_FLUSH,
                                null,
                                fallbackId
                            )
                            if (result == TextToSpeech.ERROR) {
                                finishSpeech()
                            }
                            Toast.makeText(this, "Fish Audio недоступен — использую системный голос.", Toast.LENGTH_SHORT).show()
                        } else {
                            // If the system TTS is not initialized, do not leave JARVIS stuck in speaking mode.
                            finishSpeech()
                        }
                    }
                },
                onComplete = { finishSpeech() }
            )
        } else {
            val systemTts = tts
            if (systemTts == null) {
                finishSpeech()
                return
            }
            if (!ttsReady) {
                mainHandler.postDelayed({
                    if (ttsReady && !isFinishing && !isDestroyed) {
                        speak(text, resumeAfterSpeech)
                    } else {
                        finishSpeech()
                    }
                }, 600)
                return
            }
            val result = systemTts.speak(
                text,
                TextToSpeech.QUEUE_FLUSH,
                null,
                "jarvis-response-${System.currentTimeMillis()}"
            )
            if (result == TextToSpeech.ERROR) {
                // Some devices report TTS failure synchronously. Recover the
                // listening state instead of leaving JARVIS stuck in speaking mode.
                finishSpeech()
            }
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
        if (requestCode != 100) return

        val microphoneGranted =
            ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED

        if (microphoneGranted) {
            runOnUiThread {
                if (::webView.isInitialized) {
                    webView.evaluateJavascript(
                        "window.onJarvisSpeechReady && window.onJarvisSpeechReady()",
                        null
                    )
                }
            }
            mainHandler.postDelayed({ startWakeListening() }, 350)
        } else {
            runOnUiThread {
                if (::webView.isInitialized) {
                    webView.evaluateJavascript(
                        "window.onJarvisSpeechError && window.onJarvisSpeechError(${JSONObject.quote("Доступ к микрофону не разрешён. Включите его в разрешениях Android для J.A.R.V.I.S.")})",
                        null
                    )
                }
            }
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


    private fun fetchNewsAndSpeak() {
        showVoiceStatus("Получаю свежие новости…")
        backgroundExecutor.execute {
            try {
                val feeds = listOf(
                    "https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru",
                    "https://news.google.com/rss?hl=ru&gl=US&ceid=US:ru"
                )
                var items = emptyList<String>()
                var lastError: Exception? = null

                for (feed in feeds) {
                    try {
                        val connection = (URL(feed).openConnection() as HttpURLConnection).apply {
                            requestMethod = "GET"
                            connectTimeout = 10_000
                            readTimeout = 20_000
                            instanceFollowRedirects = true
                            setRequestProperty("User-Agent", "Mozilla/5.0 JARVIS-Android")
                            setRequestProperty("Accept", "application/rss+xml, application/xml, text/xml")
                        }
                        val code = connection.responseCode
                        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                        val xml = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
                        connection.disconnect()
                        if (code !in 200..299) throw IllegalStateException("HTTP $code")

                        items = Regex("<item>([\\s\\S]*?)</item>", RegexOption.IGNORE_CASE)
                            .findAll(xml)
                            .mapNotNull { match ->
                                val block = match.groupValues[1]
                                val title = Regex("<title>([\\s\\S]*?)</title>", RegexOption.IGNORE_CASE)
                                    .find(block)?.groupValues?.get(1)
                                    ?.replace("<![CDATA[", "")?.replace("]]>", "")
                                    ?.let { Html.fromHtml(it, Html.FROM_HTML_MODE_LEGACY).toString().trim() }
                                val source = Regex("<source[^>]*>([\\s\\S]*?)</source>", RegexOption.IGNORE_CASE)
                                    .find(block)?.groupValues?.get(1)
                                    ?.replace("<![CDATA[", "")?.replace("]]>", "")
                                    ?.let { Html.fromHtml(it, Html.FROM_HTML_MODE_LEGACY).toString().trim() }
                                title?.takeIf { it.isNotBlank() }?.let {
                                    if (source.isNullOrBlank()) it else "$it — $source"
                                }
                            }
                            .distinct()
                            .take(6)
                            .toList()
                        if (items.isNotEmpty()) break
                    } catch (e: Exception) {
                        lastError = e
                    }
                }

                if (items.isEmpty()) throw lastError ?: IllegalStateException("В новостной ленте нет материалов.")
                val prompt = "Сделай краткую нейтральную голосовую сводку свежих новостей на русском языке. Назови 5-6 главных тем по заголовкам ниже, по 1-2 предложения на тему. Не придумывай факты и явно отделяй заголовок от неподтвержденных деталей. Заголовки: " + items.joinToString(" | ")
                val answer = gigaChat.ask(prompt, selectedPersona, "")
                val finalText = if (answer.startsWith("В настройках J.A.R.V.I.S.")) {
                    "Свежие новости: " + items.take(5).joinToString(". ")
                } else answer
                runOnUiThread {
                    if (::webView.isInitialized) {
                        webView.evaluateJavascript("window.onGigaChatResult && window.onGigaChatResult(${JSONObject.quote(finalText)})", null)
                    }
                    speak(finalText, resumeAfterSpeech = true)
                }
            } catch (e: Exception) {
                val message = "Не удалось получить свежие новости: ${e.message ?: "ошибка соединения"}"
                runOnUiThread {
                    if (::webView.isInitialized) {
                        webView.evaluateJavascript("window.onGigaChatResult && window.onGigaChatResult(${JSONObject.quote(message)})", null)
                    }
                    speak(message, resumeAfterSpeech = true)
                }
            }
        }
    }

    private fun analyzeLatestWhatsApp() {
        mainHandler.postDelayed({
            backgroundExecutor.execute {
                val notification = JarvisNotificationService.latest(30)
                    .firstOrNull { JarvisNotificationService.isWhatsApp(it.packageName) }
                val screen = if (notification == null) {
                    JarvisAccessibilityService.instance?.visibleText().orEmpty()
                } else {
                    ""
                }
                val source = buildString {
                    if (notification != null) {
                        append("Последнее уведомление WhatsApp. Отправитель/чат: ")
                        append(notification.title)
                        append(". Текст: ")
                        append(notification.text)
                    }
                    if (screen.isNotBlank()) {
                        if (isNotEmpty()) append("\n\n")
                        append("Текст, видимый на открытом экране WhatsApp:\n")
                        append(screen.take(8000))
                    }
                }.trim()

                val answer = if (source.isBlank()) {
                    "Я открыл WhatsApp, но не смог получить текст последнего сообщения. Проверьте доступ J.A.R.V.I.S. к уведомлениям и специальным возможностям."
                } else {
                    val prompt = "Проанализируй последнее сообщение WhatsApp по данным ниже. Ответь по-русски коротко и естественно для голосового ассистента. Обязательно назови имя отправителя или название группы, если оно видно. Затем объясни простыми словами, о чём сообщение, что человек или группа сообщает, просит или хочет. Не выдумывай отсутствующие сведения и скажи, если данных недостаточно. Данные WhatsApp:\n" + source
                    val result = gigaChat.ask(prompt, selectedPersona, "")
                    if (result.startsWith("В настройках J.A.R.V.I.S.")) {
                        "Последнее сообщение: ${notification?.title.orEmpty()}. ${notification?.text.orEmpty()}".trim()
                    } else result
                }

                runOnUiThread {
                    if (::webView.isInitialized) {
                        webView.evaluateJavascript("window.onGigaChatResult && window.onGigaChatResult(${JSONObject.quote(answer)})", null)
                    }
                    speak(answer, resumeAfterSpeech = true)
                }
            }
        }, 1500)
    }

    private fun showVoiceStatus(text: String) {
        runOnUiThread {
            if (::webView.isInitialized) {
                webView.evaluateJavascript("window.onGigaChatResult && window.onGigaChatResult(${JSONObject.quote(text)})", null)
            }
        }
    }

    private fun sendToGigaChat(text: String, memoryText: String = text) {
        backgroundExecutor.execute {
            val answer = gigaChat.ask(text, selectedPersona, memory.memoryContext())
            memory.rememberTurn(memoryText, answer)
            runOnUiThread {
                if (::webView.isInitialized) {
                    val escaped = JSONObject.quote(answer)
                    webView.evaluateJavascript("window.onGigaChatResult && window.onGigaChatResult($escaped)", null)
                }
                speak(answer, resumeAfterSpeech = true)
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
        if (!activityResumed || isSpeaking) return
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
        if (isSpeaking) return
        if (conversationUntil > System.currentTimeMillis()) {
            restartConversationListening()
            return
        }
        wakeListening = false
        mainHandler.postDelayed({ startWakeListening() }, 350)
    }

    override fun onResume() {
        super.onResume()
        activityResumed = true
        startWakeListening()
    }

    override fun onPause() {
        activityResumed = false
        wakeListening = false
        manualListening = false
        conversationUntil = 0L
        mainHandler.removeCallbacksAndMessages(null)
        speechRecognizer?.cancel()
        runOnUiThread {
            if (::webView.isInitialized) {
                webView.evaluateJavascript(
                    "window.onJarvisSpeechReady && window.onJarvisSpeechReady()",
                    null
                )
            }
        }
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
            val memoryText = text.substringAfter("Запрос пользователя: ", text).trim()
            rememberUserName(memoryText)
            memory.recordHabit(memoryText)
            val normalized = memoryText.lowercase()
            if (
                normalized.contains("кто мне написал") ||
                normalized.contains("прочитай сообщения") ||
                normalized.contains("прочитай сообщение") ||
                normalized.contains("новые сообщения")
            ) return notificationReply()

            if (
                normalized.contains("кто тебя создал") ||
                normalized.contains("кто тебя разработал") ||
                normalized.contains("кто тебя придумал") ||
                normalized.contains("кто твой создатель") ||
                normalized.contains("кто создал тебя")
            ) {
                val answer = if (selectedPersona == "J.A.R.V.I.S.") {
                    "Я J.A.R.V.I.S. — искусственный интеллект и голосовой помощник Тони Старка из фильма «Железный человек»."
                } else {
                    "Я $selectedPersona — персонаж J.A.R.V.I.S. и мой создатель — сам J.A.R.V.I.S. из фильма «Железный человек»."
                }
                memory.rememberTurn(memoryText, answer)
                return answer
            }

            if (
                normalized.contains("последние чаты") ||
                normalized.contains("покажи последние чаты") ||
                normalized.contains("последние разговоры") ||
                normalized.contains("последний чат") ||
                normalized.contains("что мы обсуждали") ||
                normalized.contains("что я спрашивал") ||
                normalized.contains("что я спрашивала")
            ) {
                val dialogues = memory.recentDialogues().takeLast(8)
                val answer = if (dialogues.isEmpty()) {
                    "Я пока не сохранил прошлые диалоги."
                } else {
                    buildString {
                        append("Вот последние сохранённые диалоги:\n")
                        dialogues.forEachIndexed { index, pair ->
                            append(index + 1).append(". Вы: ").append(pair.first)
                                .append(" | Я: ").append(pair.second).append("\n")
                        }
                    }.trim()
                }
                memory.rememberTurn(memoryText, answer)
                return answer
            }

            if (
                normalized == "что ты помнишь обо мне" ||
                normalized == "что ты обо мне помнишь" ||
                normalized == "что ты знаешь обо мне" ||
                normalized == "какую информацию ты обо мне помнишь"
            ) {
                val answer = memory.factsSummary()
                memory.rememberTurn(memoryText, answer)
                return answer
            }

            if (
                normalized.startsWith("запомни что ") ||
                normalized.startsWith("запомни, что ") ||
                normalized.startsWith("запомни: ")
            ) {
                val factText = memoryText
                    .replaceFirst(Regex("(?i)^запомни\\s*,?\\s*"), "")
                    .trim()
                val answer = if (memory.rememberFact(factText)) {
                    "Запомнил: $factText"
                } else {
                    "Не получилось сохранить информацию. Скажите, что именно нужно запомнить."
                }
                memory.rememberTurn(memoryText, answer)
                return answer
            }

            if (
                normalized == "забудь это" ||
                normalized == "забудь последнее" ||
                normalized == "забудь последнюю информацию"
            ) {
                val answer = if (memory.forgetLastFact()) {
                    "Хорошо, последнюю сохранённую информацию забыл."
                } else {
                    "У меня нет сохранённого факта, который можно забыть."
                }
                memory.rememberTurn(memoryText, answer)
                return answer
            }

            if (normalized.startsWith("забудь что ") || normalized.startsWith("забудь, что ")) {
                val query = memoryText.replaceFirst(Regex("(?i)^забудь\\s*,?\\s*что\\s*"), "").trim()
                val answer = if (memory.forgetFact(query)) {
                    "Хорошо, эту информацию забыл."
                } else {
                    "Я не нашёл такую информацию в памяти."
                }
                memory.rememberTurn(memoryText, answer)
                return answer
            }

            if (
                normalized == "новости" ||
                normalized.contains("сводка новостей") ||
                normalized.contains("последние новости") ||
                normalized.contains("главные новости")
            ) {
                fetchNewsAndSpeak()
                memory.rememberTurn(memoryText, "Получаю свежую сводку новостей.")
                return "Получаю свежую сводку новостей."
            }

            if (
                normalized.contains("прочитай последнее сообщение в ватсап") ||
                normalized.contains("прочитай последнее сообщение whatsapp")
            ) {
                val hasStoredMessage = JarvisNotificationService.latest(30)
                    .any { JarvisNotificationService.isWhatsApp(it.packageName) }
                val result = if (hasStoredMessage) {
                    "Читаю последнее сообщение WhatsApp."
                } else {
                    router.execute(text)
                }
                analyzeLatestWhatsApp()
                memory.rememberTurn(memoryText, result)
                return result
            }

            if (router.canHandle(text)) {
                val result = router.execute(text)
                memory.rememberTurn(memoryText, result)
                return result
            }
            sendToGigaChat(text, memoryText)
            return ""
        }

        @JavascriptInterface fun startListening() { runOnUiThread { this@MainActivity.startListening() } }
        @JavascriptInterface fun startConversationWindow(seconds: Int) {
            runOnUiThread { this@MainActivity.startConversationListening(seconds.coerceIn(1, 30) * 1000L) }
        }
        @JavascriptInterface fun speak(text: String) { runOnUiThread { this@MainActivity.speak(text, resumeAfterSpeech = false) } }
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
            JarvisNotificationService.clear(this@MainActivity)
            return "История уведомлений J.A.R.V.I.S. очищена."
        }

        @JavascriptInterface fun checkUpdates() { checkForUpdates(true) }
        @JavascriptInterface fun toast(text: String) { runOnUiThread { Toast.makeText(this@MainActivity, text, Toast.LENGTH_SHORT).show() } }
    }

    override fun onDestroy() {
        activityResumed = false
        mainHandler.removeCallbacksAndMessages(null)
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
