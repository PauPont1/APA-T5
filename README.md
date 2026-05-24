# Sonido estéreo y ficheros WAVE

## Alumno

Pau Pont

## Descripción

En esta práctica se ha desarrollado el fichero `estereo.py`, que permite trabajar con señales de audio en formato WAVE PCM utilizando exclusivamente el módulo `struct`.

Las funciones implementadas permiten:

- Convertir señales estéreo en señales monofónicas.
- Construir señales estéreo a partir de dos señales mono.
- Codificar señales estéreo mediante semisuma y semidiferencia.
- Decodificar señales codificadas para reconstruir los canales originales.

## Funciones implementadas

### estereo2mono(ficEste, ficMono, canal=2)

Lee una señal estéreo de 16 bits y genera una señal monofónica.

Opciones disponibles:

- canal = 0 → canal izquierdo.
- canal = 1 → canal derecho.
- canal = 2 → semisuma `(L + R) / 2`.
- canal = 3 → semidiferencia `(L - R) / 2`.

```python
def estereo2mono(ficEste, ficMono, canal=2):
    wave = _leer_wave(ficEste)

    if wave["canales"] != 2 or wave["bits"] != 16:
        raise ValueError("El fichero debe ser estéreo de 16 bits")

    muestras = _muestras_16(wave["datos"])
    pares = list(zip(muestras[0::2], muestras[1::2]))

    if canal == 0:
        salida = [izq for izq, der in pares]
    elif canal == 1:
        salida = [der for izq, der in pares]
    elif canal == 2:
        salida = [_limitar_16((izq + der) // 2) for izq, der in pares]
    elif canal == 3:
        salida = [_limitar_16((izq - der) // 2) for izq, der in pares]
    else:
        raise ValueError("El canal debe ser 0, 1, 2 o 3")

    datos = _empaquetar_16(salida)
    _escribir_wave(ficMono, 1, wave["frecuencia"], 16, datos)
```

### mono2estereo(ficIzq, ficDer, ficEste)

Lee dos señales monofónicas de 16 bits y genera una señal estéreo intercalando las muestras de ambos canales.

```python
def mono2estereo(ficIzq, ficDer, ficEste):
    izq = _leer_wave(ficIzq)
    der = _leer_wave(ficDer)

    if izq["canales"] != 1 or der["canales"] != 1:
        raise ValueError("Los dos ficheros deben ser monofónicos")

    if izq["bits"] != 16 or der["bits"] != 16:
        raise ValueError("Los dos ficheros deben ser de 16 bits")

    if izq["frecuencia"] != der["frecuencia"]:
        raise ValueError("Las frecuencias de muestreo deben coincidir")

    muestras_izq = _muestras_16(izq["datos"])
    muestras_der = _muestras_16(der["datos"])

    if len(muestras_izq) != len(muestras_der):
        raise ValueError("Los dos canales deben tener la misma longitud")

    muestras = [
        muestra
        for par in zip(muestras_izq, muestras_der)
        for muestra in par
    ]

    datos = _empaquetar_16(muestras)
    _escribir_wave(ficEste, 2, izq["frecuencia"], 16, datos)
```

### codEstereo(ficEste, ficCod)

Lee una señal estéreo de 16 bits y la codifica en una señal monofónica de 32 bits.

La codificación utilizada almacena:

- En los 16 bits más significativos: la semisuma `(L + R) / 2`.
- En los 16 bits menos significativos: la semidiferencia `(L - R) / 2`.

De este modo la señal puede reproducirse en sistemas monofónicos y reconstruirse posteriormente en sistemas estéreo.

```python
def codEstereo(ficEste, ficCod):
    wave = _leer_wave(ficEste)

    if wave["canales"] != 2 or wave["bits"] != 16:
        raise ValueError("El fichero debe ser estéreo de 16 bits")

    muestras = _muestras_16(wave["datos"])
    pares = zip(muestras[0::2], muestras[1::2])

    codificadas = [
        (((izq + der) // 2) << 16) | (((izq - der) // 2) & 0xFFFF)
        for izq, der in pares
    ]

    datos = _empaquetar_32(codificadas)
    _escribir_wave(ficCod, 1, wave["frecuencia"], 32, datos)
```

### decEstereo(ficCod, ficEste)

Lee una señal monofónica de 32 bits codificada mediante semisuma y semidiferencia y reconstruye los canales izquierdo y derecho para generar una señal estéreo estándar.

```python
def decEstereo(ficCod, ficEste):
    wave = _leer_wave(ficCod)

    if wave["canales"] != 1 or wave["bits"] != 32:
        raise ValueError("El fichero debe ser mono de 32 bits")

    muestras = _muestras_32(wave["datos"])

    def desempaquetar(valor):
        semisuma = valor >> 16
        semidiferencia = valor & 0xFFFF

        if semidiferencia >= 0x8000:
            semidiferencia -= 0x10000

        izq = _limitar_16(semisuma + semidiferencia)
        der = _limitar_16(semisuma - semidiferencia)

        return izq, der

    muestras_estereo = [
        muestra
        for par in map(desempaquetar, muestras)
        for muestra in par
    ]

    datos = _empaquetar_16(muestras_estereo)
    _escribir_wave(ficEste, 2, wave["frecuencia"], 16, datos)
```

## Estructura del proyecto

```text
.
├── estereo.py
└── README.md
```

## Aspectos destacados

- Uso exclusivo del módulo `struct`.
- Gestión de ficheros mediante gestores de contexto (`with`).
- Verificación del formato WAVE PCM.
- Generación de cabeceras RIFF/WAVE válidas.
- Compatibilidad con reproductores estándar.

## Pruebas realizadas

Se han realizado pruebas utilizando los ficheros proporcionados para la práctica verificando:

- Conversión estéreo a mono.
- Conversión mono a estéreo.
- Codificación estéreo.
- Decodificación estéreo.

## Conclusiones

La práctica ha permitido comprender la estructura interna de los ficheros WAVE, el manejo de datos binarios mediante el módulo `struct` y la implementación de sistemas de codificación estéreo compatibles con sistemas monofónicos.
