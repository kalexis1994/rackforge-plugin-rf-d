# VCO periódico con contornos, filtro, VCA y salida J7

## Resultado admitido

Pasan dos recorridos propios de **40 a 100 ms**, desde el mismo estado
HIGH/LOW de la voz completa a 40 ms. Un solo VCO nominal de 410,8013 Hz,
sierra, panel fijo; KEY a 10 V hasta 75 ms y luego a 0 V. La cadena
mantiene sus 118 incógnitas y todas sus memorias; el VCO detallado se
aproxima por su ciclo de circuito. No se reinicia C2/C5 ni la salida.
Esto es una bifurcación de una nota existente, no un arranque autónomo
ni una emulación con todos los controles.

[Protocolo y gates](HYBRID_VOZ_PROTOCOLO.md),
[trayectorias](../evidence/hybrid_voice_native05.json),
[auditoría original](../evidence/hybrid_voice_audit01.json).

## Representación del reset y puerto cargado

El primer candidato usa el VCO admitido de 52 armónicos. J7 pasa con
error RMS de 0,05688 %, pero el BUS falla: 4,587 veces su tolerancia
previa. No se admite ese candidato aunque su salida audible medida sea
cercana. [Fallo y replay](../evidence/hybrid_voice_native03.json).

La corrección conserva frecuencia/época y usa DRIVE48/TRI54 del mismo
ciclo nativo aislado, sin entrenar con la ventana nueva. De 22212 puntos
a **901 nudos**: interpolación lineal, error máximo **49,884 µV** frente
al perfil original, gate 50 µV. Diferencia entre extremos de ciclo
1,328 µV, unida por promedio e incluida en el error. Se conserva el
nivel DC; no hay onda ideal ni normalización. Este perfil de tiempo
continuo retiene el reset y no está limitado a la banda de audio.
[Derivación e identidades](../evidence/hybrid_voice_profile01.json).

En cada etapa Radau, BUS=116 permanece libre; I_BUS y su Jacobiano
provienen de la red resistiva R6/R45 de cuatro terminales. Las ramas
antiguas de mezclador están OFF. No se duplican cargas. Las corrientes
de drivers y masa existen en el puerto; la reacción de BUS sobre la
fase y las memorias del VCO sigue aproximada. Los contornos, ladder,
recuperación, ambos VCA y condensadores de salida siguen en el solve.

## Comparación reservada, sin ajustes posteriores

481 relojes comunes por recorrido, cada 125 µs. Referencias completas
de 250 incógnitas con paso máximo full 64/32 µs. Valores máximos entre
ambos contrastes:

| Observación | Error medido | Gate previo |
|---|---:|---:|
| J7 RMS relativo | 1,06716 % | 3 % |
| J7 pico relativo | 2,60793 % | 6 % |
| J7 error medio | 0,08895 µV | 10 µV |
| J7 error máximo | 298,613 µV | RMS/pico de arriba |
| C2 error máximo | 1,910 nV | 2 mV + 0,001·abs(V) |
| C5 error máximo | 29,472 nV | 2 mV + 0,001·abs(V) |
| BUS fracción de gate | 0,024266 | ≤1 |
| R59/R60 fracción de gate | 0,006523 | ≤1 |

Los umbrales no cambiaron después del rechazo. El reset más preciso
reduce el error del BUS, pero aumenta el error de J7 respecto del perfil
limitado a 52 armónicos. Se reportan ambos: acertar en J7 solamente no
valida una tensión interna ni la banda de una representación distinta.
No se reclama igualdad puntual en todas las 118 incógnitas o igualdad
continua a partir de esta grilla de 8 kHz.

Refinamiento entre recorridos: RMS J7 5,926e-8 relativo y pico 2,871e-7,
error máximo 3,312 nV. Los techos de 64/32 µs casi no separan las
trayectorias: la adaptación produce 5279/5280 pasos. Este contraste de
techos no demuestra por sí solo convergencia con un estimador más fino;
el contraste con la voz completa es el gate externo de esta admisión.

## Ecuaciones originales, memoria y costo

24 pares seleccionados, **5712 filas originales**, cursor Amount
explícito y estrella resistiva VCO original. La auditoría Python deriva
corrientes y diferencias finitas independientes: residual máximo
0,71901 pA y corrección 0,32505 nV, dentro de 20 pA/2 nV. Evalúa
candidatos nativos; no construye otra trayectoria independiente.

Solver nativo: residual ≤1 pA/corrección ≤2 nV. Pasos mínimos full
1 µs; máximos estimadores 0,950788 del gate. Cuatro replays exactos por
recorrido, cinco rechazos inválidos atómicos por recorrido y **cero
asignaciones heap durante la integración medida**. Se conservan todas
las cargas de cadena de la semilla y de los pasos propios.

28,553/28,468 s de integración medida para 60 ms simulados en este
equipo. El VCO ya no requiere el MNA completo de 134 incógnitas; la
cadena detallada todavía cuesta mucho para un callback de audio.
No se declara tiempo real, deadline, antialias de producción ni plugin
tocable. El muestreo directo de este perfil no está admitido a 48 kHz.

## Archivos y siguiente bloque

Un solo `tmp/lab-current`, vacío al terminar; ejecutable y semilla
retirados. Grillas compactas y raíces seleccionadas en recibos comprimidos
con restitución SHA256. Sin nueva biblioteca, Cargo, WAV, cache,
carpetas de muestras o input privado de sonido.

Se conservan un fallo de lector gzip, tres rechazos de compilación del
arnés y el rechazo eléctrico del BUS con fuentes/replays sin cambios.
Las referencias originales y los 8769 inputs anteriores permanecen.

Siguiente trabajo: reducir la dinámica de contornos/filtro/VCA sobre
esta unión funcional, midiendo cargas, J7 y costo. Después ampliar
arranque/ataque, CV y escenas. El parecido con un Moog físico sigue sin
verificación; la admisión actual es respecto del circuito documental.
