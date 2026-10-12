# Reutilizar el trial aceptado de Newton

Declaración previa a medición, 2026-10-12. Base RF-D f8b89c9, voz229
CA3046 condicionada. Sin cambios físicos, temporales ni de tolerancias.

## Hipótesis y cambio

La búsqueda de línea calcula el stamp y la corrección lineal del trial
antes de aceptarlo. La siguiente iteración repite ambas funciones puras
con exactamente p, historia fija, delta y h. Conservar esos dos resultados
elimina una evaluación y un solve por transición aceptada entre iteraciones.
No reciclar un Jacobiano de otro estado ni una factorización aproximada.
La primera evaluación, criterio de parada, 64 iteraciones, 24 halvings,
orden aritmético, predictor y errores permanecen iguales. La iteración64
debe seguir rechazando si sólo su trial final cumple: no ampliar el budget.

## Contraste y costo

Extraer los 84 pares seleccionados de los cuatro perfiles de ciclo: coarse,
mid y end, incluyendo reposo, cambios de gatillo y reset. Mantener float
entrante por bytes, fuentes y h. Comparar todos los componentes HIGH/LOW
de candidatos/incrementos, residual, corrección, iteraciones y trials por
bits contra el kernel congelado y los valores almacenados. Warmup separado;
cinco rondas alternando orden referencia/reuso; medir ambos kernels en el
mismo proceso. Instrumentación de laboratorio cuenta llamadas, duración
de ensamblado y solve; se publica aparte del runner sin instrumentación.
Exigir menos ensamblados/solves y mediana de aceleración>1 para admitir
utilidad en este banco. El wall anterior no es un benchmark pareado.

Repetir los cuatro recorridos completos de3.004 ms con cada semilla propia
y el mismo caller/controlador. Exigir identidad byte a byte de TODOS los
archivos de perfil respecto de la campaña anterior: STEP/LTE/intentos,
OBS, ledgers, raíces seleccionadas, checkpoints y rechazos inducidos.
No comparar ejecutables ni el tiempo de pared textual. Heredar el contraste
independiente de38472 ecuaciones sólo por identidad de esos datos.
Comparar error y rollback también en los casos del caller; no reclamar
cobertura universal de matrices o de todos los errores de Newton.

120 s compilación, 300 s benchmark, 900 s/perfil, 4000 s campaña;
64 MiB privados nuevos, reserva1 GiB, stack32 MiB. Cada rechazo conserva
fuentes/salida y replay idéntico antes de reparar. Proteger QA3043 fuentes
y7566 privados.248 tests heredados por identidad, no reejecutados.
No nueva biblioteca, SPICE, audio, contorno desde silencio o RT.
El costo medido incluye copias/stack del cache: ahorrar operaciones no
basta para acreditar deadlines ni una nota musical completa.
