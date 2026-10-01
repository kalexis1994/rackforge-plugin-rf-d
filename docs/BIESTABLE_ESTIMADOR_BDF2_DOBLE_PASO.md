# Estimador BDF2 por paso completo y dos medios pasos

## Motivo y contrato

El estimador anterior compara BE y BDF2 desde el estado actual. Se prepara
un estimador que usa **BDF2 en ambas rutas**, manteniendo sus dos historiales
entrantes. Este corte verifica el prototipo; todavía no genera una trayectoria
adaptativa completa ni cambia la admisión del contraste anterior.

Desde tiempos t y t−k aceptados se calculan:

1. Un BDF2 completo de duración h.
2. Un BDF2 de h/2 desde los mismos historiales.
3. Un BDF2 desde el estado intermedio hasta el **mismo tiempo binario**
   alcanzado por el completo. El segundo h parcial se obtiene de esa resta;
   no se retima el destino para forzar coincidencia.

Las tres publicaciones se verifican desde sus historiales reales con
Decimal80: KCL <10 pA, ecuación de rama <10 fV y serialización exacta.
El intervalo real mínimo de cada ruta es 1 ps, así que el macro necesita
al menos 2 ps; crecimiento BDF2 ≤2. El prototipo exige fuente constante
y dos estados aceptados: no define arranque ni manejo de otro salto de KEY.

La diferencia se escala por voltajes de nodo y juntura, conservando la
métrica independiente del origen de carga. No se divide por un factor
Richardson supuesto. El trial comprueba incremento de juntura del intervalo
completo y productos h·λ+ de las tres rutas; los modos son congelados y no
dan una garantía de estabilidad continua.

Al aceptar, el candidato publicado es **el paso completo**. Ambos medios
pasos permanecen provisionales. Esto conserva h como intervalo anterior
de la trayectoria y permite crecimiento ×2 en el próximo intento. Si se
publicaran los medios pasos y luego se duplicara el macro, la comparación
completa siguiente pediría razón h/k=4, fuera del dominio BDF2 admitido ≤2.

## Contraejemplo al factor 1/3

Para el problema sintético normalizado y=t³, y′=3t², con historiales exactos
en 0 y −k, r=h/k, el defecto de la derivada cuadrática es
−h(h+k)y‴/6. Resolver la recurrencia y propagar el error del primer medio
paso al segundo da, en unidades de h³:

`Efull = (r+1)² / [r(2r+1)]`

`Efine = (3r²+6r+4) / [12r(r+1)]`

El cociente `Efine / (Efull−Efine)` vale 13/19 para r=1, **no 1/3**.
Para r=0,25; 0,5; 1; 2 resulta 0,57233; 0,62000; 0,68421; 0,76087.
La comparación comparte un historial precedente que no fue refinado;
el patrón clásico de dos soluciones globales con pasos uniformes no describe
este ensayo local. Estas fórmulas no calibran el error de un DAE no lineal.

## Sondas de circuito y regresión

Antes de ejecutar se fijan tres límites de anclaje C3: 2,3 ms, 2,42 ms y
2,44205 ms. Se usa el último estado aceptado no posterior a cada límite,
con razones h/k de 0,25; 0,5; 1; 2. Las **12 sondas** conservan las hipótesis
R61=200 Ω/BUS=0/KEY=10 del [modelo BDF2](BIESTABLE_BDF2_CARGA.md).
La diferencia cruda máxima de nodo entre rutas es **0,683818 µV**.
Ese resultado local no predice el pico acumulado de una trayectoria.

Productor: `tools/loudness_latch_bdf_doubling_probes.py`.

Datos: `evidence/loudness_latch_bdf_doubling_probes.json`.

`python tools/loudness_latch_bdf_doubling_probes.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf_doubling.py -v`

Seis regresiones verifican las tres rutas de cada sonda, memorias intermedias,
residuos, reproducción y Jacobiano totalmente FD en razones 0,25/2 para
los tres anclajes. También contrastan el cúbico exacto, aceptación del
candidato completo, rechazo con tolerancia muy estricta y entradas fuera
de dominio, sin modificar ambos historiales.

## Siguiente gate

Declarar dos políticas del estimador v4 antes de medir y repetir desde DC
con arranque explícito, rechazos conservados y gate máximo de 1 mV.
Conservar los barridos BE/BDF2 y el experimento condicional. No se admiten
refinamiento global, error continuo, conmutación física ni audio con estas
sondas. Los parámetros sintéticos y las cargas omitidas siguen abiertos.

El corte posterior [D4/E4 desde DC](BIESTABLE_BARRIDO_DOBLE_PASO.md)
ejecuta ese protocolo y conserva su resultado global y consultas propios.
Los datos de este prototipo permanecen intactos.
