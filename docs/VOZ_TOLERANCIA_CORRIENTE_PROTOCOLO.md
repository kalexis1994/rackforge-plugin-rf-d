# Voz: tolerancia absoluta de corriente y controles reservados

Fecha: 2026-10-06. El banco KLU anterior mantiene su rechazo de cutoff
bajo y ambos mute. Las tres trazas señalan JQ7_left como elemento de
convergencia; base Q21=0 V rechaza a 1.754 ns, antes del primer reset.
Ese diagnóstico no identifica un error de topología ni una causa única.

## Hipótesis y cambio numérico

La comprobación de corriente del JFET suma tolerancias relativa y absoluta
al comparar predicción y corriente actual. Sus cargas se integran y también
participan del control de paso. Fuentes primarias: NG-46, opciones de
análisis transitorio, y código `jfetload.c`/`cktterr.c` fijado por revisión y
SHA en [el manifiesto](../evidence/voice_current_tolerance_sources.json).
La tolerancia interna no es una constante física ni un gate de error de audio.

Se exploran, en orden, `abstol=1e-12`, `1e-11`, `1e-10` A frente al
baseline 1e-13 A. Cada candidato conserva KLU, reltol=1e-7, vntol=1e-8 V,
gmin=1e-12 S, bypass=0, itl4=100, tarjetas, todas las ramas y condiciones
iniciales. Se mantiene Gear2 con paso máximo 125 ns, duración 40 ms y
observación desde 20 ms. Ningún capacitor se elimina o regulariza.
El motivo es contrastar sensibilidad del criterio de convergencia;
no se presume que una tolerancia mayor sea suficientemente precisa.

## Selección congelada antes de medir

Por candidato: base Q21=0 V, contorno=0 V, cutoff=0.2 y nominal. Se
detiene ese candidato en la primera escena rechazada; se conserva su
trayectoria parcial. Se elige el primer candidato que complete las cuatro
con fuentes estables, reloj íntegro, salida finita y balance C2 <=1e-10 C.
Si ninguno completa, no se amplía automáticamente la lista de tolerancias.
Completar este screening no admite un nuevo oráculo.

## Validación posterior predeclarada

Con el candidato seleccionado, ejecutar las once escenas del
[banco KLU](VOZ_KLU_PROTOCOLO.md) y añadir a cada una de las tres escenas
antes rechazadas Gear2 con paso máximo 250 ns y Trap2 con 125 ns.
Total: 17 escenas. Contrastar los tres pares nominales originales, y
refinamiento 250→125 ns / Gear2→Trap2 en cada control antes rechazado.
Comparar además nominal125 contra el baseline estricto anterior.

Se mantienen los gates: frecuencia <=1 cent, extremos de BUS/recuperación/
salida <=5 mV, diferencia RMS <=1% + 10 microvolt y balance integrado
C2 <=0.1 nC por escena. Mute se reporta en voltios y dB respecto al nominal;
no se introduce un objetivo de amplitud después de observar los datos.
Un rechazo conserva el gate abierto. Un resultado aceptado sólo describe
estas escenas y fronteras; no identifica dispositivos vintage, envolventes,
estabilidad continua ni tiempo real. El banco histórico nunca se reescribe.
