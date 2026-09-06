package com.darkdemon.yuna

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : AppCompatActivity() {

    private lateinit var chatLogic: YunaChatLogic

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        chatLogic = YunaChatLogic()

        val chatView = findViewById<TextView>(R.id.chatView)
        val inputMessage = findViewById<EditText>(R.id.inputMessage)
        val btnSend = findViewById<Button>(R.id.btnSend)

        btnSend.setOnClickListener {
            val message = inputMessage.text.toString()
            if (message.isNotBlank()) {
                chatView.append("\nPapá: $message")
                inputMessage.text.clear()

                CoroutineScope(Dispatchers.Main).launch {
                    val response = chatLogic.sendToYuna(message)
                    chatView.append("\nYuna: $response")
                }
            }
        }
    }
}
