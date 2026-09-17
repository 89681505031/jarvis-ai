package com.jarvis.phone

import android.content.Context
import android.media.MediaPlayer
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class FishAudioTts(private val context: Context) {
    companion object {
        private const val API_URL = "https://api.fish.audio/v1/tts"
        private const val MODEL = "s2.1-pro-free"
        private const val JARVIS_VOICE_ID = "4c3eaacc1a0545cdb0295bfddf3e3785"
        private const val ASTRA_VOICE_ID = "f6a0ee8b5fa743eca0e931405f319940"
        private const val LUNA_VOICE_ID = "2a1036d645634680b3cc69aeeb60375b"
        private const val CYBER_VOICE_ID = "cc1b79b1108f4ed3b8aac118ba6ebd07"
        private const val TERRA_VOICE_ID = "c962ed46edfd419abc530d1e33a7435f"

        fun voiceIdFor(persona: String): String? = when (persona) {
            "J.A.R.V.I.S." -> JARVIS_VOICE_ID
            "Astra" -> ASTRA_VOICE_ID
            "Luna" -> LUNA_VOICE_ID
            "Terra" -> TERRA_VOICE_ID
            "Cyber" -> CYBER_VOICE_ID
            else -> null
        }
    }

    private val executor = Executors.newSingleThreadExecutor()
    private var player: MediaPlayer? = null

    fun speak(text: String, persona: String, onError: ((String) -> Unit)? = null) {
        val prefs = context.getSharedPreferences("jarvis_settings", Context.MODE_PRIVATE)
        val apiKey = prefs.getString("fish_api_key", "").orEmpty()
        val voiceId = voiceIdFor(persona)
        if (apiKey.isBlank()) { onError?.invoke("Fish Audio API key is not configured"); return }
        if (voiceId.isNullOrBlank()) { onError?.invoke("Voice ID for $persona is not configured"); return }
        executor.execute {
            try {
                val body = "{\"text\":${json(text)},\"reference_id\":${json(voiceId)},\"format\":\"mp3\"}"
                val c = (URL(API_URL).openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"; connectTimeout = 15000; readTimeout = 60000; doOutput = true
                    setRequestProperty("Authorization", "Bearer $apiKey")
                    setRequestProperty("Content-Type", "application/json")
                    setRequestProperty("model", MODEL)
                }
                c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                if (c.responseCode !in 200..299) throw IllegalStateException("Fish Audio HTTP ${c.responseCode}")
                val f = File(context.cacheDir, "jarvis_fish_${System.currentTimeMillis()}.mp3")
                c.inputStream.use { input -> f.outputStream().use { output -> input.copyTo(output) } }; c.disconnect()
                android.os.Handler(android.os.Looper.getMainLooper()).post {
                    try {
                        player?.release()
                        player = MediaPlayer().apply {
                            setDataSource(f.absolutePath)
                            setOnCompletionListener { release(); player = null; f.delete() }
                            setOnErrorListener { _, _, _ -> release(); player = null; f.delete(); true }
                            prepare(); start()
                        }
                    } catch (e: Exception) { f.delete(); onError?.invoke(e.message ?: "Fish Audio playback error") }
                }
            } catch (e: Exception) { onError?.invoke(e.message ?: "Fish Audio request error") }
        }
    }

    fun release() { player?.release(); player = null; executor.shutdownNow() }
    private fun json(v: String) = "\"" + v.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\""
}