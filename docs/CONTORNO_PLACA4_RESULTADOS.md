# Contorno de volumen: circuito cargado y notas completas

Fecha: 2026-10-06. [Protocolo previo](CONTORNO_PLACA4_PROTOCOLO.md),
[banco de diez escenas](../evidence/loudness_board4_bank02.json.gz),
[replay independiente de las mediciones](../evidence/loudness_board4_validation.json),
[escucha](../evidence/loudness_board4_listening.json) y
[verificación final](../evidence/loudness_board4_tests.json).

## Alcance alcanzado

La simulación une diez BJT de contorno/gatillo con los 25 de placa 4:
ladder, recuperación, retorno, ambos VCA y salida. R59=68 kohm carga
el seguidor de contorno con la corriente de base de Q18. Se retira la
fuente ideal de contorno; C2, Q25/Q15 y el seguidor producen su señal
desde la misma solución. No hay tabla ADSR, reloj de fase, reset digital
ni imposición del voltaje del capacitor o del estado del biestable.

Cada escena completa **350 ms**, con teclado ON desde 10 ms y OFF
desde 200 ms; ambas transiciones impuestas de 10 microsegundos.
Son 35 BJT con carga Gummel–Poon condicionada y 18 capacitores discretos.
Los diodos de contorno mantienen sus hipótesis de conducción anteriores,
con almacenamiento sin identificar y omitido. No se sustituyen por
tarjetas de fabricante ni se identifica una unidad vintage.

La fuente de audio sigue siendo **senoide impuesta 440 Hz, 0.1 V pico,
resistencia 1 kohm**. Q21 sigue con base a 2 V; suministro del contorno
9.3 V impuesto; carga del contorno de filtro sobre gatillo/reset omitida.
Esta referencia cierra el contorno cargado bajo esas fronteras.
La unión VCO/voz sigue siendo [nominal y limitada](VOZ_ACOPLADA_RESULTADOS.md).

## Convergencia numérica finita

| Contraste | Máxima diferencia de C2/contorno (microvolt) | Máxima diferencia de salida (microvolt) | Máxima diferencia de RMS por ventana (microvolt) |
| --- | ---: | ---: | ---: |
| Gear2, máximo 8 → 4 microsegundos | 0.015602 | 99.710236 | 26.790989 |
| Gear2, 4 → 2 microsegundos | 0.122530 | 60.184384 | 6.337970 |
| Gear2 → Trap2, 2 microsegundos | 0.254463 | 17.911427 | 1.360866 |

Pasan 5 mV en grilla común de 20 microsegundos, sin realinear eventos,
y 1% + 10 microvolt en RMS de reposo/ataque/held/release. No es una
cota continua ni una prueba de estabilidad global del biestable.
El mayor defecto de carga acumulado del contorno es **8.650 pC**,
en ataque 1000 ohm; el de salida **17.043 pC**, en nominal 8 microsegundos.
Ambos pasan 100 pC, incluyendo eventos y corriente de CR4 cuando corresponde.

Las diez mediciones y los tres contrastes se reconstruyen exactamente
desde los exports privados, con cero nuevos solves. La revisión de fuentes
preserva una excepción histórica de checkout CRLF para el grafo de
contorno: sólo el par exacto de hashes LF/CRLF está permitido. No se
normalizan todos los archivos ni se ignoran cambios de bytes.

## Controles y observaciones reservadas

| Escena | Contorno medio en held (V) | RMS salida en ataque (V) | RMS salida en release (V) |
| --- | ---: | ---: | ---: |
| Nominal: ataque 10 kohm / decay 100 kohm | 5.402409 | 0.384606 | 0.745202 |
| Ataque 1000 ohm | 5.060905 | 0.739960 | 0.729376 |
| Decay 10000 ohm | 4.718194 | 0.385034 | 0.244084 |
| Sustain inferior 1000 ohm | 5.371589 | 0.384437 | 0.743855 |
| Decay final OFF | 5.397060 | 0.360929 | 0.039999 |
| Resistor a Q12: 4700 ohm | 5.402245 | 0.383474 | 0.745193 |
| Pullup de reset: 1000 ohm | 5.402862 | 0.388080 | 0.745222 |

Ventanas: ataque 20–80 ms, held 120–190 ms, release 230–340 ms.
El nominal llega a 5.517346 V de contorno y su reposo está a -0.290032 V;
salida en reposo 1.356 microvolt RMS. El contorno nominal sigue alto
al final de esta nota corta: **no ha completado el decay natural**.
No se confunde la ventana held con sustain ya asentado. El cambio de
SUSTAIN afecta una dinámica que aún está descendiendo, no una lectura
estática del cursor. La salida puede variar por no linealidad de ambos
VCA; no se exige monotonía de RMS para todo el intervalo.

## Escucha de toda la nota medida

Tres notas: nominal, ataque 1000 ohm y decay final OFF. Cada una usa los
350 ms completos de salida, con interpolación de reloj no uniforme,
FIR simétrico a 21.6 kHz, DC global retirada, PCM16 mono/48 kHz,
escala fija 8 V/full scale y fades de 10 ms. El recibo fija taps, ventana,
padding, delay y hashes; ninguna escena se normaliza por pico.

Montaje local: `artifacts/loudness-board4/rf-d-contorno-nominal-ataque-rapido-decay-off.wav`,
1.35 s con dos pausas de 0.15 s. **No se repite un ciclo**: las variaciones
temporales provienen del contorno resuelto. La señal de entrada es una
senoide del laboratorio. Fades y duración no prueban release terminado.

## Rechazos conservados y siguiente prioridad

El [primer banco](../evidence/loudness_board4_bank01.json.gz) completó
las diez simulaciones, pero el adaptador omitía guardar la salida de
contorno necesaria para medir; sus diez rechazos permanecen. El segundo
banco añade ese vector y repite las mismas escenas y gates. El
[primer auditor](../evidence/loudness_board4_audit_rejected.json) rechazó
el checkout CRLF histórico; la reparación reconstruye exclusivamente
los bytes congelados y conserva ambos hashes.

Los diagnósticos de voz también conservan su rechazo:

- [Tolerancia de corriente](../evidence/voice_current_tolerance_screen01.json.gz):
  1e-12/1e-11/1e-10 A detienen base Q21=0 V a 2.277/9.109/34.158 ms.
  Ningún candidato fue seleccionado ni aplicado al modelo nominal.
- [Puertos de carga JFET](../evidence/voice_jfet_charge_ports01.json.gz):
  el contraste de terminales pasa (máxima diferencia de corriente 0.122 nA),
  pero las cuatro escenas de voz rechazan. La equivalencia local no resuelve
  la convergencia de la red. No se aplica esa representación a la referencia.

Próximo: integrar este contorno con VCO bajo carga y resolver las tres
escenas históricas rechazadas; cerrar contorno de filtro, alimentación
común y control de Q21. Ruta portable, eventos más largos, autooscilación,
VCO2/3, ruido, fidelidad física y deadlines siguen abiertos. Los certificados
formales anteriores conservan su alcance; este banco no los reemplaza.
