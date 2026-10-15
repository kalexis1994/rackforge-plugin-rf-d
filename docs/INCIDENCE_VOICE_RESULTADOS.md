# Ensamblaje por incidencias: motor nominal seleccionado

## Qué cambia

[Contrato previo](INCIDENCE_VOICE_PROTOCOLO.md) y
[contrato de selección](INCIDENCE_SELECTION_PROTOCOLO.md). Se conserva
el directo anterior como referencia inmutable. El candidato retira sus
matrices globales J/M de 118×118 por etapa: reúne coeficientes actuales
de contornos 56 y audio 68 en un paquete ordenado por fila/columna.

Contornos primero, después audio con los mismos guards g/m≠0; derivada
VCO al final. Se conservan sumas en nodos compartidos, C18 una vez, todas
las cargas e historial HIGH/LOW. J y masa permanecen separados hasta
construir B·mass+dc con el orden original del CSR. No cambia factor,
pivotes, escalas, capacidades temporales o estimador. Se añade rechazo
explícito de escalas backward no finitas: una cancelación finita no puede
ocultar una normalización con overflow.

El soporte sale de valores presentes, leyendo todos los coeficientes de
los componentes; no se aprende de una escena. Admite enlaces nuevos dentro
del contrato físico y detecta cruces ilegales en el solver. Arrays fijos,
sin heap en integración. El paquete tiene capacidad 4096 por etapa y el
sistema temporal conserva su capacidad 4096. FULL=false no publica tangente.

El [punto de entrada seleccionado](../crates/rf-d-circuit/src/active_nominal_voice.rs)
reexporta esta implementación. Es el motor **nominal de laboratorio** para
la rama existente, no una integración de plugin o renderer general.
CA3046/SVC-204D nominal, un VCO de fase con carga aproximada sobre sus
memorias internas, sierra fija y controles de la escena; 40–100 ms desde
semilla reservada a 40 ms, KEY OFF 75 ms. No se amplía arranque, CV,
antialias de producción o fidelidad física.

## Precisión y representación

[Recibo nativo](../evidence/incidence_voice_native01.json):

| Comprobación | Resultado |
| --- | --- |
| Pares/etapas | 24 / 48 |
| DC, dq y estados HIGH/LOW; FULL/residual | iguales al directo |
| J/M físicos | 1.336.704 valores iguales numéricamente |
| Sistema temporal | 1.336.704 coeficientes iguales bit a bit |
| Direcciones | 192 idénticas al estructurado anterior |
| Contraste con solve completo refinado | fracción máxima del gate 0,972279 |
| Rechazos del solver / nuevos enlaces legales | 33 con recuperación exacta / 24 |
| Guardas propias del paquete | 37 rechazos / 27 reintentos válidos |
| Máximo de entradas por etapa observado | 480 / capacidad 4096 |
| Backward local final máximo | 9,972265e-12 frente a 1e-11 |

Guardas de paquetes incompletos, índices, capacidad, no finitos, overflow
desde entradas finitas y actualización atómica. Cancelaciones conservadas;
eliminar una entrada cancelada libera capacidad para otro enlace. El
[contrato adicional de representación](../evidence/incidence_voice_packet01.json)
comprueba siete casos de orden, asignaciones repetidas, sumas, cancelación,
inserción entre columnas/filas y tamaño. `Parts` pasa de **226.568 a 78.480
bytes**; el paquete mide 74.696 bytes. Es tamaño del contenedor en este
toolchain, no medición del pico de stack del procesamiento completo.

Trayectorias 64/32 µs con GRID/ROOT/SOLVER y estados finales idénticos al
directo, sin alineación o normalización. Pasan voz reservada/refinamiento.
Máximos Newton 0,999722 pA y 1,872098 nV frente a 1 pA/2 nV. Pasos mínimos
observados 1 µs; 5279/5280 pasos. Ocho replays, diez rechazos atómicos y
heap cero en el candidato; la fachada repite estas comprobaciones.

[Auditoría independiente](../evidence/incidence_voice_audit01.json): 24 pares,
5712 filas originales con Amount y estrella resistiva VCO; máximos
0,719007 pA y 0,325050 nV, dentro de 20 pA/2 nV. Audita los estados
reconstruidos; no integra otra trayectoria independiente de 250 nodos.

## Costo y selección

Mismo compiler/rlib/flags, sin timers internos. Segundos de procesamiento
de la rama de 60 ms simulados; replays excluidos del acumulado de costo.

| Medición a máximo 32 µs | Directo fresco, s | Nuevo motor, s | Ratio |
| --- | ---: | ---: | ---: |
| Candidato | 16,703000 | 12,673773 | 0,758772 |
| Fachada seleccionada, segundo control fresco | 16,390667 | 12,923647 | 0,788476 |

Ambas pasan **≤0,90**: **24,12 % y 21,15 % menos costo**, respectivamente.
La [selección verificada](../evidence/incidence_voice_selection01.json)
ejecuta también 64 µs; conserva observaciones y estados idénticos al
candidato. Se adopta **active_nominal_voice.rs** con solver por incidencias.
Estos ensayos no separan el ahorro de materialización del de recorridos,
no son una distribución estadística de deadlines y **no acreditan RT**.
La cadena detallada continúa offline.

[QA global](../evidence/incidence_voice_tests01.json) fija rutas y SHA del
solver, implementación y fachada. Su commit propio queda explícitamente
pendiente dentro del JSON; después de commitear se verifica cada blob del
commit real por SHA. No se adjudica al nuevo solver el commit histórico
del directo anterior. Las fuentes y su origen anterior se conservan.

## Conservación y siguiente bloque

Protección de las 4215 fuentes previas y 8769 inputs privados; 255 tests
Rust heredados por identidad, sin reejecutar. Se ejecutaron dos ramas del
candidato, dos de la fachada seleccionada y dos controles frescos.
Recibos acotados a 8 MiB sin QA; un tmp/lab-current vacío, sin WAV,
Cargo, rlib, cache o inputs privados de sonido nuevos.

Con la representación admitida, priorizar el arranque propio de la cadena
nominal y su ataque, en lugar de otra optimización local. Fijar primero
condiciones iniciales y memorias compatibles con la fuente periódica
existente, evitando proyectar un estado a 40 ms de una trayectoria reservada.
El arranque de la cadena no demuestra el arranque físico del VCO real.
Contrastar DC/carga, trigger y ambas etapas con ecuaciones originales;
después recorrer la nota completa y su refinamiento. Conservar el motor
anterior como control y los gates. No ampliar controles o generación de
muestras mientras no pase esa unión funcional.
