"""Pau Pont Camp.

Manejo de ficheros WAVE PCM para convertir señales estéreo y mono,
y codificar/decodificar señales estéreo usando semisuma y semidiferencia.
"""

import struct


def _leer_wave(nombre):
    with open(nombre, "rb") as fichero:
        if fichero.read(4) != b"RIFF":
            raise ValueError("El fichero no es RIFF")

        fichero.read(4)

        if fichero.read(4) != b"WAVE":
            raise ValueError("El fichero no es WAVE")

        fmt = None
        datos = None

        while True:
            cabecera = fichero.read(8)
            if not cabecera:
                break
            if len(cabecera) != 8:
                raise ValueError("Cacho WAVE incompleto")

            nombre_cacho, tamanyo = struct.unpack("<4sI", cabecera)
            contenido = fichero.read(tamanyo)

            if len(contenido) != tamanyo:
                raise ValueError("Cacho WAVE corrupto")

            if tamanyo % 2:
                fichero.read(1)

            if nombre_cacho == b"fmt ":
                fmt = contenido
            elif nombre_cacho == b"data":
                datos = contenido

        if fmt is None or datos is None:
            raise ValueError("Faltan los cachos fmt o data")

        if len(fmt) < 16:
            raise ValueError("Cacho fmt incorrecto")

        formato = struct.unpack("<HHIIHH", fmt[:16])
        audio_format, canales, frecuencia, byte_rate, align, bits = formato

        if audio_format != 1:
            raise ValueError("Sólo se admite PCM lineal")

        if len(datos) % align != 0:
            raise ValueError("Tamaño de datos incorrecto")

        return {
            "canales": canales,
            "frecuencia": frecuencia,
            "bits": bits,
            "datos": datos,
        }


def _escribir_wave(nombre, canales, frecuencia, bits, datos):
    align = canales * bits // 8
    byte_rate = frecuencia * align
    tamanyo_fmt = 16
    tamanyo_riff = 4 + 8 + tamanyo_fmt + 8 + len(datos)

    with open(nombre, "wb") as fichero:
        fichero.write(b"RIFF")
        fichero.write(struct.pack("<I", tamanyo_riff))
        fichero.write(b"WAVE")

        fichero.write(b"fmt ")
        fichero.write(struct.pack("<I", tamanyo_fmt))
        fichero.write(struct.pack(
            "<HHIIHH",
            1,
            canales,
            frecuencia,
            byte_rate,
            align,
            bits,
        ))

        fichero.write(b"data")
        fichero.write(struct.pack("<I", len(datos)))
        fichero.write(datos)


def _limitar_16(valor):
    return max(-32768, min(32767, valor))


def _muestras_16(datos):
    return struct.unpack("<{}h".format(len(datos) // 2), datos)


def _muestras_32(datos):
    return struct.unpack("<{}i".format(len(datos) // 4), datos)


def _empaquetar_16(muestras):
    return struct.pack("<{}h".format(len(muestras)), *muestras)


def _empaquetar_32(muestras):
    return struct.pack("<{}i".format(len(muestras)), *muestras)


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
