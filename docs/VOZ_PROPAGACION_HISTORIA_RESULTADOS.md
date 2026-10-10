# Propagación de memoria por ventanas de calendario fijo

2026-10-10. Model D clásico CA3046, misma escena y biblioteca de los
cuatro ciclos corregidos. [Protocolo previo](VOZ_PROPAGACION_HISTORIA_PROTOCOLO.md),
[calendarios](../evidence/voice_history_propagation_inputs01.json),
[campaña nativa](../evidence/voice_history_propagation_native01.json),
[contraste independiente](../evidence/voice_history_propagation_reference01.json)
y [QA](../evidence/voice_history_propagation_tests01.json).

## Implementación y cobertura

El adaptador de laboratorio comparte una eliminación para nueve RHS.
Conserva el pivotado escalado, umbral singular 1e-12 y tratamiento de
ceros exactos del solver escalar admitido. Las 48 matrices del banco
anterior producen 172800 coordenadas idénticas por bits a nueve llamadas
escalares; el auditor también compara estos bytes con el output anterior.
No se cambia ni recompila la biblioteca física.

Se compone `J_n S_n = -H_x,n U_n`, `U_(n+1) = S_n[etapa final]`.
Nueve direcciones iniciales: 43, 5, 12, 139, 199, 194, 157, 117 y 98.
Los estados, cargas de juntura y memorias internas de corriente mantienen
las unidades y HIGH/LOW de la admisión anterior. La respuesta es respecto
de coordenadas absolutas; no deriva cada redondeo del codec.

Doce ventanas de 64 medios pasos reales, 768 pasos/6912 direcciones y
2764800 coordenadas de etapa. Cada trayectoria perturbada sigue el calendario
publicado desde su propio final. 27648 solves nuevos: nueve direcciones,
dos tamaños centrales y dos signos. Los 24 primeros pares de incrementos y
candidatos reproducen el banco seleccionado por bits. Los 768 finales
reproducen por bits siete tensiones de sus trazas históricas; continuidad
HIGH/LOW y relojes enteros completos comprobados. No se reproducen todos
los estados de todo un ciclo ni sus decisiones adaptativas.

## Resultados

Perfiles 0/1: memoria 0 a 125/62.5 ns máximos; perfiles 2/3: memoria 1
a esos mismos máximos. La tabla expresa duración real de ventana, no límite
nominal del motor. Cada ratio debe ser ≤1.

| Ventana | Perfil | Ubicación | Duración s | Peor ratio independiente | Peor ratio FD propio |
|---|---|---|---:|---:|---:|
| 0 | 0 | first | 5.96875e-06 | 4.53340682e-05 | 0.00106412961 |
| 1 | 0 | reset1 | 1.953125e-08 | 0.00172233494 | 2.91134779e-05 |
| 2 | 0 | reset2 | 1.953125e-08 | 0.00147501467 | 3.11035216e-05 |
| 3 | 1 | first | 3.34375e-06 | 2.44484204e-05 | 0.00106412961 |
| 4 | 1 | reset1 | 1.953125e-08 | 0.00203350566 | 2.90006836e-05 |
| 5 | 1 | reset2 | 1.953125e-08 | 0.00155937233 | 2.93341554e-05 |
| 6 | 2 | first | 5.96875e-06 | 2.13769563e-05 | 0.00106408659 |
| 7 | 2 | reset1 | 1.953125e-08 | 0.00163534461 | 2.92561514e-05 |
| 8 | 2 | reset2 | 1.953125e-08 | 0.0019562077 | 2.93062639e-05 |
| 9 | 3 | first | 3.34375e-06 | 4.0211877e-05 | 0.00106408659 |
| 10 | 3 | reset1 | 1.953125e-08 | 0.00204003176 | 2.92528032e-05 |
| 11 | 3 | reset2 | 1.953125e-08 | 0.00201511595 | 2.92388239e-05 |

Peor ratio independiente 0.00204003176; peor ratio de historias propias
0.00106412961. Las 768 respuestas del control algebraico 98 son exactamente
cero, tanto nativas como independientes. El gate de cambio por coordenada
sigue siendo 1e-8 V / 1e-11 A + 1e-4 relativo. No se amplía ningún gate.

El oráculo reconstruye masa en la historia y Jacobianos de ambas etapas
para cada uno de los 768 pasos, propagando su propia matriz de respuesta.
VCO Decimal100 y cadena con gradiente FD/binary64 independiente heredado.
Se evalúan candidatos nativos; no se buscan raíces no lineales independientes.
El contraste FD resuelve historias no lineales nativas distintas; su calendario
es fijo y no incluye la respuesta del selector adaptativo.

Se fija un único epsilon por dirección y ventana usando el máximo cambio
lineal previsto en sus 128 etapas: techo 10 µV/10 nA, base de entrada
10 µV/0.1 nA. El codec RFJHPRO1 guarda epsilon y las respuestas a ambas
escalas; el auditor recalcula la regla para la ventana completa. No es una
cota continua del error, ni una admisión de perturbaciones mayores.

## Decisión y siguiente bloque

Se admite composición temporal sólo para estas doce ventanas a calendario
fijo. El siguiente bloque debe extender la respuesta al retorno y añadir
la dependencia del tiempo/fase del evento antes de usarla para corregir
memoria periódica. También falta contrastar el calendario adaptativo.
El primer y segundo reset aquí aportan ventanas distintas, no periodos
consecutivos asentados. Sin nueva corrección periódica, encendido físico,
fidelidad vintage, nuevo audio, SPICE o admisión de tiempo real.
248 tests Rust heredados por identidad, sin reejecutarlos.

## Recursos

Campaña nativa 403.718825 s. Compilación≤120 s, ejecución≤900 s,
total≤1200 s; pila 32 MiB. Preflight 1 GiB + 96 MiB estimados, vigilancia
cada 250 ms y stop cooperativo. Mínimo observado de disco libre
1262161920 bytes. Verificador independiente 282.053017 s,
límite 900 s. Todos los artefactos anteriores conservan sus hashes.
