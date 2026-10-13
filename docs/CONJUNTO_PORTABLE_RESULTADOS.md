# Conjunto229 en biblioteca Rust pública

2026-10-13. [Protocolo previo](CONJUNTO_PORTABLE_PROTOCOLO.md). Integración
aditiva del circuito y motor temporal admitidos, con ownership del workspace.
No cambia dispositivos, constantes, masas, puertos, Newton o controlador.

## Circuito, API y alcance

CA3046 VCO1→BUS→ladder/VCAs/J7, contorno de volumen cargado R59/Q18 y
229 estados HIGH/LOW. Conserva las fuentes, páginas, conflictos y fronteras
del [modelo admitido](RADAU_EN_SITIO_RESULTADOS.md), incluida alimentación
de contorno impuesta y cargas/semiconductores condicionados. No incorpora
identificación vintage, otros osciladores o contorno de filtro completo.

Exportaciones aditivas en lib.rs:

- [conditioned_voice](../crates/rf-d-circuit/src/conditioned_voice.rs):
  Parameters,State,Parts,Stamp,Pair y Workspace; solver y cargas ligadas a la voz.
- [conditioned_engine](../crates/rf-d-circuit/src/conditioned_engine.rs):
  Engine,Checkpoint,Settings,Accepted y errores del controlador.

El caller conserva dos buffers Stamp dentro de Workspace y lo presta por
&mut a cada step/advance. En cada llamada se repone el Stamp actual; no
cachea J/factores de otra historia/trial. Las referencias actual/trial
permutan al aceptar. El motor confirma únicamente el checkpoint conjunto
después de coarse/mid/end, LTE y observaciones; un error lo conserva.

El checkpoint no incluye scratch: restore recupera estados, parámetros,
settings, reloj y propuesta. Un workspace puede reutilizarse serialmente
entre motores; &mut impide alias simultáneo. La fachada step de una sola
llamada conserva compatibilidad y crea scratch local; preferir Workspace::step
para procesamiento repetido. Constructor/traslados grandes quedan fuera
del intervalo de procesamiento medido.

```rust
let mut workspace = rf_d_circuit::conditioned_voice::Workspace::new();
let mut engine = rf_d_circuit::conditioned_engine::Engine::restore(checkpoint)?;
let accepted = engine.advance_to(&mut workspace, target_ticks)?;
```

El ejemplo requiere checkpoint condicionado explícito y un contexto Result.
No acredita arranque desde silencio o parámetros físicos identificados.
[Receta de transformación](../tools/prepare_conditioned_portable.py).

## Biblioteca y regresiones públicas

Se compila una nueva rlib GNU x86_64, compiler/flags ligados por SHA,
sin cache Cargo ni dependencias nuevas. lib.rs conserva exactamente su
prefijo anterior y añade sólo las dos exportaciones. Solver/contorno/cargas
son copias transformadas por imports crate; todas las fuentes previas y
privados permanecen protegidos. [Compilación](../evidence/voice_conditioned_portable_library01.json).

84 raíces públicas coinciden por bytes con el laboratorio:1834 campos,
iteraciones/trials.84 stamps comparan17.620.176 coeficientes J,38.472
residuales y76.944 coordenadas de candidatas. Workspace reutilizado entre
todos los casos, A→B→A y después de rechazo, frente al control intacto.

396 sistemas J/b originales guardados se reproducen con el solver de la
rlib pública:181.368 correcciones escalares idénticas por bits. Es **replay
de matrices almacenadas**, no export de todos los solves activos del motor
público. La receta y raíces/candidatas conservan la integración; no presentar
ese replay como observación activa. Permite heredar181.368 filas Decimal100
y38.472 ecuaciones de banco; no se reejecutan sus ecuaciones independientes.
[Banco y replay](../evidence/voice_conditioned_portable_bank02.json).

El primer driver rechaza E0282 por un índice sin tipo explícito; ambas
compilaciones y fuente conservadas antes de anotar usize sólo en la closure
del driver. No cambia la biblioteca o gates. [Fallo](../evidence/voice_conditioned_portable_bank01.json)
y [reparación](../evidence/voice_conditioned_portable_driver_repair01.json).

