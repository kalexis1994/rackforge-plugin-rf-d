# Voz acoplada: referencia nominal y escucha condicionada

Fecha: 2026-10-05. [Protocolo congelado](VOZ_KLU_PROTOCOLO.md),
[banco de once escenas](../evidence/voice_circuit_klu_bank01.json.gz),
[auditoría por alcance](../evidence/voice_circuit_scoped_validation.json),
[adaptación de escucha](../evidence/voice_circuit_listening.json) y
[pruebas finales](../evidence/voice_circuit_tests.json).

## Circuito y alcance

La escena nominal resuelve VCO1 CA3046, formadores, panel R6/R45,
C27/Q29/Q30, ladder, recuperación, realimentación, dos VCA y salida
simultáneamente. No se impone una onda, frecuencia, corriente de cola,
ganancia VCA ni buffer de interconexión. Se conservan los componentes,
capacitores ideales, tarjetas de dispositivo y tolerancias anteriores.
El cambio admitido es seleccionar KLU como solver lineal en ngspice 46.
No se añade resistencia serie numérica ni una ESR supuesta.

El [grafo de placa 4](../evidence/voice_board4_graph.json) mantiene su
transcripción independiente de SVC-204D Fig. 9-11, PDF p. 13 y tablas
7–8, pp. 30–31; panel Fig. 9-17, p. 19. El perfil documental y sus
incertidumbres siguen en [el resultado de filtro/VCA](FILTRO_VCA_RESULTADOS_CIRCUITO.md).
R61=200 ohm es el perfil nominal; 200 kohm sigue como conflicto documental.
Los BJT genéricos, E402 condicionado y diodos exploratorios no identifican
una unidad vintage. Rieles ideales y cargas de salida impuestas se declaran
en el protocolo. Sólo VCO1 está poblado.

Controles nominales: cutoff eléctrico 0.5, range 0.5, scale 250 ohm,
EMPHASIS 50000 ohm, retorno inferior de regeneración 500 ohm, contorno
2 V, base Q21 2 V y amount de filtro 0 V. Trims VCO: R11=521.3126579373712
ohm y R8=0.2613404652606161; CV de laboratorio -2.1 V. Estos valores
se mantienen entre escenas; no son una calibración por forma de onda.

## Tres contrastes nominales aceptados

Cada escena pide 40 ms y observa desde 20 ms. Los gates fijados antes
de medir son 1 cent, 5 mV en extremos de BUS/recuperación/salida,
1% + 10 microvolt en RMS de salida y 1e-10 C en balance integrado de C2.

| Contraste | Frecuencia (cent) | Máxima diferencia de extremos (microvolt) | Diferencia RMS de salida (microvolt) |
| --- | ---: | ---: | ---: |
| Gear2, paso máximo 500 → 250 ns | 0.000003321 | 0.735923 | 0.063654 |
| Gear2, 250 → 125 ns | 0.000004192 | 0.201732 | 0.018208 |
| Gear2 → Trap2, 125 ns | 0.000060813 | 0.037773 | 0.001019 |

El auditor reconstruye exactamente las mediciones de ocho exports completos
y verifica identidad y reloj de tres exports parciales, sin nuevos solves.
La aceptación nominal **no cambia el rechazo del banco completo** ni
demuestra error continuo, fidelidad física o cumplimiento de tiempo real.
Los logs confirman KLU; el ejecutable y fuentes están fijados por SHA.

## Banco completo rechazado

| Escena | Estado | Último reloj cuando rechaza |
| --- | --- | ---: |
| Nominal Gear2: 500, 250 y 125 ns | Completa | — |
| Nominal Trap2: 125 ns | Completa | — |
| Cutoff eléctrico 0.8 | Completa | — |
| Triángulo | Completa | — |
| Pulso estrecho | Completa | — |
| Carga principal 10 kohm | Completa | — |
| Cutoff eléctrico 0.2 | Rechaza | 31.880620 ms |
| Contorno 0 V | Rechaza | 11.386113 ms |
| Base Q21 0 V | Rechaza | 1.754009 ns |

