# Auditoría eléctrica de la nota extendida

Antes de auditar, conservar los gates originales de 119 filas: residual
<=20 pA y corrección completa <=2 nV. Misma referencia independiente Amount,
misma estrella resistiva VCO y cargas originales. No auditar el FIR como
si fuera parte del circuito ni estados escalares interpolados como raíces.

Auditar DC propio desde ambas aproximaciones y los 24 pares guardados de
cada perfil largo: primer paso, antes/después de KEY ON, frontera de 75 ms,
antes/después del nuevo KEY OFF a 200 ms, 300 ms y soporte final 301 ms.
Son 48 pares, 96 etapas y 11424 filas dinámicas, más 238 filas de DC.
Comprobar empalmes HIGH/LOW en DC→primer paso y ambos eventos de KEY.
No se integra una segunda trayectoria original: se auditan etapas ya
admitidas por el motor y se declara esa distinción.

El adaptador reutiliza el auditor de arranque sin cambiar ecuaciones:
sustituye sólo el parser por el formato largo y deriva los conteos de los
pares efectivamente auditados. Conservar fuentes e inputs, error y replay
sin cambios ante un fallo. Este alcance amplía el horizonte numérico;
no valida parecido con una unidad física ni presupuestos de tiempo real.

## Control negativo de alias previo al FIR

Además de los estímulos fijados en el protocolo, inyectar un coseno de
180 kHz a ambas tasas antes de medir este control. A 192 kHz se pliega a
12 kHz antes del FIR: exigir pico de salida >0,99 para demostrar que el
filtro ya no puede quitarlo. A 384 kHz sigue fuera de banda: exigir salida
<=10^(-90/20). Conservar también el bypass de 30 kHz que se pliega a
18 kHz al reducir a 48 kHz. Son controles de límites del conversor, no
estímulos atribuidos al Moog o una modificación del circuito.
