def fibonacci(n):
    if n < 0:
        return "El número debe ser mayor o igual a 0."
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    try:
        n = int(input("Ingrese qué posición de la secuencia de Fibonacci desea (ej. 10): "))
        resultado = fibonacci(n)
        print(f"El número de Fibonacci en la posición {n} es: {resultado}")
    except ValueError:
        print("Por favor, ingrese un número entero válido.")

if __name__ == "__main__":
    main()
