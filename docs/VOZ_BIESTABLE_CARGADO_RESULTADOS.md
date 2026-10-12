# Q25/Q15 cargados en la voz nativa

2026-10-12, Model D CA3046. [Contrato](VOZ_BIESTABLE_CARGADO_PROTOCOLO.md),
[semilla KEY](VOZ_BIESTABLE_SEMILLA_PROTOCOLO.md),
[predictor S](VOZ_BIESTABLE_CONTACTO_PROTOCOLO.md),
[auditor](VOZ_BIESTABLE_AUDITOR_PROTOCOLO.md),
[refinamiento](VOZ_BIESTABLE_REFINAMIENTO_PROTOCOLO.md).
[Inputs](../evidence/voice_latch_charge_inputs04.json),
[nativo](../evidence/voice_latch_charge_native04.json),
[oráculo](../evidence/voice_latch_charge_reference05.json),
[QA](../evidence/voice_latch_charge_tests01.json).

## Cierre eléctrico

229 incógnitas/dos etapas Radau: VCO1→BUS→ladder→ambos VCAs→J7 y la
placa2 completa del contorno de volumen/gatillo. Q25/Q15 y R38/R39/R56
sustituyen las fuentes de SET_BASE, RESET_COLLECTOR y RESET_BASE.
Q16/Q17 reciben ahora su corriente desde el colector real Q25; CR6/CR8
cargan la base real Q15. R59 y todos sus retornos se ensamblan una vez.
Alimentación9.3 V ideal y contorno de filtro/Q26 omitido permanecen explícitos.

Se heredan450 coordenadas225 por bits, con C2/C7 y la carga orientada
de C4 intactas. Al liberar SET_BASE, C4 necesita dos terminales internos:
sus cuatro coeficientes de masa se conservan, incluido el retorno a Q25.
Los cuatro bias nuevos y sus cargas BE/BC son condiciones declaradas,
no un equilibrio completo ni una preparación medida del instrumento.

Las corrientes Ebers–Moll de Q25/Q15 y sus cargas de depleción/transporte
usan la misma temperatura/Is/β. TF1 ns/TR3 ns y los parámetros de depleción
son hipótesis de laboratorio. La expansión high/low y los incrementos
estables se contrastan contra Q y derivadas Decimal100. Los otros ocho
BJT y diodos de placa2 siguen sin almacenamiento intrínseco. Esta
admisión no se hereda desde la campaña SPICE Gummel–Poon anterior.

## Ventana local de conmutación

Cuatro perfiles de10 µs desde5.322 ms, final decay ON/OFF y pasos
15.625/7.8125 ns. Cinco tramos de2 µs; KEY=[0,10,10,0,0] V,
S cerrado sólo en el tramo2. Ningún estado de Q25/Q15 está impuesto.
C7 conserva los≈3.858 mV entrantes y llega≈7.714 mV: sólo se observa
el inicio del RC de KEY, no un Note On completo por teclado.

Valores finales ON a7.8125 ns, en V:

| Tramo | RESET_DRIVER | Q25 base | Q25 colector | Q15 base | Q15 colector | C4 orientado | C2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0: reposo | .0295256744 | −.0549487697 | 8.29410518 | .691699777 | .0100166389 | .149410930 | 3.20052574 |
| 1: KEY alto | .0295254213 | −.0543024550 | 8.29410519 | .691700094 | .0100169806 | .148118668 | 3.20052104 |
| 2: S cerrado | 7.10728274 | .705291935 | .0142555488 | .253382224 | 5.00262878 | .271656911 | 3.20063989 |
| 3: S abierto | .0295486768 | −.113724288 | 8.29410451 | .691670952 | .0099855511 | .266929204 | 3.20064613 |
| 4: reposo | .0295481952 | −.112493547 | 8.29410452 | .691671556 | .0099862023 | .264468395 | 3.20064142 |

S cerrado activa Q25 y reduce su colector de≈8.294 V a≈14.256 mV.
Al abrir S, R36/CR8 vuelve a elevar la base Q15 y la red regresa al estado
de reposo; no se cambia RESET_BASE desde una fuente. La respuesta de
Q15 colector todavía evoluciona dentro del pulso de2 µs. No se afirma
un tiempo ADSR, retención completa, ciclo de nota o convergencia estacionaria.
En OFF, C2 termina3.195003106 V y J7≈2.568748828 mV; en ON,
C2=3.200641424 V y J7≈2.575214375 mV. Esta ventana continúa una voz
precargada; no representa un ataque completo desde silencio.

## Evidencia y rechazos

3840 pasos originales,5760 repetidos,40 restores completos de tramo,
16 corrupciones rechazadas. Checkpoint3712 bytes: reloj/paso/tramo,
KEY, versión del dispositivo, flags de contactos y458 componentes.
Cada cambio de fuente conserva todas las componentes por bits.
La repetición completa a15.625 ns es idéntica a la campaña03; los
prefijos anteriores a ambos fallos Newton también permanecen idénticos.

80 candidatos,18320 ecuaciones independientes y120 valores de corriente
en40 endpoints. Máximo residual/gate=2.11820083433·10⁻⁵;
corrección/gate=2.01760520531·10⁻⁷, corriente comparada≤1.735·10⁻¹⁸ A.
Balances C2/C18/C27/C7/C4 y terminales cargados Q25/Q15, por tramo y
total: error máximo9.217·10⁻²² C, gate1 pA×duración.
Cuadratura nativa Radau; no integración independiente de cada paso.

La malla31.25/15.625 ns convergía pero se rechazó por refinamiento:
C4_LEFT difería≈14.30 µV al cerrar S. Se conservó el rechazo y replay
antes de reducir ambos pasos, sin cambiar parámetros/gates.
La nueva pareja tiene error máximo1.552638551 µV en SET_BASE al final
del tramo3, ratio.776319276 respecto de2 µV. Comparación de todas las
coordenadas en semilla y cinco finales; no una cota para todo instante.

Otros fallos conservados: KEY fuera del dominio con semilla anterior;
64 rondas agotadas al cerrar S; fila FAST_K vacía del adaptador ON;
diagnóstico que olvidaba el BUS vacío de la cadena OFF; alias de contacto
omitida del auditor. Predictores sólo en nodos sin almacenamiento,
adaptadores corregidos sobre los mismos datos y ninguna tolerancia ampliada.

Campaña final157.5651245 s, oráculo14.3459792 s. Biblioteca congelada;
248 tests heredados por identidad, sin reejecutarlos. Sin audio nuevo,
compilación de biblioteca, SPICE, hardware, identificación física o RT.

## Siguiente bloque funcional

Continuar esta red cerrada hacia una trayectoria de contorno de volumen
que cubra ataque, sustain y liberación con contactos propios y balances,
con un controlador temporal para el sistema229. Mantener separados el
cierre topológico local, las cargas aún omitidas y la fidelidad física.
El contorno de filtro, otros VCO, host y deadlines permanecen pendientes.
