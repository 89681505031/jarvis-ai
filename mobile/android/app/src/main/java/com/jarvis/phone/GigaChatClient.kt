package com.jarvis.phone

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

class GigaChatClient(private val context: Context) {
    companion object {
        private const val TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        private const val CHAT_URL = "https://api.giga.chat/v1/chat/completions"
        private const val MODEL = "GigaChat"
    }

    @Volatile private var accessToken: String? = null
    @Volatile private var tokenExpiresAt: Long = 0L

    fun ask(userText: String, persona: String): String {
        val key = context.getSharedPreferences("jarvis_settings", Context.MODE_PRIVATE)
            .getString("gigachat_api_key", "").orEmpty().trim()
        if (key.isBlank()) return "В настройках J.A.R.V.I.S. не указан API ключ GigaChat."

        return try {
            val token = getToken(key)
            val body = JSONObject().apply {
                put("model", MODEL)
                put("messages", JSONArray().apply {
                    put(JSONObject().apply {
                        put("role", "system")
                        put("content", systemPrompt(persona))
                    })
                    put(JSONObject().apply {
                        put("role", "user")
                        put("content", userText)
                    })
                })
            }

            val response = postJson(
                CHAT_URL,
                body.toString(),
                mapOf(
                    "Authorization" to "Bearer $token",
                    "Content-Type" to "application/json",
                    "Accept" to "application/json"
                )
            )

            JSONObject(response).optJSONArray("choices")
                ?.optJSONObject(0)?.optJSONObject("message")?.optString("content")
                ?.trim()?.takeIf { it.isNotBlank() }
                ?: "GigaChat не вернул текст ответа."
        } catch (e: Exception) {
            "Не удалось получить ответ GigaChat: ${e.message ?: "ошибка соединения"}"
        }
    }

    @Synchronized
    private fun getToken(key: String): String {
        val now = System.currentTimeMillis()
        accessToken?.let { if (now + 60_000L < tokenExpiresAt) return it }

        val response = postForm(
            TOKEN_URL,
            "scope=GIGACHAT_API_PERS",
            mapOf(
                "Authorization" to "Basic $key",
                "RqUID" to UUID.randomUUID().toString(),
                "Content-Type" to "application/x-www-form-urlencoded",
                "Accept" to "application/json"
            )
        )

        val json = JSONObject(response)
        val token = json.optString("access_token")
        if (token.isBlank()) throw IllegalStateException("GigaChat не выдал access token")
        accessToken = token
        tokenExpiresAt = json.optLong("expires_at", (now / 1000L) + 1500L) * 1000L
        return token
    }

    private fun systemPrompt(persona: String): String = when (persona) {
        "Astra" -> "Ты Astra, творческий голос мобильного J.A.R.V.I.S. Отвечай живо, дружелюбно и полезно."
        "Luna" -> "Ты Luna, аналитический голос мобильного J.A.R.V.I.S. Отвечай точно, логично и по существу."
        "Terra" -> "Ты Terra, практичный голос мобильного J.A.R.V.I.S. Давай конкретные действия и короткие инструкции."
        "Cyber" -> "Ты Cyber, помощник по безопасности. Отвечай осторожно, объясняй риски и безопасные действия."
        else -> "Ты J.A.R.V.I.S., персональный голосовой ассистент пользователя. Отвечай по-русски, вежливо, кратко и естественно. Обращайся к пользователю как к сэр, когда это уместно."
    }

    private fun postForm(url: String, body: String, headers: Map<String, String>): String =
        request(url, "POST", body.toByteArray(Charsets.UTF_8), headers)

    private fun postJson(url: String, body: String, headers: Map<String, String>): String =
        request(url, "POST", body.toByteArray(Charsets.UTF_8), headers)

    private fun request(urlString: String, method: String, body: ByteArray, headers: Map<String, String>): String {
        val connection = (URL(urlString).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 20_000
            readTimeout = 60_000
            doInput = true
            doOutput = true
            headers.forEach { (name, value) -> setRequestProperty(name, value) }
        }

        return try {
            connection.outputStream.use { it.write(body) }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (code !in 200..299) throw IllegalStateException("HTTP $code: ${extractError(text)}")
            text
        } finally {
            connection.disconnect()
        }
    }

    private fun extractError(text: String): String {
        return try {
            JSONObject(text).optString("message").ifBlank { text.take(180) }
        } catch (_: Exception) {
            text.take(180)
        }
    }
}
