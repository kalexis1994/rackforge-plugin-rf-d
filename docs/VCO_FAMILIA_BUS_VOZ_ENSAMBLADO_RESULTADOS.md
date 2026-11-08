# Ensamblado conjunto de las dos etapas Radau

El banco usó la voz H128 a 48 kHz, CV de placa fijo a
−1,6 V y el solver de filas activas con carga de junturas
validada. Se mantuvieron los mismos historiales, pasos
y eventos de KEY.
[Protocolo](VCO_FAMILIA_BUS_VOZ_ENSAMBLADO_PROTOCOLO.md)

El ensamblador lee una vez cada fila fuente y construye
las contribuciones de las dos etapas. Los cursores del
almacenamiento disperso avanzan desde extremos opuestos
y comparten 4096 entradas. La lectura recupera el mismo
orden de columnas y de sumas por fila, con los cuatro
puertos de Schur y el mismo LU.

## Reservas

Cada una de las 15 auditorías reconstruyó la matriz
cargada de 236 × 236. Coincidieron bit a bit las
835.440 entradas comparadas, incluidos los ceros de
la representación densa. El caso sintético también
conservó soportes distintos por etapa y la cancelación
de un coeficiente del bloque diagonal. El exceso de
capacidad y el producto no finito dieron el mismo
rechazo y el mismo resultado válido al reutilizar el
workspace.

Ambas reservas reprodujeron los 129 relojes bit a bit
en los estados HIGH/LOW, la fase, J7 y los retornos
R59/R60. La inversión del biestable de volumen mantuvo
su sentido y el intervalo entre 77,904296875 y 77,90625
muestras. El orden de los colectores del filtro se
mantuvo. Pasaron las auditorías de KCL, C27 y R21 y las
direcciones con excitación separada de ambos retornos.

## Coste del solver

| Reserva | Control | Variante | Diferencia |
| --- | ---: | ---: | ---: |
| Positiva, 512 subpasos por muestra | 38,700 s | 36,856 s | −4,8 % |
| Negativa, 64 subpasos por muestra | 4,995 s | 5,004 s | +0,2 % |

Un recorrido de 128 muestras por variante, con CPU
lógica 9 y reloj de pared alrededor del solver. En la
rama positiva, el tiempo de CPU del hilo, que incluye
auditoría y registro, bajó 4,1 %. La medida de CPU de
la rama negativa coincidió a la resolución del contador.

El perfil alternado separó ensamblado, factorización y
resolución completa. En la rama positiva, las medianas
del ensamblado subieron 1,6 % antes de la liberación,
bajaron 1,7 % durante la liberación y bajaron 0,6 %
después. La diferencia del bloque completo describe
ese recorrido. La mejora del ensamblado por ventana
quedó sin confirmar.
[Recorrido conjunto](../evidence/vco_family_voice_bus_scatter01.json)

## Emisión de filas por bits

La segunda prueba conservó las mismas matrices y
trayectorias. El fixture alcanzó 4096 entradas después
de rechazar una fila y cancelar un par. Coincidieron
el orden de columnas y los bits de una derivada cero
con signo al lado de masa no nula.

En la rama positiva, el bloque completo subió de
46,794 a 56,377 s en pared y 13,7 % en tiempo de CPU
del hilo. En la negativa pasó de 5,803 a 6,008 s.
El perfil de la etapa completa durante la liberación
subió 13,6 %. También aumentó la duración de secciones
sin cambios de aritmética, como la factorización. El
contraste registra la regresión de esta variante en
el banco y deja abierta su causa.
[Emisión por bits](../evidence/vco_family_voice_bus_scatter02.json)

Los dos cambios quedan en el laboratorio. El recorrido
conjunto aporta una observación favorable de coste
en la rama positiva, con resultados dispares en la
sección de ensamblado. Se conserva el control de filas
activas. Los pases físicos quedan pendientes porque el
coste supera el margen de 1,333 ms. Se retiraron los
binarios y tablas temporales.
[Auditoría](../evidence/vco_family_voice_bus_scatter_tests01.json)
