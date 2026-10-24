# Restricciones algebraicas y salto de la fuente inicial

El diagnóstico posterior a los ciclos trapezoidales rechaza el balance
instantáneo: BASE_Q29+BUS carecen de carga en modo común y sus KCL deben
sumar cero. El DC de fuente media no satisface esa restricción con fase0.
Trapezoidal impone Fnew+Fold sobre el subespacio algebraico y conserva
un residuo alternante: 0.5243/0.2178 uA. La repetición sin cambios coincide
por bytes. Las raíces y refinamientos del método no bastan para admitirlo.

No cambiar elementos, fuente H128, historia C27 o gates para ocultarlo.
Probar SDIRK2 rígidamente estable, gamma=1-1/sqrt(2), stiffly accurate.
Cada etapa resuelve F(x)+DeltaQ/(gamma*h)=0 y la fase correspondiente;
por ello impone las restricciones algebraicas en esa etapa. Primera etapa
desde historia original; segunda desde la historia virtual
xold+(1-gamma)/gamma*(xstage-xold). Sólo se publica el endpoint final.
El flujo físico integrado es h*((1-gamma)*Istage+gamma*Iendpoint).
La historia virtual no es otro paso físico ni capacitor reinicializado.

Mantener los mismos controles, estados DC medios, pasos .5/.25 us y gates.
El punto inicial sigue siendo el salto especificado; desde la primera
etapa exigir |KCL_BASE+KCL_BUS|<=1e-13 A. Balance C27 con pesos SDIRK:
<=1e-16 C+1e-8 de throughput. El control negativo del trapezoidal conserva
su rechazo, no se reetiqueta como voz o ciclo admitido.

Repetir los doce DC y dieciséis raíces de subpaso BE69 contra el oráculo
independiente, incluidas las columnas BASE/BUS/fase. Después completar los
cuatro ciclos SDIRK de un período y su refinamiento. Ninguna comparación
comparte raíces como semillas; sí comparten las historias declaradas y
la familia H128. No es otro modelo VCO independiente.
