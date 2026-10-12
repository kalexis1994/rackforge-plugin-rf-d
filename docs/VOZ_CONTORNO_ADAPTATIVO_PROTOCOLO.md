# Control temporal229 y contacto sostenido

Protocolo previo, 2026-10-12. Continúa
[Q25/Q15 cargados](VOZ_BIESTABLE_CARGADO_RESULTADOS.md), CA3046,
sin unidad física. Misma conectividad, dispositivos, valores de panel,
almacenamiento y parámetros condicionados; no hay nueva ley ADSR.

## Función que cierra el bloque

El motor200 existente aporta coarse Radau de2h y dos pasos finos deh.
Se adapta su binding al kernel229, con error de todas las incógnitas:
2 µV/2 nA, aceptación≤1; duplica si≤.25, sostiene en otro caso.
Rechazos numéricos/LTE reducen el paso; historia fija durante los trials.
Mínimo full8 ticks, intento máximo20; ticks=125 ns/65536.
Publica sólo los dos pasos finos una vez completadas las observaciones.
Errores de destino, precisión o presupuesto preservan checkpoint por bits.
La ley de circuito y Newton64/24/gates del banco anterior no se modifican.

KEY0..10 V/contacto S son cambios explícitos de frontera, sin alterar estado.
Restaurar un checkpoint inmediatamente posterior a un cambio KEY no exige
que la vieja tensión algebraica del diodo CR10 ya esté en equilibrio.
La validación del dominio propone sólo el mismo trial KEY_DIODE_K del
solver; nunca publica ese guess ni cambia memoria/cargas almacenadas.
El codec declara toda la receta, pasos, contador y fuentes para reanudar.

## Escena y alcance

Inicio2795503616 ticks (5.332 ms), final229 propio de7.8125 ns ON/OFF.
Todas las458 componentes se heredan por bits. Ninguna carga se inicializa.
Tres tramos: reposo2 µs, KEY10/S cerrado50 µs, KEY0/S abierto50 µs.
KEY/S cambian sólo en las fronteras exactas. El contacto sostenido deja
evolucionar Q15 colector, ataque y la carga C2 antes de la liberación.
No se espera ni se declara ataque/decay/sustain completo en102 µs.

Cuatro perfiles ON/OFF × máximo medio paso250/125 ns (131072/65536 ticks).
Misma semilla fina por ON/OFF. Se alcanza cada frontera y cada10 µs de
observación dentro de los tramos sostenido/liberado; esa grilla no impone
valores del contorno. Comparación de229 incógnitas en12 relojes:
semilla, fin de reposo y diez cortes, gate2 µV/2 nA.

Guardar todos los tamaños/errores/intentos aceptados y voltajes del contorno,
J7, BUS y corrientes. Auditar primer/último accepted de cada tramo:
coarse+dos finos, dos etapas cada uno;144 candidatos/32976 ecuaciones
con grafo/FD y Q Decimal100, gates20 pA/0.2 nV y1 µV/1 nA.
Balances C2/C18/C27/C7/C4 y cargas de Q25/Q15 por tramo/total,
gate1 pA×duración, cuadratura Radau de los pasos finos publicados.

Restore al principio y al primer corte interior de cada tramo largo,
y comienzo del reposo: cinco restores completos por perfil, repitiendo
todo el resto del tramo, con decisiones LTE/candidatos/iteraciones por bits.
No se altera el calendario para el replay. Rechazar corrupción de magic,
estado NaN, fase/receta y paso. Probar destino inválido y fallo de intento
con rollback completo; el fallo de intento se induce con presupuesto1
durante la primera transición S, conservando la receta/datos originales.

Presupuesto300 s por perfil,1500 s campaña,120 s compilación,
300 s auditor; salidas privadas≤32 MiB, reserva1 GiB, stack32 MiB.
Conservar rechazo y replay idénticos antes de cualquier reparación.
Biblioteca congelada;248 tests heredados por identidad, no reejecutados.
Sin audio nuevo, cargas adicionales de placa2, SPICE, identificación
vintage, gate de nota completa, latencia/host o deadline de tiempo real.
