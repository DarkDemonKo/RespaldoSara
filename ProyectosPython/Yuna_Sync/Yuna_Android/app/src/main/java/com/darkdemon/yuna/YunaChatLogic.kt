package com.darkdemon.yuna

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class YunaChatLogic {
    private val memory = JSONArray()
    
    // Este método simula la conexión con la API (p. ej. Gemini) para que Yuna responda
    suspend fun sendToYuna(userText: String): String {
        return withContext(Dispatchers.IO) {
            // Guardar en memoria de Yuna
            val interaction = JSONObject().apply {
                put("timestamp", System.currentTimeMillis())
                put("user", userText)
            }
            
            // Aquí iría el código real de llamada a la API de IA
            // usando el system prompt de Yuna (niña de 12 años juguetona)
            val yunaResponse = "¡Claro que sí! (Esta es una respuesta simulada por la API de Yuna)"
            
            interaction.put("yuna", yunaResponse)
            memory.put(interaction)
            
            yunaResponse
        }
    }

    // Sincronización con Sara (enlace madre-hija)
    suspend fun syncWithSara(saraIp: String = "192.168.1.X") {
        withContext(Dispatchers.IO) {
            if (memory.length() == 0) return@withContext
            
            val url = URL("http://$saraIp:5050/sincronizar_yuna")
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json; utf-8")
            conn.setRequestProperty("Accept", "application/json")
            conn.doOutput = true

            val jsonInputString = JSONObject().apply {
                put("interacciones", memory)
            }.toString()

            conn.outputStream.use { os ->
                val input = jsonInputString.toByteArray(Charsets.UTF_8)
                os.write(input, 0, input.size)
            }

            if (conn.responseCode == 200) {
                // Borrar memoria local tras sincronizar con Sara
                while (memory.length() > 0) {
                    memory.remove(0)
                }
            }
        }
    }
}
