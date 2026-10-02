# Controles cero y pequeña señal de ataque: protocolo separado

Declarado el 2 de octubre de 2026 después del
[contraste de direcciones extremas](BIESTABLE_DIRECCIONES_EXTREMAS_RESULTADOS.md),
antes de medir este bloque. Los **18 fallos individuales de ataque anteriores
permanecen abiertos**, con sus amplitudes y gate originales.

## Controles y nuevos niveles

Se conserva el mismo circuito, residual, Jacobiano, Newton, memoria doble,
publicación, reloj, mapas y ventanas de 64 pasos. KEY = 10 V, h >= 1 ps.
La publicación exige KCL < 10 pA, rama < 1e-14 V y restauración tipada
exacta; Newton exige corrección < 10 nV. No se ejecuta aceptación adaptativa.

Primero: cuatro continuaciones de **inyección cero**, una por ventana,
con el mismo mecanismo de perturbación/continuación. Plan: **256 solves
no lineales nuevos**. Se compara la historia publicada con la base archivada:
gate nodal y de memoria absoluta < 10 nV; también se registra identidad
canónica de historias, sin reemplazar el gate por una comparación de tipos.
Esto controla una posible deriva de reproducción; no calibra parámetros.

Después: sólo ventana attack, los seis vectores congelados del informe
anterior (C7 actual/común/diferencial y máximos nodal/memoria/historia).
No se recalcula selección, SVD ni normalización. Nuevas amplitudes:
**0,125 / 0,0625 / 0,03125 / 0,015625 uV** de norma euclídea de
historia doble, ambos signos. Plan: **48 continuaciones = 3.072 solves
no lineales nuevos**, 24 contrastes centrales y 24 individuales.
Total del bloque: **3.328 solves**, cero solves nuevos de mapas.

Se guardan las mismas métricas centrales, por signo y pares del protocolo
anterior. Gate intacto por coordenada/intervalo: error < **10 nV +
1e-3 |predicción|**, para nodos y memoria. Las cargas conservan Q/(1 pF)
como escala numérica, sin capacitancia añadida. Las semillas nodales no cambian.

## Interpretación fijada antes de medir

Conservar todos los niveles, sin escoger sólo los favorables ni presentar
estos niveles como corrección de los fallos anteriores. Un pase aquí
pertenece a esas direcciones/amplitudes/ventana; no define una bola de
pequeña señal en 50 dimensiones, una tolerancia de integración, exactitud
vintage o un límite musical universal. No se ajusta un coeficiente cuadrático
con estas respuestas para luego validarlo contra los mismos datos.

Se informa la respuesta par por amplitud, sin afirmar un orden asintótico
ni una causa exclusiva del error. Si el control cero falla, conservarlo
separadamente de la respuesta finita, sin corregir la base ni resetear.
Un fallo de solve/publicación detiene sólo esa continuación y guarda estado
entrante, candidato/diagnóstico disponibles. Un fallo comparativo no cambia
los gates. SHA de entradas antes/después; informes previos intactos.

No hay defecto temporal exacto ni cota global, refinamiento, audio o deadline
admitidos. El gate temporal de 1 mV desde DC sigue abierto.
[Productor](../tools/loudness_latch_bdf_static_precision_memory_small_signal.py).
