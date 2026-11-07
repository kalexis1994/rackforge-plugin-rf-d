# Extensión limitada al par de entrada

Previo a esta medición, 2026-11-06. El ensayo de recuperación sola conserva
sus seis rechazos de nivel: a=.1 V el peor error ya está en TAIL (nodo5),
no en recuperación. El siguiente incremento reemplaza también las dos
leyes Ebers–Moll del par Q29/Q30, sin calibrar parámetros con las reservas.
Stamp SVC-9 Fig.9-11 p.13: (base,collector,emitter)=(6,8,5),(7,12,5).

Se aplica la misma [derivación y gates](RECOVERY_PORT_PROTOCOLO.md), ahora
12 uniones de seis BJT.18 memorias físicas, mismo G/M/DC, puertos, retornos,
constantes, SDIRK y tres puntos fijos. No incluir más BJT ni cambiar gates
si las reservas siguen rechazadas. Contrastar64 perturbaciones nativas en
nodos5/6/7/16..23; los restantes dispositivos sólo ven perturbaciones en
conexiones resistivas o no cambian. Conservar el ensayo8 como control.

La implementación Rust será sólo de12 uniones; comparar1537 pasos en cada
punto con Python y medir1200 bloques con FIR. No interpolar nodos del
oráculo ni admitir una trayectoria a partir de sus condiciones iniciales:
todos los candidatos arrancan de su DC y reciben sólo entrada y reloj.
Separar constitución a250 ns de método a384 kHz mediante integración
parcial propia si se compara un reloj distinto. Si el método o coste
falla, publicar ese rechazo. La familia no admite cutoff dinámico ni la
voz completa, y la ausencia de hardware sigue limitando fidelidad externa.
