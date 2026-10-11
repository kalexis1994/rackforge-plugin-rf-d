# Derivada local del cruce y estado en fase

Protocolo previo, 2026-10-10. Model D clásico CA3046, misma escena,
biblioteca y ocho ventanas reset admitidas. Sólo laboratorio.

## Observación diferenciada

El evento observado es el interpolante lineal de la rampa 43 que cruza
-2 V en sentido creciente entre dos endpoints realmente aceptados.
No se identifica ese interpolante con un evento continuo exacto del circuito.
En cada ventana se reproducen los dos primeros pasos y sus HIGH/LOW por bits.
Se toman las nueve direcciones/epsilon ya fijadas para la ventana completa
en el banco anterior. No se elige una escala después del resultado.

Con endpoints A/B, rampas a/b y duración h del bracket:

`alpha=(-2-a)/(b-a)`

`dalpha=-[(1-alpha) Sa[43]+alpha Sb[43]]/(b-a)`

`dt=h*dalpha`

`Z=(1-alpha) A+alpha B`

`dZ=(1-alpha) Sa+alpha Sb+(B-A)*dalpha`.

La última suma incorpora el cambio de tiempo/fase. Las rampas del detector
usan HIGH+LOW redondeado a binary64, como las trazas históricas. El estado
interpolado usa diferencias compensadas HIGH/LOW. Las tangentes son las
derivadas físicas evaluadas a primer orden, no de cada redondeo del codec.
El tiempo se compara como desplazamiento relativo al inicio del bracket;
no se resta el reloj absoluto de milisegundos para medir cambios sub-ps.

## Pruebas y gates

Ocho eventos × nueve direcciones. Cuatro historias propias por dirección
(±epsilon, ±epsilon/2), dos pasos cada una: 576 solves no lineales nuevos.
Cada historia debe mantener a<-2≤b, denominador positivo y 0≤alpha≤1.
Guardar ambos endpoints completos de cada signo/tamaño, alpha y estado
interpolado: el auditor reconstruye las diferencias, no confía en FD exportado.

El oráculo reconstruye masa y Jacobianos de ambas etapas de los 16 pasos
con el mismo camino independiente Decimal100/gradiente de cadena del banco
anterior, propagando sus propias respuestas. Calcula alpha/dalpha/dZ en
Decimal100 y contrasta todos los estados y nueve direcciones.

Gates de cambio: estado 1e-8 V / 1e-11 A + 1e-4 relativo;
tiempo 1e-17 s + 1e-4 relativo. Para alpha, convertir el mismo gate de
tiempo por h. Los gates de estado/Newton heredados no se amplían.
Estado base/perturbado interpolado y alpha deben coincidir con el oráculo
a 1e-13 V / 1e-16 A y 2e-15 respectivamente. La sección interpolada debe
quedar a -2 V con error≤1e-13 V. La respuesta de rampa escalada debe anularse
con error≤1e-18 V. Control algebraico 98: respuesta y tiempo exactamente cero.
Control positivo 43: sin término de tiempo la respuesta de rampa debe
superar el gate de estado; con proyección debe pasar.

## Recursos y admisión

Campaña compacta: estimación 16 MiB, reserva 512 MiB, vigilancia 250 ms,
pila 32 MiB. Compilación≤120 s, ejecución≤300 s, total≤480 s. Esta reserva
es propia de este banco de 576 solves/outputs acotados; los recibos anteriores
y sus reservas de 1 GiB conservan su admisión histórica y bytes. No se borra
ni comprime evidencia. Guardar fuentes, parciales y replay antes de reparar
un rechazo. Verificador≤300 s, sin nuevos procesos SPICE ni audio.

Se admite únicamente la derivada de este observador interpolado y sus
estados en fase, respecto de la historia inmediatamente anterior al bracket.
No es un Jacobiano del periodo completo, una saltación de un sistema híbrido,
una derivada del calendario adaptativo, memoria periódica ni fidelidad física.