Las trayectorias parciales no se admiten como referencia sonora. El fallo
numérico no prueba que los mute físicos fallen. KLU permite este alcance
nominal, pero no resuelve la convergencia en todo el dominio de controles.

## Escucha de la señal realmente acoplada

| Forma | Frecuencia medida (Hz) | Diferencia entre dos ciclos finales (mV) |
| --- | ---: | ---: |
| Sierra | 439.142091 | 1.012859 |
| Triángulo | 439.148856 | 0.897266 |
| Pulso estrecho | 439.148837 | 1.651590 |

Las tres pasan el límite previo de repetición de 5 mV. Se toma la salida
principal del circuito acoplado; el VCO responde eléctricamente a esa carga.
El adaptador repite el último ciclo medido durante 0.75 s por forma,
reconstruye Fourier desde la señal lineal por tramos en reloj no uniforme,
limita banda a 0.45 Fs y elimina DC. Usa 48 kHz PCM16 mono, escala fija
8 V/full scale y fades de 10 ms. No normaliza por pico.

El montaje local `artifacts/voice-circuit/rf-d-voz-sierra-triangulo-pulso.wav`
dura 2.55 s, incluidas dos pausas de 0.15 s. **El circuito se resolvió
durante 40 ms por escena; no durante toda la duración del WAV.** La
repetición no prueba estacionariedad infinita, respuesta a eventos ni
envolventes. Los archivos privados y sus hashes constan en el recibo.

## Diagnósticos conservados y cambios no admitidos

1. [Aislamiento del reset](RESET_VCO_AISLAMIENTO_PROTOCOLO.md) y
   [seis escenas](../evidence/voice_reset_isolation01.json.gz): cargas
   resistiva y RC del VCO completan; placa 4 eléctricamente desacoplada
   en el mismo solve también falla. Eliminar sus capacitores completa
   el diagnóstico, pero deja de representar esa voz.
2. [Pruebas de orden y capacitores](../evidence/voice_reset_numerical01.json.gz):
   BE y newtrunc no resuelven la unión. Eliminar C9, C24 o C4 permite
   escenas desacopladas; no identifica por sí solo un componente erróneo.
3. [Comparación Sparse/KLU](../evidence/voice_reset_klu01.json.gz):
   KLU completa la unión nominal de 10 ms sin modificar ramas físicas.
   La escena desacoplada todavía rechaza. No se atribuye una causa única.
4. [Coordenadas exactas de capacitor](CAPACITORES_COORDENADAS_PROTOCOLO.md)
   y [resultados](../evidence/voice_capacitor_coordinates01.json.gz):
   el puerto lineal reproduce corriente con diferencia máxima 5.031e-12 A,
   pero las cuatro escenas no lineales rechazan. Equivalencia eléctrica
   no implica estabilidad numérica. No se aplica al generador de voz.
5. [Resistencia serie aproximada](CAPACITORES_APROXIMACION_PROTOCOLO.md)
   y [resultados](../evidence/voice_capacitor_regularization01.json.gz):
   0.001 ohm permite tres escenas cortas, pero base Q21 0 V rechaza.
   Esa resistencia no es una transformación exacta ni ESR identificada;
   no se admite ni se ejecuta la serie posterior de aproximaciones.

El [manifiesto de fuentes numéricas](../evidence/voice_reset_source_manifest.json)
fija las fuentes primarias de ngspice usadas para interpretar estos ensayos.
Todos los intentos preservan decks, logs, exports y fuentes antes/después;
la referencia de producción conserva los capacitores ideales originales.

## Siguiente prioridad

Resolver las tres escenas rechazadas con criterios eléctricos y numéricos
separados; después sustituir contorno y base Q21 impuestos por sus redes
documentadas y medir eventos. Implementación portable, VCO2/3, ruido,
resonancia/autooscilación, parámetros físicos y deadlines siguen abiertos.
Esta escucha es un prototipo nominal de laboratorio, no un plugin de voz
completa ni una declaración de fidelidad vintage.
