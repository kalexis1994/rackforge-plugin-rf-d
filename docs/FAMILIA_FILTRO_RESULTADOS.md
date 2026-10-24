# Entrada real del filtro y restricciones por etapa

2026-10-24. [Protocolo](FAMILIA_FILTRO_PROTOCOLO.md),
[decisión de integración](FAMILIA_FILTRO_RESTRICCIONES.md),
[nativo SDIRK](../evidence/family_filter_sdirk_native01.json),
[oráculo independiente](../evidence/family_filter_sdirk_reference01.json),
[ciclos y carga](../evidence/family_filter_cycles01.json) y
[QA](../evidence/family_filter_tests01.json).

## Qué se conecta

BASE_Q29 ya no es fuente impuesta. La familia H128, con trims y datos
anteriores intactos, entrega corriente al BUS de la cadena real de68
nodos: Q29/R54/C27, ladder, recuperación, dos VCA y salida/J7.
El solve incluye69 incógnitas con fase, cargas HIGH/LOW y Jacobiano
completo. OSC1 se excluye de OnMixer porque R6/R45 ya están en el puerto
de la familia. Las otras ramas siguen siendo fuentes cero condicionadas.

Doce DC propios de fuente media: tres CV, dos cargas y los perfiles
documentales R61=200/200000 ohm separados. Controles fijos de laboratorio,
range=.1, cutoff=.5, R14=25k y loudness1/2=2 V. Conservar dieciocho
memorias capacitivas, incluido C10 explícito. No hay KEY/contornos activos
o CV temporal en esta nueva ruta. La voz audible anterior queda intacta.

## Oráculo y ciclos completos

Ecuaciones Python independientes de la cadena, todos sus nodos y el
cursor R6 por solve propio; Newton FD sin semilla de raíz nativa.
Doce DC y dieciséis raíces de subpaso BE69 pasan; estas últimas comparten
la historia declarada, no otra trayectoria independiente. La familia
H128 es compartida: no constituye un segundo oráculo VCO físico.
Máximo nodal de la comparación 6.70 nV, gate1 uV. BASE/BUS/fase:
48 columnas y3312 entradas de Jacobiano pasan el contraste FD.
El QA separa voltios de ciclos al comparar las69 coordenadas; no usa
el campo máximo mezclado del export de diagnóstico como gate de admisión.

R61=200/L1, CV=-2.6/-.6 V: cuatro recorridos completos del primer ciclo
desde DC medio, pasos500/250 ns, fuente en fase0 desde el arranque.
No son ciclos ya asentados. Refinamiento DC/norma de armónicos1..8:

| Métrica máxima | Resultado | Gate |
|---|---:|---:|
| BUS | 60.16 nV | 10 uV |
| BASE_Q29 | 59.97 nV | 10 uV |
| Panel/C27 | .1010 nA | 2 nA |
| J7 DC | .0780 nV | .5 mV |
| J7 vector armónico | .0354 nV | 2% o1 uV absoluto |

J7 tiene señal no nula en los cuatro recorridos. Es contraste numérico
de esos ciclos y controles, no audio a48 kHz o parecido con un vintage.
KCL algebraico máximo9.94e-14 A, gate1e-13 A; balance C27 máximo
3.68e-20 C. Los pesos de corriente corresponden a SDIRK, no a una
cuadratura trapezoidal aplicada después. Se conserva la carga inicial.

## Rechazo que cambió el integrador

El primer kernel trapezoidal resolvía sus raíces y coincidía con FD,
pero eso no bastaba: el DC medio cambia instantáneamente a fase0 y no
satisface la restricción algebraica BASE+BUS de esa fuente.
[Diagnóstico](../evidence/family_filter_constraint_diagnostic01.json) y
[replay idéntico](../evidence/family_filter_constraint_replay01.json):
trapezoidal perpetúa un residuo alternante de .5243/.2178 uA. Los cuatro
recorridos originales conservan su rechazo físico; no son ciclos admitidos
por pasar residual de sus ecuaciones discretizadas o error entre pasos.

[SDIRK2](../evidence/family_filter_sdirk_derivation01.json),
gamma=1-1/sqrt(2), impone la restricción en cada etapa y publica sólo
el endpoint final. La segunda historia virtual no es otro paso físico.
No cambia capacitor, dispositivos, familia o gates. El punto t=0 se
etiqueta como salto de fuente desde DC medio; desde la primera etapa
se exige el balance instantáneo. No se reinicializa C27 para conseguirlo.

Un auxiliar para leer el Jacobiano falló al convertir StepError a error
de consola. Fuente/replay y
[corrección](../evidence/family_filter_tangent_correction01.json) conservados;
la corrección sólo adapta ese error, sin tocar ecuaciones o límites.

## Publicación, recursos y alcance

[Doce fixtures](../evidence/family_filter_retry01.json) comprueban36
rechazos, incluido agotamiento real de una iteración. Estado HIGH/LOW
intacto y retry válido por bits, comparando ceros con signo; cero heap
medido. Controles de traza con BASE fija y R45 duplicada son detectados;
no se cuentan como nuevas simulaciones del circuito perturbado.

Compiler/biblioteca congelados por hash. Sin Cargo, rlib nueva, cache,
SPICE o WAV nuevo. Ventanas de los ciclos exactas, raíces HIGH/LOW y
recibos de los intentos conservados, área temporal vacía al finalizar.
Se heredan272 tests por identidad, sin reejecutarlos o sumar ensayos como
unit tests. Fuentes, entradas privadas, voz activa y escucha protegidas.

Admisión del kernel de laboratorio, sus DC/etapas y cuatro primeros
ciclos SDIRK con la entrada real del filtro conectada. No nota asentada,
integración de contornos, nuevo arranque del VCO de circuito, controles
generales, deadline RT o fidelidad vintage. Siguiente: extender una nota
con estos controles fijos, medir asentamiento y conectarla a la lectura
antialias antes de reemplazar la escucha actual.
