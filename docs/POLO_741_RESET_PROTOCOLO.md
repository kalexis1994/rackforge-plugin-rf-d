# Flujo, historia y ecuación de L2 en reset

2026-10-06. Continuación de la sonda Newton local, sin transferencia automática
al ejecutable oficial. Conservar completamente `newton-build01` y sus fuentes.
Copiar fuente y build en `newton-build02`; sólo recompilar los archivos
intervenidos. Identificar la copia, el compilador, módulos y ejecutables.

## Observación antes de cambiar aritmética

L2 de IC3 une 98 → 17 en el macromodelo TI LM741. No es un componente físico
identificado dentro del chip. Mantener L=530.5 mH, multiplicador, estado DC,
historia, R13=1 kohm, fuentes y toda la trayectoria original.

Ventana 2.2773–2.2775 ms, mismos decks BUS cero y variable del bloque anterior.
Registrar cada carga y solve de esta rama: corriente, flujo presente e
histórico, coeficientes Gear, orden/modo, resistencia y fuente equivalentes,
y voltajes de terminal. Parear por orden de registros y número de rama;
el tiempo representado puede repetirse entre intentos.

Para flujo phi=L*i/m, la ecuación discretizada es
`v98-v17 = a0*L*i/m + sum(aj*phi_j,j>=1)`.
La matriz estampa `v98-v17-req*i=veq`, con `req=a0*L/m`.
Recalcular la suma histórica y el residual de **esta fila** con Decimal de
80 dígitos a partir de los valores binary64 observados. No llamarlo residual
KCL completo. Comparar el cálculo real de `veq` con esa suma y buscar cambios
de RHS entre iteraciones que conservan coeficientes e historia.

Admitir la observación sólo si conserva exactamente todos los tiempos y seis
vectores del baseline anterior, tanto apagada como encendida. BUS cero debe
seguir completo y BUS variable debe conservar su rechazo. Verificar las fuentes
del inductor y NIintegrate contra la revisión ngspice 46 fijada antes del parche.

## Reformulación condicional

Si la observación confirma que el RHS histórico depende numéricamente del flujo
provisional, ensayar **una** reformulación Gear de órdenes 1/2: calcular `veq`
directamente desde los historiales, evitando restar `a0*phi0` del voltaje integrado.
No modificar req, flujo/voltaje guardado, método, tolerancias ni ramas físicas.
La igualdad algebraica debe cubrir ambos órdenes y los coeficientes reales;
el experimento queda condicionado al build local.

Antes de BUS variable, exigir control BUS cero completo de 40 ms, diferencia
de voltaje ≤5 mV en grilla común de 5 us, frecuencia ≤1 cent, igual cantidad
de resets y desviación temporal ≤10 ns. Son gates anteriores, sin alineación
de fase. Si falla, conservar y detener. Si pasa, medir BUS variable completo;
un prefijo no admite integración. Cualquier resultado posterior debe volver
a cerrar R45 y contorno, contrastarse con el oficial y dejar el runtime abierto.

Fuentes: [INDload](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/spicelib/devices/ind/indload.c),
[NIintegrate](https://raw.githubusercontent.com/imr/ngspice/ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6/src/maths/ni/niinteg.c),
y [observación previa](NEWTON_RESET_RESULTADOS.md).
