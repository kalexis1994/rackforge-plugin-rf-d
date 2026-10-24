# Refinamiento del oráculo ante el rechazo Gear125

2026-10-24. El primer KCL rechazaba exclusivamente el OP en t=0:
.ic impone BUS con corriente de capacitor cero. El diagnóstico conserva
ese punto y acredita el transitorio posterior bajo el mismo límite. Se
aplica el gate a la ventana tardía declarada, sin modificar 1e-10 A.

Tres escenas pasan Gear2/125 ns; -1.6/L1 aborta a 11.277 ms por timestep
mínimo, con replay. No es trayectoria de 30 ms admitida. Probar sólo las
variantes ya previstas Gear2/62.5 ns y Trap2/125 ns en esa escena,
misma condición inicial, componentes, duración y errores. Capturar fallo
antes de otra decisión. Si una variante completa y pasa, se puede usar
en la continuación de ese escenario y conservar la variante rechazada.
Los tres ciclos válidos anteriores se reusan sin copiar ventanas.

El mensaje de Q7 no identifica por sí solo causa física ni inexistencia
de solución. No reducir C27, cambiar su conexión o suavizar dispositivos
para que un solver complete. Log/deck/fuentes y replay permanecen;
el prefijo parcial del aborto anterior fue retirado sin digest, y no
se promete reanalizar sus estados. Nuevos intentos guardan tamaño/hash
del export aun si la simulación aborta.
