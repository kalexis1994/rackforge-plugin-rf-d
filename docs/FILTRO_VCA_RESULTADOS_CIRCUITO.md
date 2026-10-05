# Ladder y dos VCA: circuito funcional con entrada eléctrica

Fecha: 2026-10-05. [Protocolo](VOZ_CIRCUITO_PROTOCOLO.md),
[grafo independiente](../evidence/voice_board4_graph.json),
[banco completo](../evidence/filter_vca_circuit_bank01.json.gz) y
[replay de 19 exports](../evidence/filter_vca_circuit_validation.json).

## Alcance alcanzado

Placa 4 resuelve simultáneamente 25 BJT: Q26/Q28, ladder con cuatro
capacitores 68 nF, recuperación Q5–Q8, retorno C10/R14/R73, ambos
multiplicadores, conversión Q1/Q12/Q17 y salida C2/R75/R77. Incluye
carga de entrada y de ambos conectores. No se impone corriente de cola,
onda de filtro ni ganancia VCA. Tarjetas BJT comunes y diodos exploratorios
siguen condicionados, con ESR y parámetros vintage sin identificar.

R61=200 ohm es el perfil principal del esquema. Su alternativa 200 kohm
también se mide; cambia la salida y no resuelve la discrepancia documental.
Contorno, base Q21 y amount de filtro son fronteras de voltaje fijas.
La impedancia de auriculares es una terminación impuesta, no su amplificador.

## Convergencia finita

19 escenas de 80 ms; observación después de 40 ms. Fuente nominal:
senoide 440 Hz, 0.1 V pico, resistencia 1 kohm. Controles, trims y
terminaciones se fijaron en el protocolo. Coste total de solves: 65.28 s
offline en este equipo; no es un perfil de audio en tiempo real.

| Comparación | Máxima diferencia de extremos BUS/recuperación/salida | Diferencia RMS de salida |
| --- | ---: | ---: |
| Gear2, paso máximo 2 → 1 microsegundo | 6.2313 microvolt | 0.4947 microvolt |
| Gear2 → Trap2, paso máximo 1 microsegundo | 1.1322 microvolt | 0.1449 microvolt |

Pasan 5 mV y 1% + 10 microvolt predefinidos. El mayor defecto absoluto
integrado de C2 frente a las dos ramas de salida es 1.302e-14 C;
límite 1e-10 C. No es una cota continua ni un gate de fidelidad física.
Las 19 trazas, relojes, netlists y logs privados se verifican por SHA;
sus mediciones se reconstruyen exactamente con cero nuevos solves.
El auditor recupera también del commit limpio el generador VCO auxiliar
que el recibo inicial no enumeraba directamente; los recibos no se reescriben.

## Controles y cargas reservados

| Escena | RMS AC de salida principal (V) |
| --- | ---: |
| Nominal, contorno 2 V / Q21 base 2 V | 0.3049718 |
| Cutoff eléctrico 0.2 | 0.0076326 |
| Cutoff eléctrico 0.8 | 0.3399562 |
| Contorno 0 V | 0.000001260 |
| Contorno 1 V | 0.1237462 |
| Contorno 4 V | 0.6537666 |
| Base Q21 0 V | 0.000001102 |
| EMPHASIS 5000 ohm | 0.2037630 |
| EMPHASIS 0 ohm | 0.1570578 |
| Carga principal 10 kohm | 0.2655820 |
| Perfil R61 200 kohm | 0.1103172 |

Mute del primer/segundo control: -107.68/-108.84 dB respecto de la escena
nominal, para estas tarjetas/fronteras. Q28 pasa de 8.046 a 479.882 microamp
entre cutoff 0.2/0.8. No se transforma esa fracción eléctrica en frecuencia
de corte o giro físico por un ajuste arbitrario. El cambio de EMPHASIS
no obliga a monotonía de amplitud en una frecuencia fija.

Las entradas reservadas de 1 y 10 V pico dan 0.589876 y 0.310468 V RMS:
la ruta no es lineal a esos niveles. No se identifica por ello el clipping
del instrumento. A 1 mV pico se observaron cuatro frecuencias, 110/440/
1760/7040 Hz; la salida cae desde 3.543 mV hasta 6.709 microvolt RMS.
Cuatro puntos no describen toda la respuesta ni certifican autooscilación.

## Escucha de sierra medida a través del panel y placa 4

[Recibo completo](../evidence/filter_vca_circuit_listening.json).
La frontera es la sierra 9B medida del banco VCO anterior, 410.80177 Hz,
52 armónicos y DC retenida; se aplica como voltaje seleccionado de panel.
R6=25 kohm al centro y R45=33 kohm resuelven su carga con el filtro.
Esto **no vuelve a resolver el VCO bajo esa carga**.

| Apertura eléctrica | RMS de salida (V) | Diferencia máxima entre dos ciclos finales (mV) |
| --- | ---: | ---: |
| 0.2 | 0.0023050 | 0.02220 |
| 0.5 | 0.0785014 | 0.02459 |
| 0.8 | 0.0964630 | 0.03469 |

Las tres escenas completan 80 ms con paso máximo 1 microsegundo. Pasan
el límite previo de repetición de ciclo de 5 mV. El adaptador repite el
último ciclo durante 0.75 s por apertura, elimina DC, limita a 0.45 Fs,
usa 48 kHz PCM16 mono, escala fija 8 V/full scale y fades 10 ms.
No normaliza cada apertura ni simula el circuito durante todo el WAV.
Archivos locales: `artifacts/filter-vca-circuit/`; montaje cerrado→medio→abierto.

## Unión con VCO pendiente y fallos preservados

La netlist que resuelve VCO1/mixer/placa 4 juntos se detiene durante su
primer reset E402. Cinco intentos conservan deck/log/export parcial:
[inicial](../evidence/voice_circuit_rejected_initial.json),
[más iteraciones, Trap y C4 alternativo](../evidence/voice_circuit_reset_rejections.json)
y [bypass deshabilitado](../evidence/voice_circuit_rejected_bypass_off.json).
No se admiten esas trayectorias parciales como referencia de voz.
El banco independiente aceptado no demuestra que esa unión funcione.

Próximo bloque: aislar la causa del reset bajo carga, completar la ruta
portable y sustituir las fronteras de contorno/Q21 por sus redes de control.
Faltan VCO2/3, ruido, eventos, barridos de resonancia/autooscilación,
parámetros físicos y deadlines. No se declara voz completa ni fidelidad vintage.

La [verificación final](../evidence/filter_vca_circuit_tests.json) registra
pruebas estructurales, fronteras inválidas y rechazo de repetir una señal
no estacionaria, además de la identidad de las fuentes verificadas.
