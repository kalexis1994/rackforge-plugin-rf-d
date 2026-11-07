# Aislamiento de picos en la salida NVIDIA

2026-11-07. Mantener la salida física `High Definition Audio 1/2`,
RackForge `37e5f803` y los paquetes O3 con LTO admitidos por
las reservas y el FIR. El driver recibe silencio. Verificar
el mismo fixture de 2048 muestras antes de medir.

Cambiar sólo la espera del supervisor durante el stream.
El supervisor espera un evento con un límite de 25 s.
El último callback señala el evento y el coste de esa
señal queda dentro de la medida de pared. Mantener la
condición previa del 85 % de inactividad global y 90 %
en el par SMT elegido, los marcadores de ciclos, el
reloj, la afinidad y la preparación del primer callback.
[Eventos de Windows](https://learn.microsoft.com/en-us/windows/win32/sync/event-objects)

Exigir un control silencioso de 1200 callbacks y dos
pases físicos independientes de 4800 a 48 kHz, todos
con 128 frames efectivos, alternancia y avance de reloj.
Aplicar el umbral de medio período (1,333333… ms) a
cada callback, incluida la preparación del primero.
Mantener los requisitos de plazos, avisos, errores,
intervalos, asignaciones y fallos de slot. Conservar
el resultado de todos los pases.

Después de los pases físicos, repetir la misma secuencia
de 4800 renders con un temporizador y afinidad a CPU 8,
que ejecutó los pases NVIDIA previos. Comparar los mismos
ordinales, sus ciclos y el tiempo dentro de la llamada
al motor. Este contraste permite comprobar recurrencia
por bloque. El tiempo dentro de una llamada puede incluir
interrupciones del hilo.
[Banco físico previo](RECOVERY_ENGINE128_PHYSICAL_RESULTADOS.md)

Si la primera pareja con evento excede el margen, repetir
el control y los dos pases fijando CPU 8. Es la CPU elegida
en el sondeo O3 anterior y en los pases NVIDIA de referencia.
Para cada apertura exigir cuatro ventanas de 250 ms con al
menos 90 % de inactividad global y 95 % de ciclos ociosos
relativos en ambos hermanos del núcleo 8/9. Mantener la
espera por evento y el mismo criterio de aceptación.
[Sondeo O3](../evidence/recovery_engine128_schedule04.json)

Si el requisito global del 90 % impide abrir los bancos,
repetir con el 85 % global de la campaña anterior y
conservar el 95 % relativo del par 8/9. Registrar ese
cambio de condición previa y mantener todos los límites
de las capturas físicas.

Si el control y uno de los dos pases fijos cumplen, repetir
una vez la campaña completa con la misma condición previa,
la misma CPU y los mismos paquetes. Guardar ambas campañas.
La admisión exige dos pases de la misma campaña y su control.

Si las dos campañas fijas dejan su segundo pase dentro
del margen y el primero fuera, añadir un pase previo
de 4800 callbacks con el paquete DSP tras el control
silencioso. Es una prueba del orden del banco. Conservar
las métricas del pase previo y exigir que confirme el
reloj físico sin plazos perdidos, intervalos excesivos,
avisos, errores, asignaciones ni fallos de slot. Aplicar
el límite de pared al control y a los dos pases de
confirmación que siguen. Cada pase se abre en su propio
proceso y conserva la preparación del primer callback
en la medida.

Si el pase previo no reproduce el margen en las dos
confirmaciones, probar la CPU 9 del mismo par SMT con
la política fija de 85 % global y 95 % en el par, sin
pase previo. Comparar el control y dos pases nuevos.
La consulta de interrupciones por CPU fuera del stream
orienta esta elección. Su resolución temporal no permite
asignar una interrupción a un callback concreto.
