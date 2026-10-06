# Volver a la voz monolítica con el solve refinado

2026-10-06. Siguiente banco, todavía no medido. Parte de la
[admisión local del VCO mínimo](NEWTON_REFINAMIENTO_RESULTADOS.md), que
no cierra por sí sola la unión o un puerto con retorno PWL.
Preservar builds/recibos y usar build08, tres correcciones sin cambios.
El runner local debe fijar SHA del candidato y runtime; el runner oficial
permanece intacto. Flags de observación/replay/fila equivalente apagados.

## Orden y gates

1. Control monolítico nominal con contorno fijo 2 V: reconstruir su deck
   por identidad, conservando VCO1, R6/R45, filtro, ambos VCA y salida.
   Ejecutar build06 original y build08 apagado; exigir mismo reloj y
   observables. Ejecutar build08 activo, 40 ms completos. Comparar DC y
   los observables comunes con los gates previos: voltajes DC ≤1 µV,
   grilla absoluta 5 µs ≤5 mV, frecuencia ≤1 cent, igual cantidad de resets
   y máximo desfase ≤10 ns; sin realineación. Conservar toda frontera
   ideal original. Si falla identidad/cobertura/gates, detener el banco.
2. Sólo si pasa, medir de nuevo las cuatro escenas del
   [protocolo monolítico](CONTORNO_VCO_UNION_PROTOCOLO.md), con contorno
   físico cargado y sin Vmixer/VF4_contour. Conservar sus decks originales
   por SHA salvo export y entorno del runner. Gear2 500/250/125 ns y
   Trap2 125 ns, 40 ms, mismas tarjetas/trims/teclado y tolerancias.
3. Exigir las cuatro trayectorias completas y los tres contrastes ya
   congelados: frecuencia ≤1 cent; C2, contorno, BUS, recuperación y salida
   ≤5 mV en grilla de 5 µs; RMS por ventanas ≤1% + 10 µV; balance acumulado
   de ambos C2 ≤0.1 nC. Reutilizar validadores y no confundir cobertura
   con concordancia entre políticas. Si una escena rechaza, conservarla
   y declarar no medidos los contrastes que necesiten esa cobertura.

Fijar 900 s de presupuesto por proceso antes de medir, por el tamaño mayor
de la matriz. No incrementar itl4 ni aflojar reltol/abstol/vntol/gmin o pasos.
Conservar timeout separado de aborto numérico. Comparar clocks/exports/logs
y fuente/build/runtime antes/después; exit code cero no admite un TRAN.

El método directo vuelve a resolver la red monolítica. Las iteraciones
anteriores divididas en R45 permanecen rechazadas; no se hereda su supuesto
cierre a este banco ni se cuenta la PWL del VCO mínimo como contorno físico.
Una admisión de 40 ms sólo permite extender después duración/Note On/Off;
todavía no autoriza crear audio extendiendo un prefijo o repitiendo ciclos.
Contorno de filtro, alimentación compartida, Q21 real, otras fuentes,
tarjetas identificadas y portabilidad/RT siguen fuera de ese alcance.
