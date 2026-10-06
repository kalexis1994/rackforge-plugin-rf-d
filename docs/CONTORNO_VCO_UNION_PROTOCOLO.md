# Unión VCO y contorno cargado: primer contraste

Fecha: 2026-10-06. Se unen los dos bloques ya contrastados: VCO1/mixer/
placa 4 y contorno de volumen cargado. Se conservan grafos, tarjetas,
trims y fuentes de los [resultados de contorno](CONTORNO_PLACA4_RESULTADOS.md).
No se hereda su admisión a esta interfaz. El generador copia exclusivamente
las ramas identificadas del contorno; no importa su fuente senoidal.

La fuente Vmixer y la de contorno VF4_contour desaparecen. La salida
real del VCO carga R6/R45/C27; el seguidor de contorno comparte nodo con
pin 9 de placa 4, con R59 y corriente de base Q18 resueltos. Se conservan
ambos VCA y la salida. No se imponen ondas, corriente de cola o estados
de fase ADSR. Alimentación 9.3 V, teclado ideal y base Q21 2 V siguen
como fronteras. Contorno de filtro y su carga de gatillos quedan omitidos.

Primer banco: cuatro escenas de **40 ms**, teclado 0→10 V a 2 ms,
OFF a 25 ms, transiciones 10 microsegundos. Controles eléctricos:
ataque 10 kohm, decay 100 kohm, sustain inferior 2500 ohm, decay final ON.
Trims/CV/cutoff iguales al nominal anterior. Gear2 con máximo 500/250/125
ns y Trap2/125 ns; KLU, bypass=0, itl4=100, reltol=1e-7, abstol=1e-13 A,
vntol=1e-8 V y gmin=1e-12 S. No se regulariza ningún capacitor o tarjeta.

Antes de medir: tres contrastes de frecuencia <=1 cent; máximo de C2,
contorno, BUS, recuperación y salida <=5 mV en grilla común 5 microsegundos,
sin alineación de eventos; RMS por ventana <=1% + 10 microvolt. Ventanas:
reposo 0.4–1.6 ms, ataque 2.01–25 ms y release 25.01–40 ms. Se exige
balance acumulado de ambos C2 <=0.1 nC durante toda la trayectoria.
Frecuencia se observa desde los resets posteriores a 2.01 ms.

Se exportan 18 observables suficientes para estos gates, sin alterar
ecuaciones. Escena completa, reloj finito creciente y fuentes estables son
obligatorios. Cualquier rechazo conserva deck, log, export parcial y recibo;
no se admite ni se alarga una trayectoria parcial por repetición de audio.
La extensión a notas más largas sólo procede si este banco completa y
sus tres contrastes pasan. La falta de dispositivos identificados, contorno
de filtro, otras fuentes, salida de auriculares y tiempo real se mantiene.
