# Integrador candidato con J66 compensado: protocolo previo

Tras archivar la auditoría de 64 intervalos, probar una **variante explícita
de laboratorio**. La clase histórica, sus productores y evidencia quedan
intactos. Sólo el Jacobiano estático de audio 66×66 cambia a los sellos
compensados; contorno, R59, capacitancias, Q25/Q15, residual original,
Newton/line search, BDF2 y publicación se heredan sin modificación.
La preparación racional ocurre antes de evaluar; no hay admisión de audio.

Primero verificar igualdad binary64 del residual original y candidato en
los **64 candidatos guardados**, y en cuatro desplazamientos adicionales
por candidato: delta ±1 µV en los nodos 27 y 66. Son **320 pares de
evaluaciones**, sin Newton nuevo. Comparar cada J candidato con la matriz
compensada archivada; verificar la ruta FD explícita en el primer candidato
de cada ventana. Estas evaluaciones no son solves no lineales.

Restaurar el mismo historial doble inicial de cada una de cuatro ventanas;
mantener los **16 intervalos E4G8 guardados**, KEY=10 V, r61=200 Ω y modelo
documental `finite_transit` de escala 1. Son **64 intervalos no lineales
planificados**. Avanzar cada ventana desde sus propios estados candidatos
sin sustituirlos por la referencia. No aplicar un controlador adaptativo,
buscar otra raíz, retimar ni reiniciar memoria. Ante fallo conservar el
historial entrante, intervalo, mensaje y último estado; detener esa ventana.

Gates heredados: Newton KCL <10 pA y corrección <10 nV; publicación directa
desde los dos historiales KCL <10 pA, ecuaciones de ramas <10⁻¹⁴ V y
restauración tipada exacta. Comparar todos los nodos compensados contra la
trayectoria anterior con gate **10 nV absoluto**. Comparar las 25 memorias
con **10 nV** en su coordenada anterior (21 voltajes; cuatro cargas con
escala 10⁻¹² C/V exclusivamente numérica). Este contraste mide diferencia
entre implementaciones con reloj fijo; no error temporal ni fidelidad física.

Registrar incrementos, estados completos, hashes de historial entrante,
diagnósticos y publicación incluso si falla el contraste contra referencia.
El contraste de referencia fallido no aborta una ventana cuyo solve y
publicación pasan; tampoco admite la ruta. Contar intentos/intervalos,
iteraciones y fallos, sin convertirlos a benchmarks de CPU o deadlines.

Identificar fuentes/datos antes y después. No reducir presupuestos, gates
o ventanas después de medir. No se ejecuta aquí una trayectoria desde DC
con el controlador E4G8 ni se cierra el fallo global de refinamiento de 1 mV.

`python tools/loudness_latch_bdf_static_precision_continuation.py`
