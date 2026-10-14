# Ambos contornos cerrados con las cargas de filtro y VCA

2026-10-14. [Protocolo previo](CONTORNOS_CADENA_PROTOCOLO.md).

## Función cerrada

La red nativa de 118 nodos conecta ambos contornos, ladder, recuperación,
dos VCA y salida J7. VCA_BASE y TAIL son incógnitas simultáneas: R59 carga
el seguidor de volumen y R60 devuelve al contorno la corriente del ladder.
Q26/Q28 y C18 aparecen una sola vez. Amount mantiene la carga de su cursor
por reducción exacta; el oráculo conserva el cursor como nodo 119.
C2/C5/C7 y cargas de los seis transistores de latch/gatillo se preservan.
El gatillo compartido continúa emergiendo de Q12/Q20, sin selector ADSR.

Módulos nuevos de laboratorio fuera de lib.rs: `dual_chain.rs` y promoción
generada `dual_contour_loaded.rs`. El generador registra cinco sustituciones
exactas del núcleo anterior; su fuente permanece intacta. Se usa la misma
rlib congelada y no se recompila la biblioteca ni se crea caché Cargo.

## Banco completo

Dos escenas de 36 ms, máximos 8/4 us, C11/C12 OFF, panel fijo del protocolo.
KEY cambia a 1/10/20/30 ms; nunca se reinician los capacitores. La excitación
es una fuente sinusoidal impuesta al mixer, 100 Hz y 0,2 V pico: este cierre
no incorpora todavía el oscilador real. Arranque DC propio de la unión;
no prolonga la historia de voz de 164 ms ni los anteriores WAV.

- 8671 y 12579 Accepted: 21250 pasos y 42500 extremos de medios pasos.
- 144 clocks comunes comparan todos los 118 nodos y ambas cargas R59/R60.
- 20 replays locales comprueban estado final e intervalo aceptado; no son
  nuevos checkpoints ni replay completo de todos los campos de las etapas.
- Seis rechazos de intervalos inválidos conservan el estado.
- 60 parejas Radau seleccionadas: 14518 filas originales, incluidos dos DC
  y el cursor explícito; KCL máximo 0,400817 pA, corrección 0,049735 nV.
- 139240 entradas comparadas de FD DC/carga seleccionadas. Máxima fracción
  del gate 0,006750603. La evaluación adicional del núcleo condensado usa
  las mismas parejas: no sumar ambas auditorías como cobertura independiente.
- DC nativo/original difiere como máximo 1,473e-12 V.

[Banco](../evidence/dual_chain_native04.json),
[derivadas y refinamiento](../evidence/dual_chain_reference01.json),
[119 filas originales](../evidence/dual_chain_star01.json) y
[observaciones eléctricas](../evidence/dual_chain_observations01.json).
Los gates de Newton, FD y refinamiento del protocolo permanecen intactos.

## Señales observadas

Extremos muestreados cada 250 us, escena 4 us; no cotas continuas.

| Señal | Mínimo | Máximo | A 36 ms |
| --- | ---: | ---: | ---: |
| C2, V | 0,860201 | 6,679579 | 6,333900 |
| C5, V | 0,860557 | 5,256912 | 4,114998 |
| VCA_BASE, V | -0,276838 | 4,307776 | 4,283379 |
| TAIL, V | 1,390989 | 1,451779 | 1,405717 |
| J7, V | -0,00106232 | 0,000965962 | 0,000155162 |

A 10 ms: R59 = 3,71459 uA y R60 = 82,66946 uA. A 20 ms:
4,76800 uA y 27,17587 uA. Estas corrientes se resuelven conjuntamente,
no son fuentes de control prefijadas. La salida J7 responde a la excitación
y al contorno cargado. No se exporta una escucha nueva de sólo 36 ms.

## Intentos conservados y límites

La primera referencia DC se detenía al minimizar el mayor residual de la
red, aunque los débiles nodos 27/28 del primer VCA aún necesitaban corrección.
Residual de 3,56e-16 A con corrección de 1,36 uV: no se admitió. Fuente,
replay sin cambios y diagnóstico se conservan. La búsqueda acepta mejora
de corrección cuando ambos residuales ya cumplen 1 pA; el criterio final
sigue exigiendo 2 nV. No se cambiaron componentes ni se aflojaron gates.
Dos intentos de compilación rechazados conservan sus fuentes y replay;
las reparaciones corrigieron sintaxis Rust y acceso al tiempo del llamador.

El banco tarda 48,4/81,8 s por 36 ms simulados. Sigue siendo una referencia
de laboratorio, sin admisión de heap/deadlines o tiempo real. No prueba
fidelidad a una unidad vintage, panel completo o receta opcional en vuelo.
Próximo cierre funcional: sustituir la entrada impuesta por el VCO real,
compartiendo BUS y su carga; después medir una reducción frente a esta red.
