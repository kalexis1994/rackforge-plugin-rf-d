# Evaluación eléctrica preparada y residual compensado

## Alcance admitido

La voz híbrida conserva 118 incógnitas HIGH/LOW, ambas etapas Radau,
los dos contornos, ladder, recuperación, VCA y J7. Mismo tramo nominal
40–100 ms, KEY OFF a 75 ms, perfil VCO y estado inicial. No se añaden
constantes audibles ni se aproximan las leyes de dispositivos/carga.

El nuevo camino prepara metadatos inmutables una vez, omite Q26/Q28,
R59 y C18 de la antigua frontera de audio (ya presentes en el contorno
real), y usa coordenadas naturales. Comprueba valores al ensamblar y
valida el candidato HIGH/LOW completo antes de proyectarlo a bloques.
Evita recalcular el mismo candidato en cada proyección.

Los trials fuera del gate Newton devuelven sólo DC/dQ, sin construir
matrices que no consumen. La corrección J·LOW se acumula desde las
derivadas de cada dispositivo y puerto, en ambos modos. LOW se conserva;
el Jacobiano completo continúa calculándose para Newton y para el mérito
de nodos débiles. No se reutilizan Jacobianos de otro estado/h.

[Protocolo y evolución](HYBRID_STAMP_PROTOCOLO.md),
[banco admitido](../evidence/hybrid_stamp_native09.json),
[auditoría original](../evidence/hybrid_stamp_audit01.json).

## Contraste eléctrico

48 etapas de los 24 pares heredados, con estado reconstruido exacto:

| Objeto | Resultado frente al Schur anterior |
|---|---:|
| DC, fracción del gate 20 pA + 1e-7·abs(ref) | 1,801e-7 |
| dQ | Igualdad numérica en las etapas medidas |
| Jacobiano y masa | Igualdad numérica en las etapas medidas |
| Modo residual frente al completo, DC/dQ | Igualdad numérica en las etapas medidas |
| 472 columnas FD ±1 µV, fracción del gate | 0,000616 |

Las columnas incluyen cuatro etapas con BUS/VCA_BASE/TAIL. Tres
configuraciones inválidas se rechazan al preparar. La nueva frontera
de estado rechaza 26 casos inválidos entre modo completo/residual, con
26 retries válidos exactos: NaN, LOW no canónico, candidato fuera del
dominio, h/tiempos/KEY inválidos y receta incompatible.
[Guardas](../evidence/hybrid_stamp_guards01.json).

Dos recorridos propios, techos full 64/32 µs, 5279/5280 pasos y 962
observaciones. Frente al Schur previo: J7 RMS relativo ≤2,739e-14,
pico ≤4,595e-14 y error medio ≤5,812e-18 V. Fracción máxima del gate
de voltajes 3,171e-11; cargas 1,361e-10; estado final completo 2,226e-10.
El control fresco reproduce exactamente grilla y estado final archivados.

Conserva el error frente a la voz de referencia de 250 incógnitas:
J7 RMS 1,0672 %, pico 2,608 %, C2/C5/BUS y R59/R60 pasan. No elimina
el error del VCO periódico. Los techos casi no separan las mallas
adaptativas; no equivalen a una prueba de convergencia con tolerancia
más fina ni acreditan toda la banda o fidelidad al Moog físico.

24 pares reconstruidos, 5712 filas originales con Amount explícito:
residual máximo 0,71901 pA y corrección 0,32505 nV, dentro de los gates
20 pA/2 nV. Evaluación independiente de candidatos, sin nueva trayectoria
original. Newton mantiene 1 pA/2 nV. Backward máximo final 9,986e-12,
99922 solves y 499 refinamientos entre candidatos, incluidos replays.
Ocho replays y diez rechazos de paso atómicos pasan; heap cero medido.

## Costo

Mismo compiler, rlib, flags, tramo, techo y equipo. Integración fuera de IO:

| Ejecución | Tiempo para 60 ms simulados |
|---|---:|
| Schur anterior fresco, techo 32 µs | 23,5213 s |
| Evaluación preparada, techo 64 µs | 20,7730 s |
| Evaluación preparada, techo 32 µs | 21,1354 s |

Ratio comparable **0,898562**, gate previo ≤0,90: **10,14 % menos costo**
en este ensayo. El margen respecto del gate es pequeño; una medición
puntual no garantiza ese ahorro ante variación de CPU, otra escena o
compilación. No se declara tiempo real, deadline o motor tocable.

La mejora corresponde al conjunto de cambios: preparación, eliminación
de la frontera duplicada, ruta de residual, disposición de temporales,
validación de estado y acumulación dispersa de J·LOW. Preparar metadatos
por sí solo no aceleró esta escena. La cadena detallada sigue offline.

## Rechazos y almacenamiento

Antes de la admisión quedaron guardados un rechazo de compilación del
adaptador y siete rechazos de costo, todos con fuentes y replay sin
cambios. Ratios de costo: 1,03873; 1,03550; 0,901787; 0,922739;
0,913501; 0,900573; 0,918001. Los candidatos casi aprobados permanecen
rechazados; no se redondeó ni debilitó el gate 0,90. La reorganización
final de J·LOW fue un cambio de código medido con control nuevo.

Recibos/fixtures acotados a aproximadamente 20,45 MB antes de QA, con
fuentes, etapas seleccionadas y replays comprimidos; sin almacenar otra
trayectoria completa de muestras. Un solo `tmp/lab-current`, vacío;
ejecutables y semilla retirados. Sin WAV, Cargo, cache, rlib nueva o
inputs privados de sonido. Todos los inputs admitidos previos se mantienen.

Siguiente bloque: mejorar la representación del sistema lineal sobre
esta evaluación, perfilando su costo con el mismo control; conservar
incidencias y cargas. Arranque/ataque, CV y producción siguen pendientes.
