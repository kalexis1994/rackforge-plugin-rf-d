# Armado de etapas y LU de la voz cargada

Continuaciones a 48 kHz, con CV de placa fijo a −1,6 V.
Control recompilado con reutilización de Newton y FMA.
Se mantienen el reloj, las historias HIGH/LOW, los
eventos de KEY y los cuatro puertos de Schur.
[Protocolo](VCO_FAMILIA_BUS_VOZ_ARMADO_PROTOCOLO.md)

## Primera prueba

Emitir filas en orden físico y permutar los índices del
LU dio las mismas reservas, pero la combinación elevó el
tiempo para 128 muestras de 5,925 a 6,300 s en la rama
negativa y de 43,115 a 45,642 s en la positiva. El
perfil separado también midió más tiempo en la sección
de armado completo para la emisión ordenada y en la
sección lineal para la permutación. Se descartaron por
coste y se conservan los tres recorridos cortos de cada
variante y los recorridos completos.
[Primer recibo](../evidence/vco_family_voice_bus_hot01.json)

## Variante con representación ligera y LU contiguo

La búsqueda lineal devuelve corrientes, cargas, estados y
fase sin transportar dos tangentes vacías. Comparte las
leyes y la aritmética de BUS con la etapa completa. El LU
omite intercambios de una fila consigo misma y actualiza
los mismos coeficientes de los tramos contiguos, con
pivotes, aritmética y límites de refinamiento conservados.

En ambas reservas se conservaron bit a bit los 129
relojes, incluidos los 118 estados HIGH/LOW, la fase,
J7 y los retornos R59/R60. Quince auditorías reservadas
compararon ambas etapas de cada paso, incluido el de
conmutación. Coincidieron el residual, las filas de
carga, el Jacobiano cargado y las correcciones de
Newton y de los dos retornos excitados por separado.
La inversión del biestable de volumen quedó entre
77,904296875 y 77,90625 muestras en el mismo sentido.
El orden de los colectores del filtro se mantuvo.

| Reserva | Subpasos por muestra | Control | Variante | Ahorro |
| --- | ---: | ---: | ---: | ---: |
| Negativa | 64 | 6,022 s | 5,539 s | 8,0 % |
| Positiva | 512 | 43,841 s | 40,800 s | 6,9 % |

Un recorrido por rama y variante, sin instrumentación
interna y fuera del host. La variante queda en el banco.
Los dos pases físicos a 128 frames siguen pendientes
porque el coste excede el margen de 1,333 ms.
[Segundo recibo](../evidence/vco_family_voice_bus_hot02.json),
[auditoría](../evidence/vco_family_voice_bus_hot_tests01.json)

## Perfil separado

Medianas de tres recorridos por variante y ventana.
Todos los perfiles reprodujeron el punto final de la
referencia con el mismo número de evaluaciones y solves.

| Sección y variante aislada | Negativa | Positiva |
| --- | ---: | ---: |
| Búsqueda sin Jacobiano, control → ligera | 26,893 → 23,794 ms | 243,755 → 215,408 ms |
| Resolución lineal, control → LU contiguo | 83,248 → 74,940 ms | 664,483 → 597,779 ms |

Son sumas sobre ventanas de cinco muestras alrededor de
KEY y de la liberación. El cronómetro de la búsqueda
ligera incluye formar el vector residual, que queda
fuera de esa sección en el control. El contraste
completo de 128 muestras incluye ese trabajo en ambas
variantes. El recibo conserva las cuatro combinaciones
y los tiempos de armado completo por separado.
