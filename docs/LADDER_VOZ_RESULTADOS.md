# Ladder reconstruido en la voz: unión numérica verificada, costo rechazado

## Qué se ejecutó

El [candidato](../crates/rf-d-circuit/src/ladder_voice.rs) integra el
kernel local en ambas etapas de la voz nominal, siguiendo el
[protocolo previo](LADDER_VOZ_PROTOCOLO.md). Resuelve 111 coordenadas por
etapa (222 temporales), reconstruye 118 nodos físicos y conserva las
cuatro memorias internas, cinco puertos, acoplamientos y el bias de
220 µF. TAIL/VCA_BASE conservan identidad. No hay memoria congelada.

La preparación conserva receta, fuentes y leyes. El estado anterior
HIGH/LOW sigue siendo físico. Los incrementos retenidos se avanzan con
compensación; los derechos se reconstruyen desde incremento izquierdo
menos incremento diferencial, sin restar endpoints redondeados. Cada
evaluación vuelve a resolver la álgebra desde el estado anterior; no
publica una semilla ni un factor de un intento rechazado.

El [generador](../tools/prepare_ladder_voice.py) deriva el solver directo
a 108 incógnitas de contorno, 110 de audio y cuatro puertos temporales.
Conserva CSR, pivoteo, backward 1e-11, tres refinamientos máximos y
comprobación de estructura/capacidad. La salida de Newton exige residual
físico completo ≤1 pA y corrección del solver original ≤2 nV. El estimador
también conserva los 118 nodos. El helper `increment` del probe presupone
ROOT válidos y sólo extrae fixtures; no participa en `advance`/`radau`.

## Resultado medido

[Runner](../tools/check_ladder_voice.py), [recibo](../evidence/ladder_voice_native01.json),
[guardas](../evidence/ladder_voice_guard01.json) y
[auditoría independiente](../evidence/ladder_voice_audit01.json).

| Gate | Resultado |
| --- | --- |
| 24 ROOT previos / 48 etapas reconstruidas | Error máximo 1,677931 nV; gate 2 nV |
| Carga frente al incremento admitido | Error 0 A; M·Tz y Tzᵀ·M exactamente cero en la unión |
| 144 direcciones frente al sistema original completo | Fracción máxima del gate 0,839599 |
| 222 columnas FD del Jacobiano reducido | Fracción máxima del gate 0,370981 |
| Guardas del wrapper | 36 rechazos; 35 retries exactos, uno después de dos rechazos consecutivos |
| Guardas del solver de 222 incógnitas | 83 rechazos con 83 retries exactos; incluye capacidad, overflow y enlaces entre interiores |
| Coeficientes / fixtures del solver | 98.568 entradas y 16 RHS con fill/swaps; dos enlaces legales añadidos y retirados |
| Dos trayectorias propias, 64/32 µs | 481 observaciones cada una; refinamiento y gates reservados pasan |
| J7 frente al directo | RMS relativo ≤4,75e-9; pico relativo ≤7,18e-9 |
| Nodos/estados finales frente al directo | Fracción máxima del gate 0,000093165 |
| Auditoría de 5712 filas originales / 24 pares | Residual ≤0,998264 pA; corrección ≤1,678588 nV |
| Newton en todas las salidas observadas | Residual ≤0,999932 pA; corrección ≤1,996897 nV |
| Backward en las trayectorias reducidas | ≤9,997113e-12; gate 1e-11 |
| Publicación / heap | Ocho replays y diez rechazos atómicos; cero asignaciones en las dos integraciones |

Los márgenes de reconstrucción/dirección y, especialmente, de corrección
Newton no son amplios. Se conservan los gates; no se extrapolan esas
holguras a otra receta, arranque o CV. Las trayectorias mantienen el perfil
VCO y la referencia reservada anterior, sin nueva calibración. La auditoría
usa las ecuaciones originales de 119 nodos, incluido Amount; evalúa los
endpoints nativos reconstruidos y no genera otra trayectoria original.

## Costo: candidato no promovido

Control directo fresco 32 µs: **16,560866 s / 60 ms** de circuito.
Candidato 64/32 µs: **25,508463 / 25,544154 s / 60 ms**. Ratio de admisión
32 µs **1,542441**, frente al gate ≤0,90: **rechazado**, aproximadamente
54,24 % más costo. Semilla, flags, compilador/rlib y equipo comunes;
serialización fuera del tiempo de integración. Un ensayo por configuración,
sin atribución causal ni inferencia de deadline o fidelidad física.

El recibo conserva fuentes, input, proceso y replay sin modificar del
rechazo. Pasan las comprobaciones numéricas de la unión, pero `passed`
del experimento es false por costo. El [cierre QA](../evidence/ladder_voice_tests01.json)
lo distingue explícitamente: unión numérica verificada, sin admisión de
esta reducción como motor activo. Sigue activo el directo de
`7c0524273048099f3fd246562c9b87d7cadffb61`; su ratio admitido no se cambia.

Los 255 tests Rust previos se conservan por identidad y no se reejecutan.
Las pruebas de unión descritas arriba sí son nuevas. Se reutilizaron los
inputs de sonido y la librería admitidos; no hay WAV, Cargo, rlib o árboles
de build nuevos. Ejecutables y semilla retirados del área temporal única.

## Continuación

El código de esta primera unión evalúa el ladder dentro del kernel local
y de nuevo al recorrer el grafo físico completo. También materializa el
Jacobiano físico antes de proyectarlo. Es trabajo duplicado observable en
el código; este ensayo no mide por separado cuánto cuesta cada parte.
Siguiente: evaluar directamente las reacciones condensadas y el padre
sin volver a estampar el ladder, manteniendo esta unión como control
funcional, la auditoría original, el historial y todos los gates. Medir
costo fresco sólo después de conservar precisión. Evitar otra secuencia
de ajustes de representación sin cambiar ese trabajo algorítmico.
