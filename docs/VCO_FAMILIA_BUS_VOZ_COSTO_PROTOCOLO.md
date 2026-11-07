# Coste y conmutación de la voz cargada

2026-11-07. Usar las dos historias H128 validadas, con el
mismo solver de etapa, curvas BUS/CV, cargas HIGH/LOW,
voltajes de control y eventos de KEY. Perfilar por separado
el armado de etapas completas, el residual sin Jacobiano y
la resolución lineal. Incluir una ventana alrededor de la
conmutación de la reserva positiva.
[Reservas de partida](VCO_FAMILIA_BUS_VOZ_RESULTADOS.md)

Para concentrar trabajo donde cambia el circuito, comparar
un paso Radau con dos medios pasos. Evaluar los 118 estados
y la fase al mismo reloj. Usar como límite de defecto local
2 nV más 2e−10 de la tensión y 1e−11 ciclos. El defecto
divide la diferencia observada directamente por el límite.
Aceptar los dos medios pasos y sus cargas. Ante rechazo,
mantener la historia anterior y dividir el intervalo por dos.
Mantener Newton a 1 pA y 2 nV en todas las raíces. No
cambiar los coeficientes de carga, contactos o umbrales del
modelo físico.

Usar intervalos diádicos hasta 2,604167 µs, con fronteras
en todas las muestras y cambios de KEY. Reducir como máximo
hasta dos unidades de una rejilla de 65536 unidades por
muestra. Aumentar la propuesta tras aceptar si el defecto
es menor que 1/16 del límite. Registrar pasos, intentos,
defecto y tiempo con la instrumentación interna desactivada.

Contrastar los 129 relojes de cada reserva con su referencia
fina de 64 o 512 subpasos por muestra. Exigir el mismo
límite nodal de 20 µV + 2e−6·|V|, corrientes R59/R60
de 2 nA + 2e−5·|I|, RMS relativo J7 de 0,001, pico
relativo de 0,003 y media de 1 µV. Repetir el contraste
de cargas, C27 y derivadas de BUS en etapas reservadas,
incluida la liberación. La inversión del orden de los
colectores Q25/Q15 identifica la conmutación de volumen
para medirla. Comprobar su sentido, cantidad y muestra de
ocurrencia con la referencia, junto con el par del filtro.
La observación de los colectores no gobierna la simulación.

La medida local del solver tiene alcance de laboratorio.
Volver al banco físico sólo cuando se conserven las
reservas y el coste observado deje margen para el host.

## Reutilización de una corrección ya evaluada

Comparar con los pasos fijos aceptados de 64 y 512
subpasos por muestra. Cuando el line search ya calculó
el residual y la corrección de Newton del candidato
aceptado, devolver ese candidato si satisface ambos
límites y queda una iteración presupuestada. Es el mismo
resultado que habría devuelto la iteración siguiente
con el mismo recuento. Mantener todos los rechazos,
las bisecciones y los criterios de Newton y Schur.

En este banco x86-64, habilitar FMA para que las llamadas
explícitas a `f64::mul_add` del residual compensado usen
la instrucción de hardware. Comprobar disponibilidad
antes de ejecutar el candidato. Mantener la semántica
de una multiplicación y suma con un solo redondeo.

Exigir igualdad binaria con la referencia en los 129
relojes, las corrientes de retorno y la fase, junto con
las mismas iteraciones y bisecciones. Registrar todas
las inversiones de los colectores en los extremos de
cada paso aceptado y contrastar sus intervalos y sentidos
con un control fijo recompilado. Incluir la etapa de
cada inversión en la auditoría del stamp denso. Medir
ambos programas con GNU O3 y las mismas dos historias.
