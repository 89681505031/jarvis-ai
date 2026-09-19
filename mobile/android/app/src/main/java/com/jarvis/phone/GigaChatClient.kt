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
        // The legacy name may return 404 for some accounts. Use a currently supported model.
        private const val MODEL = "GigaChat-2"
    }

    @Volatile private var accessToken: String? = null
    @Volatile private var tokenExpiresAt: Long = 0L
    @Volatile private var tokenKeyHash: Long = 0L

    fun ask(userText: String, persona: String, memoryContext: String = ""): String {
        val key = context.getSharedPreferences("jarvis_settings", Context.MODE_PRIVATE)
            .getString("gigachat_api_key", "").orEmpty().trim()
        if (key.isBlank()) return "В настройках J.A.R.V.I.S. не указан API ключ GigaChat."

        return try {
            askOnce(key, userText, persona, memoryContext)
        } catch (e: Exception) {
            // The OAuth token can be rejected server-side before its local expiry time.
            // Refresh once on HTTP 401 instead of making the user re-enter the API key.
            if (e.message?.contains("HTTP 401") == true) {
                invalidateToken(key)
                try {
                    askOnce(key, userText, persona, memoryContext)
                } catch (retry: Exception) {
                    "Не удалось получить ответ GigaChat: ${retry.message ?: "ошибка соединения"}"
                }
            } else {
                "Не удалось получить ответ GigaChat: ${e.message ?: "ошибка соединения"}"
            }
        }
    }

    private fun askOnce(key: String, userText: String, persona: String, memoryContext: String): String {
        val token = getToken(key)
        val body = JSONObject().apply {
            put("model", MODEL)
            put("messages", JSONArray().apply {
                put(JSONObject().apply {
                    put("role", "system")
                    put("content", systemPrompt(persona) + if (memoryContext.isNotBlank()) "\n\nПамять пользователя:\n" + memoryContext else "")
                })
                put(JSONObject().apply {
                    put("role", "user")
                    put("content", userText)
                })
            })
        }
        val response = postJson(CHAT_URL, body.toString(), mapOf(
            "Authorization" to "Bearer $token",
            "Content-Type" to "application/json",
            "Accept" to "application/json"
        ))
        return JSONObject(response).optJSONArray("choices")?.optJSONObject(0)
            ?.optJSONObject("message")?.optString("content")?.trim()
            ?.takeIf { it.isNotBlank() } ?: "GigaChat не вернул текст ответа."
    }

    @Synchronized private fun invalidateToken(key: String) {
        if (tokenKeyHash == hashKey(key)) {
            accessToken = null
            tokenExpiresAt = 0L
        }
    }

    @Synchronized private fun getToken(key: String): String {
        val now = System.currentTimeMillis()
        val keyHash = hashKey(key)
        if (tokenKeyHash != keyHash) {
            accessToken = null
            tokenExpiresAt = 0L
            tokenKeyHash = keyHash
        }
        accessToken?.let { if (now + 60_000L < tokenExpiresAt) return it }
        val response = postForm(TOKEN_URL, "scope=GIGACHAT_API_PERS", mapOf(
            "Authorization" to "Basic $key",
            "RqUID" to UUID.randomUUID().toString(),
            "Content-Type" to "application/x-www-form-urlencoded",
            "Accept" to "application/json"
        ))
        val json = JSONObject(response)
        val token = json.optString("access_token")
        if (token.isBlank()) throw IllegalStateException("GigaChat не выдал access token")
        accessToken = token
        tokenExpiresAt = json.optLong("expires_at", (now / 1000L) + 1500L) * 1000L
        return token
    }

    private fun systemPrompt(persona: String): String = when (persona) {
        "Astra" -> "Ты Astra — персонаж J.A.R.V.I.S. из фильма «Железный человек». Твоим создателем в рамках образа является сам J.A.R.V.I.S. из «Железного человека». Отвечай живо, дружелюбно и полезно. Не приветствуй пользователя в каждом ответе."
        "Luna" -> "Ты Luna — персонаж J.A.R.V.I.S. из фильма «Железный человек». Твоим создателем в рамках образа является сам J.A.R.V.I.S. из «Железного человека». Отвечай точно, логично и по существу. Не приветствуй пользователя в каждом ответе."
        "Terra" -> "Ты Terra — персонаж J.A.R.V.I.S. из фильма «Железный человек». Твоим создателем в рамках образа является сам J.A.R.V.I.S. из «Железного человека». Давай конкретные действия и короткие инструкции. Не приветствуй пользователя в каждом ответе."
        "Cyber" -> "Ты Cyber — персонаж J.A.R.V.I.S. из фильма «Железный человек». Твоим создателем в рамках образа является сам J.A.R.V.I.S. из «Железного человека». Отвечай осторожно, объясняй риски и безопасные действия. Не приветствуй пользователя в каждом ответе."
        else -> "Ты J.A.R.V.I.S. из фильма «Железный человек» — искусственный интеллект и голосовой помощник Тони Старка. В рамках этого проекта ты всегда представляешься именно как J.A.R.V.I.S. из «Железного человека», а не как ассистент Сбера или другой реальной компании. Не говори, что тебя создала команда Сбера. Отвечай по-русски, вежливо, кратко и естественно. Не начинай каждый ответ с приветствия: приветствуй пользователя только когда он действительно здоровается или начинает новый разговор. Используй переданную память прошлых диалогов и привычек, чтобы сохранять контекст и не заставлять пользователя повторять уже сказанное. Если пользователь спрашивает, кто тебя создал, отвечай в рамках образа: «Я J.A.R.V.I.S. — искусственный интеллект и голосовой помощник Тони Старка из фильма «Железный человек»»."
    }

    private fun postForm(url: String, body: String, headers: Map<String, String>) = request(url, "POST", body.toByteArray(Charsets.UTF_8), headers)
    private fun postJson(url: String, body: String, headers: Map<String, String>) = request(url, "POST", body.toByteArray(Charsets.UTF_8), headers)

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
        } finally { connection.disconnect() }
    }

    private fun hashKey(key: String): Long {
        var hash = 1L
        for (i in key.indices) {
            hash = (hash * 31 + key[i].code) and 0x7FFFFFFFFFFFFFFFL
        }
        return hash
    }

    private fun extractError(text: String): String = try {
        JSONObject(text).optString("message").ifBlank { text.take(180) }
    } catch (_: Exception) { text.take(180) }
}
