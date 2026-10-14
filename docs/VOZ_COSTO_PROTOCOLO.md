# Costo de la voz integrada y optimización conservando el circuito

Protocolo previo, 2026-10-14. Base: voz admitida de 250 incógnitas y 8 ms,
con ambos contornos, VCO real y BUS cargado. Mismos dispositivos, controles,
cargas, método Radau, gates de Newton/LTE y representación high/low.

Medir primero Parts y solución lineal sobre las 24 parejas seleccionadas
de las dos trayectorias admitidas. Repeticiones explícitas, calentamiento y
orden alternado; tiempos del laboratorio no son deadlines de audio.
No extrapolar una matriz inicial a todas las fases del oscilador.

Elegir una intervención a partir de los costos medidos. Reordenar una
factorización conserva todas las filas, columnas y coeficientes, sin
truncar valores pequeños. La matriz observada puede sugerir un orden;
no define una máscara que autorice omitir entradas futuras. Conservar
guardas de estructura y residual lineal 1e-11. Registrar mapas y fuente.

Antes de admitir: Parts idénticos por bits si no se cambian sus operaciones;
direcciones contra solver anterior, fracción de corrección ≤1 con 2 nV/2 pA;
parejas y candidatos completos, con el mismo Newton y estados anteriores.
Contrastar trayectoria completa de 8 ms en dos resoluciones al mismo reloj:
20 uV + 2e-6 |V|, slots de corriente 2 nA, cargas R59/R60 2 nA + 2e-5 |I|.
Conservar arranque DC y balance BUS ≤20 pA. Auditor eléctrico original
de 251 nodos para parejas nuevas seleccionadas, con gates anteriores.

Si mejora el costo, extender una trayectoria desde su estado final real;
duración y contactos explícitos, sin concatenar ni repetir ciclos. Una
extensión finita debe completar su propio reloj y refinamiento antes de
presentarla como historia nueva. Priorizar duración útil; no añadir una
familia de certificados locales que postergue ese objetivo.

Límites: ≥1 GiB libre, ≤32 MiB nuevos, compilación ≤120 s, perfil/escena
≤600 s, auditor ≤300 s. Conservar fuentes/datos/fallo y replay sin cambios
antes de reparar. No Cargo ni recompilación de rlib congelada. Sin admisión
de fidelity física, MIDI, heap/deadlines o tiempo real por este banco.