## Memoria y heap medidos

Cuatro tests públicos de API/allocator se compilan con --test contra la rlib
nueva, --test-threads=1 y stack32 MiB. Fixtures de historias sintéticas ya
publicadas por bits, con el inicio OFF añadido preservando el prefijo original.
No publica capturas o audio propietarios.
[Tests](../crates/rf-d-circuit/tests/conditioned_portable.rs),
[fixtures](../crates/rf-d-circuit/tests/support/conditioned_seed.rs).

| Objeto | Bytes GNU x86_64 | Contrato previo |
| --- | ---: | ---: |
| Stamp | 1689104 | ≤2 MiB |
| Workspace | 3378208 | ≤4 MiB, dos Stamp |
| Engine | 4800 | ≤16 KiB |
| Checkpoint | 4800 | ≤16 KiB |

**Cero asignaciones** en9 llamadas aceptadas y3 rechazadas:4 pasos de voz,
un rechazo de teclado,2 avances temporales, destino/presupuesto rechazados,
y3 avances de dos motores que comparten scratch serialmente. Reutilización
después de otra historia/error, rollback y restore coinciden. Constructor,
fixtures, assertions posteriores e I/O no están en el intervalo contado.
Unsafe aparece sólo en el allocator del test; módulos de producción sin unsafe.
[Medición de API/heap](../evidence/voice_conditioned_portable_tests_native01.json).

**252 tests cubiertos:4 nuevos ejecutados y248 heredados por identidad**.
No se reejecuta toda la suite histórica. Cero heap no acredita deadline,
latencia o stack host. El stack32 MiB es experimental; no es una cota de uso
ni presupuesto admitido del plugin. Tamaños medidos sólo para este target.

## Cuatro recorridos usando la biblioteca y su motor

Ventana8.438→11.442 ms desde sus cuatro historias/propuestas propias.
El caller utiliza conditioned_voice/conditioned_engine de la rlib nueva y
Workspace persistente; no invoca el kernel temporal de tools.

| Final decay | h máximo µs | Accepted | Wall del perfil s |
| --- | ---: | ---: | ---: |
| ON | 2 | 3020 | 72.6223 |
| ON | 1 | 3704 | 81.9156 |
| OFF | 2 | 2987 | 70.8658 |
| OFF | 1 | 3674 | 80.2832 |

Campaña306.520700 s, incluidos I/O y replays. No es un benchmark pareado
frente a walls históricos; no se atribuye una aceleración nueva a esta API.
[Campaña pública](../evidence/voice_conditioned_portable_native01.json).

Los40 exports completos coinciden por bytes con el laboratorio, sin incluir
ejecutable/timers.13385 accepted/26770 finos,24 restores,368 avances
repetidos,16 corrupciones y8 rollbacks se reejecutan. Permiten heredar38.472
ecuaciones temporales, cargas, corrientes, balances, LTE, resets y comparación
229 al mismo reloj con sus alcances originales. El grafo no se vuelve a
ejecutar y no crea medidas de estados internos no exportados.
[Identidad temporal](../evidence/voice_conditioned_portable_trajectory01.json).

El adaptador de identidad conserva un AssertionError de receta antes de
crear su archivo público: una sustitución de ruta se había aplicado dos veces.
Replays conservados, sustitución única reparada; no cambia datos, biblioteca
o gates. [Recibo](../evidence/voice_conditioned_portable_identity_adapter_repair01.json).

## Admisión y siguiente bloque

**Voz condicionada y motor temporal públicos admitidos para esta ventana**,
con contrato de ownership/memoria y heap medido en las rutas enumeradas.
[QA](../evidence/voice_conditioned_portable_tests01.json) protege el historial.
36197503 bytes privados nuevos, dentro del presupuesto96 MiB;
sin cache Cargo, SPICE, duración/audio nuevos, contorno desde silencio,
periodicidad asintótica, identificación física o DSP/RT admitidos.

Siguiente: inicialización y receta pública de controles desde una historia
condicionada trazable, seguida de render offline con calendario/cargas
declarados. Un runner de laboratorio no es aún interfaz musical o plugin.
Mantener admisión de circuito, escucha y deadlines como gates distintos.
