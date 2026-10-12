# Un ciclo del VCO con contorno cargado y apertura de S

2026-10-12. CA3046 condicionado, sin instrumento físico. Continúa
[ventana anterior](VOZ_CONTORNO_RESET_RESULTADOS.md) desde8.438 hasta11.442 ms.
Cada ON/OFF y máximo h2/1 µs conserva su propia historia,458 componentes,
reloj y siguiente propuesta. Reposo4 µs, S/KEY10 sostenido1.5 ms,
liberación1.5 ms. [Protocolo](VOZ_CONTORNO_CICLO_PROTOCOLO.md).

## Rechazo y reparación

[Campaña01](../evidence/voice_contour_cycle_native01.json) y su replay
rechazan en9.942 ms al abrir S: `PrecisionLimit(Nonlinear(IterationBudget))`.
C7 todavía conserva2.040774365856582 V. El predictor de apertura proponía
un estado algebraico incompatible con el otro camino de gatillo activo.
[Diagnóstico04](../evidence/voice_contour_cycle_diagnostic04.json) repite
el rechazo y rollback por bytes; la propuesta admite el mismo paso con
half16 ticks y LTE3.88214·10⁻⁷. Esto es evidencia de un paso aislado.

[Reparación declarada](VOZ_CONTORNO_CICLO_REPARACION.md): copia del kernel
con una sola condición adicional C7<0.1 V para usar ese predictor.
Umbral numérico de elegibilidad, no parámetro físico. Sin cambiar red,
cargas, ecuaciones, Newton, tolerancias ni controlador. La campaña02
conserva idéntico el prefijo aceptado de01 y completa los cuatro perfiles.
Fuentes históricas y fallo01 siguen archivados.

El auxiliar01/02 sobrescribía su kernel con el runner homónimo. Los stderr
originales faltan; [recuperación posterior](../evidence/voice_contour_cycle_aux_replay01.json)
compila dos veces la fuente sobreviviente y reproduce `circular modules`.
El intento03 además chocó con la escritura exclusiva del recibo.
Estos errores del auxiliar no se presentan como resultados eléctricos.

## Ciclo completo transitorio

Último reset anterior y primero nuevo delimitan un ciclo continuo que
atraviesa la unión exacta. Rampa43 cruza−2 V; los brackets y la interpolación
son observaciones. El calendario del contorno cambia durante ese ciclo.

| Final decay | h máximo µs | Periodo ms | Frecuencia Hz | Endpoints observados |
|---|---:|---:|---:|---:|
| ON | 2 | 2.434264003949 | 410.801785828 | 4820 |
| ON | 1 | 2.434264003949 | 410.801785828 | 5970 |
| OFF | 2 | 2.434263993465 | 410.801787598 | 4792 |
| OFF | 1 | 2.434263993465 | 410.801787598 | 5942 |

La frecuencia describe ese único ciclo transitorio de la voz con carga.
No identifica afinación de una unidad Moog ni periodicidad estacionaria.
El intervalo incluye señales VCO1/BUS/ladder/VCAs/J7 y contorno en el mismo
solve. Se unen OBS sin duplicar el reloj de la semilla y se contrastan
balances del recorrido combinado de6.008 ms. Extremos finitos de saw,
BUS/J7/C2/LOUDNESS quedan en el [oráculo](../evidence/voice_contour_cycle_reference01.json),
sin atribuirles cotas continuas entre muestras.

Finales del perfil h1 µs, fases0 reposo/1 sostenido/2 liberación:

| Final decay | Fase | C2 V | C7 V | J7 V |
|---|---:|---:|---:|---:|
| ON | 0 | 3.289637844280 | 1.143061574898 | 0.000210205868 |
| ON | 1 | 3.378134318893 | 2.040774365859 | 0.001589489475 |
| ON | 2 | 3.430662619921 | 1.667142004851 | -0.001223478229 |
| OFF | 0 | 3.045515593361 | 1.143061574898 | 0.000279405407 |
| OFF | 1 | 3.137609824333 | 2.040774365859 | 0.001458974736 |
| OFF | 2 | 3.093361753894 | 1.667142004850 | -0.000901084881 |

Durante S abierto C2 cambia+52.528301027 mV ON y
-44.248070439 mV OFF. El nombre del tramo describe las fuentes;
no asigna una fase ADSR al estado interno. C7 mantiene memoria y puede
sostener el otro camino de gatillo después de abrir S.

## Cobertura y costo

13385 accepted/26770 finos;168
candidatos/38472 ecuaciones independientes.
Residual/gate máximo0.0007355189794; corrección/gate1.338935464e-06.
24 cortes comparados a229 coordenadas pasan2 µV/2 nA; diferencia de
voltaje máxima0.1875551603 µV. Periodos y resets pasan10 ns.
Balances por tramo, total y unión: error máximo2.580171384e-18 C,
gate1 pA×duración. Sólo cuadratura fina publicada, no integración
independiente de todas las etapas.

24 restores de prefijos de hasta16 accepted;
368 avances repetidos por bits,16 corrupciones
y8 rollbacks inducidos. No replay completo de los nuevos tramos de1.5 ms.
[Campaña02](../evidence/voice_contour_cycle_native02.json):1131.712800 s;
auditor32.432604 s;22028616 bytes privados.
[QA](../evidence/voice_contour_cycle_tests01.json) protege las fuentes y
evidencia previa/nueva.248 tests Rust heredados por identidad, no
reejecutados; biblioteca sin recompilar, sin SPICE ni audio nuevo.

## Próximo bloque

El circuito funcional ya cubre un ciclo con el contorno cargado. Medir
ahora el costo del solve y desarrollar una aceleración algebraica exacta
contra esta referencia, con estados, señales y error controlados, para
hacer viable un contorno de duración musical. Mantener pendientes
contorno desde silencio, cargas de los otros dispositivos de placa2,
contorno de filtro, osciladores2/3, identificación física y deadlines RT.
