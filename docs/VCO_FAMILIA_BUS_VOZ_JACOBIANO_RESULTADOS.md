# Jacobiano directo y eliminación de bordes en la voz cargada

Continuaciones de la voz H128 a 48 kHz, con CV de placa fijo
a −1,6 V y las mismas historias, pasos y eventos de KEY.
El control conserva la búsqueda lineal ligera, el LU
contiguo, la reutilización de Newton y FMA.
[Protocolo](VCO_FAMILIA_BUS_VOZ_JACOBIANO_PROTOCOLO.md)

El Jacobiano de audio se estampa en el bloque de 68 nodos
de la etapa cargada. Se elimina la copia intermedia de
66 × 66. Las ecuaciones de R21, BUS y C10, los incrementos
de carga y la incorporación de ambos contornos conservan
sus operaciones.

En el LU de interiores se conserva el factor con su signo
y se omiten las restas en bordes sólo si vale cero. Bajo
redondeo al más cercano con subnormales, un borde sin
eliminar sólo puede tener +0 si vale cero. Restarle un
producto ±0 conserva el coeficiente. Se mantienen los
pivotes y los controles de finitud.

## Reservas

Coincidieron bit a bit los 129 relojes de cada reserva,
las 118 coordenadas HIGH/LOW, la fase, J7 y los retornos
R59/R60. La inversión del biestable de volumen permaneció
entre 77,904296875 y 77,90625 muestras en el mismo sentido.
El orden de los colectores del filtro se mantuvo. Las 15
auditorías de pasos incluyeron la inversión y compararon
el Jacobiano cargado, el residual y las correcciones de
los dos retornos excitados por separado. Pasaron además
90 contrastes de etapa a 0, 2500 y 5000 Ω en R21.

El fixture lineal verificó cuatro direcciones bit a bit y
los mismos rechazos por overflow y singularidad. Cada
rechazo fue seguido de un solve válido en el mismo
workspace. El fixture usa matrices de prueba con pivote
intercambiado, bordes y ambos signos de cero.

## Coste

En tres recorridos alternados por variante y ventana,
ambos cambios aislados redujeron el coste de su sección
en cada par. Las medianas de etapa completa bajaron
8,6 % en la rama negativa y 7,6 % en la positiva. La
resolución lineal aislada bajó 1,5 % en ambas ramas,
con ahorros individuales de 1,1 % a 1,8 %.

| Reserva | Subpasos por muestra | Control | Variante combinada | Ahorro observado |
| --- | ---: | ---: | ---: | ---: |
| Negativa | 64 | 5,535 s | 5,270 s | 4,8 % |
| Positiva | 512 | 40,626 s | 38,470 s | 5,3 % |

Un recorrido por rama y variante para 128 muestras, sin
instrumentación interna y fuera del host. Una prueba
previa que acotaba las sustituciones pasó las mismas
reservas, pero su LU aislado mejoró 0,7 % en la negativa
y empeoró 0,3 % en la positiva. Se conserva ese contraste.
[Prueba con sustituciones acotadas](../evidence/vco_family_voice_bus_jacobian01.json)

La combinación de Jacobiano directo y bordes queda en
el banco nativo. El coste excede el margen de 1,333 ms
y los dos pases físicos siguen pendientes.
[Mediciones](../evidence/vco_family_voice_bus_jacobian02.json),
[auditoría](../evidence/vco_family_voice_bus_jacobian_tests01.json)
