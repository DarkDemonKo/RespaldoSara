import customtkinter as ctk

def actualizar_color(val):
    # Obtener valores
    r = int(slider_r.get())
    g = int(slider_g.get())
    b = int(slider_b.get())
    
    # Convertir a formato hexadecimal
    color_hex = f'#{r:02x}{g:02x}{b:02x}'
    
    # Actualizar UI
    caja_color.configure(fg_color=color_hex)
    texto_color = "black" if (r*0.299 + g*0.587 + b*0.114) > 186 else "white"
    
    label_resultado.configure(
        text=f'Hex: {color_hex.upper()}\nRGB: ({r}, {g}, {b})', 
        text_color=texto_color
    )

    label_valor_r.configure(text=str(r))
    label_valor_g.configure(text=str(g))
    label_valor_b.configure(text=str(b))

# Configuración de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ventana = ctk.CTk()
ventana.title("Mezclador de Colores Pro")
ventana.geometry("450x550")

# Contenedor Principal
frame_principal = ctk.CTkFrame(ventana)
frame_principal.pack(pady=20, padx=20, fill="both", expand=True)

titulo = ctk.CTkLabel(frame_principal, text="🎨 Mezclador RGB", font=("Roboto", 24, "bold"))
titulo.pack(pady=(15, 20))

# --- Controles ---
# ROJO
ctk.CTkLabel(frame_principal, text="Rojo", text_color="#FF4C4C", font=("Roboto", 14, "bold")).pack()
slider_r = ctk.CTkSlider(frame_principal, from_=0, to=255, progress_color="#FF4C4C", button_color="#FF4C4C", button_hover_color="#CC0000", command=actualizar_color)
slider_r.pack(pady=(0, 5))
label_valor_r = ctk.CTkLabel(frame_principal, text="127")
label_valor_r.pack(pady=(0, 10))

# VERDE
ctk.CTkLabel(frame_principal, text="Verde", text_color="#4CFF4C", font=("Roboto", 14, "bold")).pack()
slider_g = ctk.CTkSlider(frame_principal, from_=0, to=255, progress_color="#4CFF4C", button_color="#4CFF4C", button_hover_color="#00CC00", command=actualizar_color)
slider_g.pack(pady=(0, 5))
label_valor_g = ctk.CTkLabel(frame_principal, text="127")
label_valor_g.pack(pady=(0, 10))

# AZUL
ctk.CTkLabel(frame_principal, text="Azul", text_color="#4C4CFF", font=("Roboto", 14, "bold")).pack()
slider_b = ctk.CTkSlider(frame_principal, from_=0, to=255, progress_color="#4C4CFF", button_color="#4C4CFF", button_hover_color="#0000CC", command=actualizar_color)
slider_b.pack(pady=(0, 5))
label_valor_b = ctk.CTkLabel(frame_principal, text="127")
label_valor_b.pack(pady=(0, 20))

# --- Caja de Resultado ---
caja_color = ctk.CTkFrame(frame_principal, height=100, corner_radius=15)
caja_color.pack(pady=10, padx=20, fill="x")
caja_color.pack_propagate(False)

label_resultado = ctk.CTkLabel(caja_color, text="Hex: #000000\nRGB: (0, 0, 0)", font=("Roboto", 16, "bold"))
label_resultado.pack(expand=True)

# Iniciar
slider_r.set(127)
slider_g.set(127)
slider_b.set(127)
actualizar_color(None)

ventana.mainloop()
