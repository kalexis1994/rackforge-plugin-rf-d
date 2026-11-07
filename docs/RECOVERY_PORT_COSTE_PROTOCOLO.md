# Resolver las mismas doce leyes con menos trabajo

Previo al banco nuevo, 2026-11-06. El primer solve12 de dos etapas conserva
su banco original:1200/1200 deadlines perdidos, mediana3.5792 ms, cero heap.
No cambiar frecuencia, FIR, entrada, gates o constitución para corregirlo.

Probar Newton modificado: Jacobiano aproximado con las seis derivadas BE,
resolver su bloque6 y recuperar las seis correcciones BC por sustitución.
Evaluar SIEMPRE las doce leyes BE/BC en el residual y exigir el mismo
2e-13 adimensional para devolver una etapa. Esto no elimina corrientes BC
ni equivale a declarar su valor cero. Cambia el precondicionador; podría
perder convergencia fuera del dominio. Conservar el rechazo atómico y el
presupuesto12, guardas previas y límites de entrada.

Regresión1537 pasos por cada DC contra Python12/fullNewton, <=1e-10 V,
<=1e-14 A, cargas<=1e-11 V y puertos por bits. Rechazos/retry/heap como
antes. Banco nuevo1200 bloques, primer bloque incluido y latencia FIR
explícita80/128 frames. Publicar también cualquier fallo de este banco.
No seleccionar la mejor repetición ni transferir tiempo real a la voz.
