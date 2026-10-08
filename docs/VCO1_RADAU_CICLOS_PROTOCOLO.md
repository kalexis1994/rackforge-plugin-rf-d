# Radau: arranque propio y ciclos nominales

Protocolo fijado antes de medir. Perfil clásico CA3046 de SVC-9, PDF
p. 5/19 y tarjetas nominales ya congeladas en el bloque Radau anterior.
TEMP=TNOM=25 °C; C4=10 pF, C1=10 nF. Controles y mixer impuestos.
No identifica hardware ni calibra otra revisión o población.

## Dominio y gates

Dos recorridos seriales de 30 ms desde `vco1_startup::startup`, sin importar
raíces o historia de SPICE. C1=0 es la frontera inicial condicionada; retirar
su corriente al comenzar. Conservar las 134 incógnitas y hi/lo, ambos 741,
las cargas no lineales y flujos. Kernel Radau, fine/data/solver sin cambios.
Máximos de medios pasos aceptados: 250/125 ns. Tick=125 ns/65536;
reloj u64 (30 ms exceden u32), export exacto en f64 porque ticks <2^53.
Piso medio 4 ticks; 20 intentos, 400.000 endpoints, Newton 64/24;
residual 1e-13 A/1e-11 V, corrección 2e-9 V/2e-12 A.
Full−end sin dividir: 2 µV/2 nA en las 134 incógnitas. Publicar ambos
medios estados sólo después de admitir las tres raíces y su error.

Reusar `vco1_circuit_probes.GATES`: dispersión relativa <=1e-5,
frecuencia 250/125 <=1 cent, extremos saw/triangle/pulse <=5 mV,
imbalance integrado Qa/Q10/C1 <=0,002. Asentar 15 ms y exigir al menos
tres cruces crecientes reales C1=−2 V, con interpolación de medida; no
usar un reloj sintético. Criterio integrado excluye Q7 y cuadratura,
como el protocolo heredado. No confundir derivadas Euler con Radau:
I2=F(Y2)−4,5[Q(Y1)−Q(X0)]/h+2,5[Q(Y2)−Q(X0)]/h.
Corrientes positivas salen del terminal. Qa/Q10 colector, Q7 gate y
panel se exportan; contrastar corrientes seleccionadas con Decimal100,
gate 2e-10 A. R6=12,5 kohm, tensión panel dividida por R6.

Seleccionar primera/última raíz y las dos mayores variaciones nodales,
determinísticamente del export completo. Resolver cada par Radau por
Decimal100 desde la historia entrante, sin semilla nativa, manteniendo
los gates del bloque anterior. Auditar KCL, suelo y puertos 741 por etapa.
El arranque se verifica contra la raíz nominal propia anterior, cuyo
contraste usa interfaces físicas binary64 y álgebra Decimal100; las
nuevas etapas usan interfaces Decimal100 sin redondeo intermedio.
No extrapolar ese contraste seleccionado a cada raíz de la trayectoria.

## Recursos y conservación

Dos procesos seriales, hasta 1200 s cada uno, pila de laboratorio 8 MiB;
reserva de disco 2 GiB monitoreada. Preflight mínimo 128 MiB sobre reserva;
no predice tamaño comprimido. Límite endpoints fija peor export crudo,
que nunca se escribe al disco: stdout se comprime por bloques de 512 filas.
XOR reversible u64 entre filas de cada columna, byte shuffle y gzip:
formato little-endian, cabecera u32 número de filas por bloque y 546
columnas f64. Decodificar y recomputar SHA256/longitud del flujo nativo
antes de medir; no cuantizar ni descartar etapas/memorias. Validar el
reloj, finitud, hi/lo, dominio y gates en todas las filas al decodificar.
Guardar originales fallidos y replay en archivos distintos; recursos,
compilación, almacenamiento, medición y física son estados distintos.

Columnas: ticks, intervalo, residual, corrección, LTE, intentos (6);
endpoint hi/lo (268), stage hi/lo (268), Qa/Q10/Q7 (3), panel (1).
Inicial: estado propio repetido en stage, dt/gates cero y corrientes DC.
Sólo pasar todos los gates admite este banco nominal de laboratorio.
C4=100 pF, CV/trims, carga activa, producción, heap/deadline y audio
requieren su propio trabajo; equivalencia numérica no acredita sonido vintage.
