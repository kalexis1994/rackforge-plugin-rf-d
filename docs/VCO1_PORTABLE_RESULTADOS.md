# VCO1: motor portable de referencia

## Resultado

El crate `rf-d-circuit` expone `vco1_engine::Engine`: arranque propio,
avance de un par Radau, observaciones consistentes y checkpoint completo.
El solver conserva las ecuaciones, tarjetas y gates del laboratorio.
Es un motor de referencia integrable; no está admitido para un thread de
audio. Perfil físico contrastado: clásico CA3046 nominal, C4=10 pF,
25 °C y mixer/controles impuestos. No hay nueva identificación física.

```rust
use rf_d_circuit::{vco1_engine::{Engine, Settings}, vco1_stamp::Controls};
let mut engine = Engine::startup(Controls::default(), Settings::default())?;
// 30 ms exactos en el reloj del protocolo; cada llamada acepta un solo par.
let target_ticks = 15_728_640_000_u64;
while engine.checkpoint().elapsed_ticks < target_ticks {
    let accepted = engine.advance_to(target_ticks)?;
    // Consumir los dos endpoints con sus relojes reales y corrientes Radau.
}
let checkpoint = engine.checkpoint();
let restored = Engine::restore(checkpoint)?;
```

El ejemplo muestra el contrato de uso, no una campaña nueva de 30 ms.
No convertir el reloj a f64 al avanzar, ni publicar el midpoint antes
de admitir full/mid/end. La restauración valida representación y dominio;
no certifica procedencia del estado o arranque propio de un checkpoint ajeno.
Controles y ajustes viajan en el checkpoint; el API no introduce cambios
de parámetros a mitad de un par.

## Pruebas ejecutadas

[Cuatro tests Rust](../evidence/voice_vco1_portable_native03.json) pasan:

- 26 comparaciones de etapas contra Decimal100 guardado: ocho de los cuatro
  intervalos reales del perfil125 y 18 del diagnóstico full/mid/end. Son
  comparaciones nuevas; no son 26 solves independientes nuevos. Se mantienen
  los gates de 2e-7 V/2e-10 A y ambos ratios Newton <=1.
- Doce comparaciones de corrientes Qa/Q10/Q7 con el referente independiente,
  gate 2e-10 A. La corriente de panel mantiene R6=12,5 kohm.
- Arranque propio y aceptación tras cinco intentos; continuidad exacta
  checkpoint/restore en estado y corrientes, con los relojes de ambos endpoints.
- Rollback completo por límite de intentos y error temporal; rollback por
  fallo LineSearch al piso. La escena extrema sólo prueba el rechazo del API.
- Destinos inválidos, seis restauraciones inválidas y avance exacto próximo
  al límite u64, sin wraparound; el reloj sobrepasa u32.
- Cero asignaciones de heap en los intervalos medidos de arranque,
  restauración, aceptación y rechazos. Fixtures y asserts quedan fuera.

235 tests previos se heredan por identidad de sus módulos; cuatro nuevos:
239 cubiertos, cuatro ejecutados en el intento final. Se conservan también
los intentos fallidos y sus replays, sin contarlos otra vez como cobertura.
Los dos recorridos nominales previos y sus métricas permanecen archivados;
no se volvieron a ejecutar ni se atribuyen al nuevo wrapper. El perfil250
usa el mérito original; el125 cambia a residual sólo al recuperar el fallo.
El kernel portable coincide con la copia residual recuperada, pero eso
no admite un recorrido completo del wrapper. La herencia íntegra prevista
en el protocolo queda limitada a leyes/gates y evidencia anterior; el API
se contrasta localmente. No hay SPICE ni audio nuevos.

## Intentos y límites

El primer intento no compiló: el wrapper esperaba un error Newton, pero
el arranque devuelve un error tipado que incluye semilla/dispositivos/Newton.
Se preservan original y replay; la reparación sólo corrige el tipo del wrapper.
El segundo pasó tres tests y falló una suposición del test: una carga de1 A
rechazó por LTE y no por Newton. El diagnóstico conservado probó ocho escenas
y su replay; se eligió CV de rango40 V, que produce LineSearch, para ejercer
esa rama. No se cambiaron kernel, tolerancias o admisiones eléctricas.

La primera auditoría de fuentes encontró CRLF en las funciones del solver
del crate y LF en la copia de laboratorio. Se conserva fallo/replay del
validador; la comparación admite exclusivamente esa diferencia de finales
de línea. Los archivos históricos mantienen sus bytes y hashes originales.

GNU fijado, O2 explícito por RUSTFLAGS, pila de laboratorio de8 MiB y ejecución
serial. La etiqueta Cargo `unoptimized + debuginfo` no describe el override
`-C opt-level=2` registrado. Heap cero y el tiempo global del test no acreditan
pila mínima ni deadline. No se midió callback RackForge, Linux/macOS ni
rendimiento de voz completa. El módulo fine privado conserva su solver Euler
histórico para identidad de bytes; no se exporta como nuevo motor.

## Próximo cierre

Resolver el dominio temporal común con la entrada/mixer/ladder/VCAs. Su piso
actual de125 ns supera los pasos mínimos del VCO; no conectar mediante clamp
de paso, duplicación de R6/R45 o interpolación sin contrato. Derivar el stamp
de carga conjunta, preservar memorias y contrastar primero intervalos reales
de conmutación. CV/trims reservados, C4=100 pF y osciladores2/3 siguen abiertos.

[Protocolo](VCO1_PORTABLE_PROTOCOLO.md),
[procedencia y snapshot](../evidence/voice_vco1_portable_before01.json),
[QA del bloque](../evidence/voice_vco1_portable_tests01.json).
