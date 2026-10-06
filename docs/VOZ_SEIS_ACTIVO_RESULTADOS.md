# Seis correcciones activas: controles y banco corto

2026-10-06. Ejecución del [protocolo activo](VOZ_NOTA_LARGA_SEIS_ACTIVO_PROTOCOLO.md)
y su [materialización de controles](VOZ_SEIS_CONTROLES_ADAPTACION_PROTOCOLO.md).

## Build11: variante activa separada

El [build](../evidence/voice_six_build01.json) deriva de build09 con el mismo
GCC UCRT64 y `-O2 -g -m64`/`-m64`. La [auditoría del árbol](../evidence/voice_six_build_validation01.json)
reconstruye los 4338 archivos y confirma sólo dos anclajes cambiados:
el bucle de tres a seis correcciones y el anuncio explícito de seis.
Conserva pares/FMA, factores SMP/KLU existentes, stamps, dispositivos,
lógica de actualización de historia y tolerancias. Los valores publicados
pueden cambiar. Este build sí publica seis al activarse; el
ensayo previo build10 sólo calculaba sobre una copia y restauraba tres.

El ejecutable queda identificado por SHA256
`333174ac4345ae786e515a6e66345e8a36af494e24bf76c63f92c8f1813af505`.
`published_corrections: 6` identifica la variante compilada; en el control
desactivado el flag está ausente y se usa el solve original. Los logs
confirman activación explícita y ausencia de observadores/replay/shadow.

## Control original heredado y dos ejecuciones nuevas

Se reutiliza build06 por identidad de recibo, deck, fuentes, runtime,
ejecutable y export; no se presenta como una nueva ejecución. Build11
desactivado conserva exactamente las 218786 filas, reloj y 31 vectores
del original de 40 ms. Sólo cambian export y ruta de runtime.

Activo: 187157 filas y 40 ms completos. Diferencia
máxima en grilla absoluta: **63.8392713 µV** frente a 5 mV;
DC 2.4873437 pV; frecuencia 9.6856241e-08 cent
frente a 1 cent; 17/17 resets y máximo desfase
2.0151519 ps frente a 10 ns. No hay alineación de fase.

## Cuatro escenas conjuntas

Se conservan DC propio, ON 2 ms/OFF 25 ms, VCO1, mixer, ladder, recuperación,
ambos VCA, contorno cargado y dieciocho vectores. Presupuesto previo:
900 s por proceso. No se cambia ningún byte eléctrico del deck histórico.

| Escena | Filas | Último reloj | Tiempo de laboratorio | Completa |
| --- | ---: | ---: | ---: | --- |
| nominal500 | 191714 | 40.000000000 ms | 321.33 s | Sí |
| nominal250 | 267743 | 40.000000000 ms | 334.62 s | Sí |
| nominal125 | 424429 | 40.000000000 ms | 513.05 s | Sí |
| nominal-trap125 | 393472 | 40.000000000 ms | 468.88 s | Sí |

**Banco corto admitido localmente.** Pasan las cuatro coberturas, ambos
balances C2 y las tres parejas 500→250, 250→125 y Gear125→Trap125.
La diferencia máxima de traza es **138.454543 µV** frente a 5 mV;
el mayor defecto acumulado de carga es **0.216153 pC** frente a 100 pC.
Frecuencia ≤1 cent y RMS por ventana ≤1% +10 µV pasan sin retimar.

La [auditoría corta](../evidence/voice_six_short_validation01.json) reproduce
identidades, relojes, medidas y decisión sin nuevos solves. Los recibos
y el [preflight corto](../evidence/voice_six_short_preflight01.json) conservan
presupuestos, fuentes antes/después y almacenamiento estimado con 2 GiB.

## Extensión de 350 ms y alcance

El [preflight largo](../evidence/voice_six_long_preflight01.json) usa las
filas y bytes reales del nuevo banco corto, ratio 8,75 y margen de 2 GiB.
Requiere 7478873297 bytes; dispone de 6762319872.
**Rechaza por espacio**. No ejecuta SPICE; la estimación no es una cota.

Las cuatro notas largas con seis quedan **no medidas**, sin convertir
el rechazo de recursos en un fallo de circuito. Siguiente paso:
[control de export binario nativo](VOZ_NOTA_LARGA_EXPORT_BINARIO_PROTOCOLO.md),
con identidad de bits de todos los vectores antes de una nueva extensión.

La [QA](../evidence/voice_six_tests01.json) ejecuta siete regresiones nuevas
y hereda 133 por identidad de sus entradas: **140 cubiertas**, sin contar
la herencia como nuevas ejecuciones. Conserva las escuchas anteriores,
el ejecutable oficial y los intentos fallidos históricos.

No se genera audio nuevo. La admisión corta no identifica parámetros
vintage, contorno de filtro, otras notas o deadline de tiempo real. Los
rechazos largos de build08 y las capturas lineales previas siguen vigentes.
