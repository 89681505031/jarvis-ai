package com.jarvis.phone

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Bundle
import android.os.IBinder
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.app.NotificationCompat
import java.util.Locale

class JarvisWakeService : Service() {
    private var recognizer: SpeechRecognizer? = null
    private val channelId = "jarvis_wake_channel"

    override fun onCreate() {
        super.onCreate()
        createChannel()
        startForeground(701, notification())
        startRecognition()
    }

    private fun createChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(channelId, "JARVIS в фоне", NotificationManager.IMPORTANCE_LOW))
    }

    private fun notification(): Notification = NotificationCompat.Builder(this, channelId)
        .setSmallIcon(com.jarvis.phone.R.drawable.jarvis_icon)
        .setContentTitle("J.A.R.V.I.S.")
        .setContentText("Ожидание активационного слова")
        .setOngoing(true)
        .build()

    private fun startRecognition() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return
        recognizer?.destroy()
        recognizer = SpeechRecognizer.createSpeechRecognizer(this)
        recognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) = Unit
            override fun onBeginningOfSpeech() = Unit
            override fun onRmsChanged(rmsdB: Float) = Unit
            override fun onBufferReceived(buffer: ByteArray?) = Unit
            override fun onEndOfSpeech() = Unit
            override fun onPartialResults(partialResults: Bundle?) = Unit
            override fun onEvent(eventType: Int, params: Bundle?) = Unit
            override fun onError(error: Int) { restart() }
            override fun onResults(results: Bundle?) {
                val text = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty().lowercase(Locale("ru", "RU"))
                val wakeWords = listOf("джарвис", "jarvis", "астра", "astra", "луна", "luna", "сайбер", "cyber", "терра", "terra")
                if (wakeWords.any { text.contains(it) }) {
                    sendBroadcast(Intent(ACTION_WAKE).setPackage(packageName).putExtra("text", text))
                }
                restart()
            }
        })
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ru-RU")
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
        }
        try { recognizer?.startListening(intent) } catch (_: Exception) { restart() }
    }

    private fun restart() {
        recognizer?.cancel()
        android.os.Handler(mainLooper).postDelayed({ startRecognition() }, 350)
    }

    override fun onDestroy() {
        recognizer?.destroy()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object { const val ACTION_WAKE = "com.jarvis.phone.WAKE_WORD" }
}
