# VCO1: subpasos verificados y precisión pendiente

2026-10-08. [Protocolo previo](VCO1_SUBPASOS_PROTOCOLO.md), CA3046 nominal,
25°C, panel SW6 3/10, CV/rieles/mixer impuestos. No se admite nota completa.

## Stamp y solves locales

`vco1_substep` conserva el stamp DC anterior y añade ΔQ/dt y C/dt de las
mismas leyes, seis C de placa y memorias de ambos 741. No duplica corrientes
DC o carga del panel. Para dt>=125ns delega exactamente al código anterior.
El piso30.517578125ps es numérico, no físico. El Newton conserva su algoritmo,
64 iteraciones/24 halvings y gates originales; puede rechazar una entrada.

La [referencia02](../evidence/voice_vco1_substep_reference02.json)
reconstruye 48 stamps: dos C4, historia de rampa/reset del export de laboratorio,
y doce pasos125ns/2..125ns/4096. Incidencias/pivotes Decimal100, ramas binary64.
28 solves independientes pasan; 20 se rechazan con replay de cada tupla.
El [primer intento](../evidence/voice_vco1_substep_reference01.json)
se detuvo en su primer rechazo y sus fuentes originales quedan archivadas.
El segundo conserva ese rechazo y completa la cobertura sin llamarlo aprobado.
Los ceros de raíz en fixtures son placeholders de rechazo, nunca raíces.

La [producción](../evidence/voice_vco1_substep_native01.json) verifica todos
los residuos y las 861.888 entradas del Jacobiano, incluidas posiciones cero:
error máximo5.68434e-14 por unidad de fila y5.11591e-13 por unidad de Jacobiano.
Las28 raíces disponibles coinciden a7.01012e-12V /2.21871e-15A.
Los40 casos anteriores delegan byte por byte en arrays/masa/memoria.
100 stamps en el piso y128 pasos62.5ns sin heap. No se admite todo el dominio
como un banco de raíces, refinamiento temporal o trayectoria autónoma completa.

## Control de precisión y campaña rechazada

`vco1_adaptive` compara h con dos pasos h/2, manteniendo memoria entrante
fija durante cada retry. Exige2µV /2nA en las134 incógnitas; acepta midpoint
y endpoint juntos, o devuelve error. Reloj entero, presupuesto16 intentos,
dt real por intervalo. No usa umbrales o forma de onda ideal.

[Tests](../evidence/voice_vco1_adaptive_native01.json):256 medios pasos,
repetición pura, límites, rechazo real en el piso y retry idéntico;
128 candidatos sin heap. Su [campaña](../evidence/voice_vco1_adaptive_cycles01.json)
se rechaza a1.184056640625ms:7520 pasos aceptados, todos preservados,
con export original y replay de mismo comando/fuentes. No se midieron
períodos/refinamiento de escenas incompletas.

## Causa local contrastada

[Instrumentación privada y replay](../evidence/voice_vco1_substep_rounding01.json)
del mismo rechazo: máxima KCL en NEG4_REF=-3.26527533e-13A, fuera del
límite1e-13A. Newton pide+1.66080245e-16V, sólo0.374ULP del estado:
al sumar, el nodo conserva exactamente el mismo float. Para C=120nF y
h=61.03515625ps, un ULP implica8.73115e-13A. La corrección satisface su
gate y la KCL no; aceptar sólo la corrección sería incorrecto.

Este dato identifica el estancamiento local por representación; no demuestra
la causa de todos los rechazos anteriores. No se relajan los gates ni se
promueve el diagnóstico a audio o RT. Derivar coordenadas de incremento y
memoria capacitiva explícita; comprobar las mismas ecuaciones con referencia
independiente de mayor precisión antes de otra campaña completa.

[QA](../evidence/voice_vco1_substep_tests02.json):229 controles, seis nuevos
(tres subpaso+tres controlador) y223 heredados por identidad. Cero SPICE/audio
nuevo. Las diez raíces de arranque propias siguen admitidas; el banco de
ciclos completos, calibración, carga activa, deadlines y fidelidad física no.
