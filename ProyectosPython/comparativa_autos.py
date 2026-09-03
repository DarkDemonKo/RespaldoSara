def main():
    # Datos de los autos (hasta 5, como pediste)
    autos = [
        {"modelo": "Nissan Versa", "año": 2024, "precio": 339900, "tipo": "Sedán"},
        {"modelo": "Kia Rio", "año": 2023, "precio": 288900, "tipo": "Hatchback"},
        {"modelo": "Toyota Corolla", "año": 2024, "precio": 419900, "tipo": "Sedán"},
        {"modelo": "Honda CR-V", "año": 2024, "precio": 739900, "tipo": "SUV"},
        {"modelo": "Mazda 3", "año": 2024, "precio": 388900, "tipo": "Sedán"}
    ]

    print("=" * 65)
    print(f"{'- COMPARATIVA DE PRECIOS DE AUTOS -':^65}")
    print("=" * 65)
    
    # Encabezados de la tabla
    print(f"{'Modelo / Marca':<20} | {'Año':<6} | {'Tipo':<12} | {'Precio (MXN)':<15}")
    print("-" * 65)

    # Filas de la tabla
    for auto in autos:
        # Formateamos el precio con comas para que sea más fácil de leer
        precio_formateado = f"${auto['precio']:,}"
        print(f"{auto['modelo']:<20} | {auto['año']:<6} | {auto['tipo']:<12} | {precio_formateado:<15}")
    
    print("=" * 65)

if __name__ == "__main__":
    main()
