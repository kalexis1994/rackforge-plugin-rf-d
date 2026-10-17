# Reserva BUS=0 y resolución de su representación

Decisión tras fallo/replay de model_failure01. Los tres CV intermedios
nuevos pasan los gates. El primer BUS=0 archivado produce 32.0 nA DC y
90.6 nA armónicos de diferencia de panel al integrar su cycle_v de 1025
puntos; el límite previo sigue en 2 nA. Esa representación coarse no
conserva el reset denso de los exports retirados. No ampliar el error
de aceptación ni ajustar la familia con estos puntos.

Regenerar cuatro oráculos BUS=0, con los CV archivados exactos -3.1+i,
Gear2/125 ns, 30 ms, mismos trims y circuito; guardar salida binaria.
Mismos gates 1 cent/5 mV/2% y 2 nA de panel. La generación de la familia
sigue con los ocho entrenamientos intactos. Los nueve contrastes reservados
de alta resolución serán cuatro BUS=0, tres CV intermedios y dos métodos
adicionales del mismo lugar. Siguen siendo siete lugares independientes.
Las cuatro tablas antiguas sólo contrastan frecuencia/forma bajo sus gates
originales, no corriente a precisión que su representación no preserva.

Este refinamiento del oráculo escribe sólo time, ramp, schmitt, saw,
triangle, pulse, wiper e i(Vmixer). Preservar todo su último ciclo exacto
con contexto, digests del export completo, cruces y coeficientes Fourier
0..64 por integración exacta lineal por tramos. No se exportan corrientes
CV ni Qa/Q10 en estos cuatro recorridos: esos gates conservan los tres
lugares nuevos/two métodos y las referencias anteriores. No atribuir al
export reducido el archivo de todos los estados del circuito.

La fila sum/NEG4/Qa/Q10 de este oráculo de salida no se usa como referencia.
Mismo tmp/lab-current y presupuestos 256 MiB/180 s/1 GiB. Recibos totales
<=32 MiB sin QA. Archivar recibos JSON sin pérdida cuando sea necesario,
reconstruyendo exactamente los bytes y hashes originales; no copiar ventanas
de entrenamientos o reducir su precisión. Mantener falla/replay anteriores.
