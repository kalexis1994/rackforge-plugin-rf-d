# Refinamiento temporal por movimiento del biestable

2026-11-07. Probar el reloj local con el núcleo H128 de
filas activas y la misma historia HIGH/LOW de ambos
contornos. Cada aceptación conserva las dos etapas de
Radau, Newton a 1 pA y 2 nV, y sus corrientes y cargas.
[Reservas finas](VCO_FAMILIA_BUS_VOZ_RESULTADOS.md),
[Control nativo](VCO_FAMILIA_BUS_VOZ_LATCH_LU_RESULTADOS.md)

Usar 4096 unidades por muestra a 48 kHz. Los pasos son
diádicos y terminan en las fronteras de muestra y KEY.
Probar techos de 32, 64, 128 y 256 subpasos por muestra.
Para un paso mayor que el de 512, medir el movimiento
máximo de los cuatro colectores de ambos biestables
desde el estado aceptado hasta cada etapa Radau. Dividir
si supera VT/32, aproximadamente 0,80 mV para la
temperatura del modelo, o si cambia su orden. VT es
el del modelo de junturas, y su fracción es una regla
numérica de resolución. Los pasos de 512 se aceptan con
las reglas de Newton. Una falla recuperable de Newton
permite dividir hasta una unidad sin publicar el ensayo.
Tras aceptar, duplicar la propuesta si el movimiento
fue menor que VT/128. Limitar cada propuesta al techo
y a la alineación de su frontera.

Contrastar los 129 relojes con las referencias finas de
64 y 512. Mantener los límites de 20 µV + 2e−6·|V| en
los nodos, 2 nA + 2e−5·|I| en R59/R60 y los límites de
J7 de 0,001 RMS relativo, 0,003 pico relativo y 1 µV en
la media. Exigir fase dentro de 1e−7 ciclos y el mismo
intervalo fino y sentido de toda inversión de colectores.
Repetir el contraste denso, C27, puerto, R21 y el
Jacobian cargado en las etapas reservadas, incluida la
inversión. Conservar candidatos rechazados y su replay
sin cambios.

Elegir el techo más grueso que pase por rama. Comparar
con un control fijo fresco y repetir la variante elegida
en CPU lógica 9. Mantener la medida de laboratorio
separada de los dos pases físicos de 128 frames, que
requieren margen de 1,333 ms.
