# Refinamiento del primer hueco: protocolo congelado

2026-10-05. Fuente: resultado real del soporte 32 de la variante elegida,
ancho 8, ensayo 1 del segundo banco preparado. 33 soportes hasta
1556444031219243/4611686018427387904 s, P fija, 22 memorias y cota heredada.
El soporte 33 es el único objetivo; su curva, extremos, cargas/RC/Q,
reloj y radio 1 µV se conservan. No se prolonga a 34 ni se aumenta el radio.

## Selección y particiones

Control 8 macroceldas; refinamientos 16, 32, 64, en ese orden. Todos parten
del mismo resultado real elegido. Detener en primer cierre completo; si
ninguno cierra, conservar cuatro rechazos y reloj admitido anterior.
Cada partición paga h/n y sus ocho subceldas internas de RHS/acción.
Se recalculan forcing, residual, RHS firmado y restos independientes,
acciones, propagación y observadores Decimal100 por celda.

El control anterior de ancho 1 usaba otra memoria entrante. Se compara
contra él la curva, RHS, forcing y cada acción, pero no se exige su pico
al recalcular el cierre con la fuente elegida. No se toma una memoria de
una rama rechazada ni se mezclan memorias de variantes.

## Reutilización certificada

Se reutiliza sólo el bloque uniforme de ancho 1, índice 1, del soporte 33.
Comprobar identidad de curva y radio, dominio 0..1, ledger analítico completo,
recinto inflado, certificado de inversa y SHA de su matriz restaurada.
Su norma, pesos y escalas vienen del mismo manifiesto certificado.
Reproducir las tres tasas y sus consultas LDL en la validación; el productor
no vuelve a medirlas. Una preparación explícita con contexto y estado
idénticos al bloque se verifica por cada budget. Ningún candidato o solve nuevo.

Los tests reproducen todas las acciones con control original y helper
preparado, mediante bytes completos, no sólo picos. Se reconstruye nodo 66
como suma racional de 22 términos de memoria y directo, para anclaje y
forcing. El grupo de junturas y el kernel orientan el diagnóstico sin
atribuir causa física o cancelar restos independientes.

## Archivo y gates

Predeclarar rutas tipadas por partición y celda, y por soporte. Cada celda
conserva residual, RHS/restos, acciones, métricas y tres consultas Decimal100.
Cada soporte conserva cierre completo, kernels, memoria y diagnóstico; el
manifiesto identifica todas las celdas por tamaño y SHA comprimido/canónico.
Fuente, stdout/stderr, comando, exit y snapshots se guardan en lanzamiento.
Archivos parciales no admiten tiempo. Congelar productor/protocolo antes de
medir y datos/tests/validator antes de validar, con corpus completo posterior.

Gates intactos: KCL 10 pA, corrección 10 nV, rama lineal 10 fV, backward
1e-10, objetivo global 1 mV, dominio exponencial 45 y norma kernel 4096.
Python y sus hijos usan -B y política explícita de enteros sin límite textual.
Laboratorio nominal/sintético offline: cobertura completa, 1 mV global,
identificación física, voz, audio y deadline permanecen abiertos.
