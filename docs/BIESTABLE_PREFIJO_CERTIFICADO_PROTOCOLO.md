# Protocolo: prefijo contiguo con memoria saliente certificada

Modelo, parámetros y datos históricos intactos. Partir del intervalo
certificado seleccionado [1,2] del banco anterior; heredar su métrica,
memoria final y error nodal, no la caja DC. Intentar como máximo ocho
intervalos adicionales de los endpoints reales publicados (rows 1..8).
Detener el prefijo en el primer intervalo sin cierre. Conservar todos
los radios y modos de cada intervalo intentado antes de elegir.

## Reloj, reconstrucción e interfaces

Usar tiempos absolutos reales positivos y h=t_end-t_start exacto.
No trasladar relojes a cero ni fabricar historias. Verificar que current
anterior coincide con previous del endpoint. Reconstrucción: potenciales
94 y cargas lineales 21 afines, junturas Q(v)/S y tasas C(v)*v'. Comprobar
94 potenciales, 21 memorias y cuatro voltajes de juntura en la interfaz;
Q es continua con la misma ley. Registrar hashes de estado y reloj.

## Banco y recintos

Radios fijos 0,1; 1; 10 µV. Si la cota nodal entrante no cabe
estrictamente, conservar rechazo previo sin afirmar que el error real
esté fuera. Modos por radio: métrica cuadrática retenida, nueva métrica
cuadrática del casco de ocho generadores. Registrar rechazo de candidato
no PD y de recinto no invertible. Seleccionar el primer par aceptado.

Ocho celdas por intervalo. Precondicionadores binary64 candidatos H119
Decimal100 en cada punto medio, uno por celda reutilizado entre radios.
Escalas de tasa 2^-30 s. Envolver coeficientes sobre el tubo completo,
certificar defecto q<1 e inversas ideales por fórmula anterior, con SHA
completo. Residual constitutivo grado seis con resto exterior y ocho
subceldas internas. Consultas Decimal100 en u=0,1/2,1 sólo diagnósticas.

## Puente exacto de normas y propagación

Retener P conserva exactamente su norma (factor uno). Para nueva P,
encerrar alpha tal que alpha*P_old-P_new sea PD mediante LDL racional:
seed inferior máximo de Rayleigh diagonal, superior
||P_old^-1*P_new||inf+1, 32 bisecciones; guardar 33 consultas y prueba
final. Factor exterior = normal_old/normal_new*sqrt_upper(alpha), donde
normal=2a. Esto convierte la cota cuadrática directamente, evitando
pasar por una caja de coordenadas. Ambos P y normalizaciones deben ser
válidos. No interpretar un factor <1 como reducción del error físico.

Sumar memoria final del anclaje y forcing anteriores, convertir únicamente
el bloque de junturas y usar esas seis cotas como entrada realmente
conocida. La cota nodal entrante es el pico certificado del intervalo
previo (conservador). Mantener métrica constante en las ocho celdas y
pagar conversiones completas de acoplamiento, forcing y salida. Cotas
isotrópica/dirigida/balanceada se intersectan sólo en la misma métrica.

Cerrar sólo si el presupuesto nodal completo, origen incluido, es
estrictamente menor al radio y todos los recintos medios son invertibles.
Heredar la continuación implícita y el dominio del protocolo anterior.
La memoria de un candidato rechazado nunca se usa en el siguiente tramo.
Registrar duración intentada, duración realmente certificada, último
endpoint y primer hueco. Una parada conserva la prueba anterior intacta.

Validar sucesión no lineal conocida y puente con métricas exactas simples,
identidad, cambio de normalización, índices/tiempos reales, continuidad,
transferencia de memorias, todos los recintos y cierres. Verificar que
un rechazo corta la cadena y no reinicia DC. Congelar fuentes antes de
medir, datos/tests antes de validar, conservar intentos y ampliar corpus.
1 mV global, hardware, audio y deadline siguen separados.
