# Stack del circuito global en Win64

## Qué se mide

Una matriz `66×66` ocupa 34848 bytes, pero el solver conserva matrices, residuales y candidatos en distintas llamadas. El banco `circuit66_admission --stack` crea workers separados con reserva solicitada de 2 MiB, 1 MiB o 512 KiB; consulta sus regiones antes de inicializar, después de DC y después de 8192 pasos. Las consultas y serialización pertenecen al banco offline. El DSP no añade FFI, clocks, logging ni asignaciones.

Se usan [GetCurrentThreadStackLimits](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getcurrentthreadstacklimits) para comprobar el marcador del worker y [VirtualQuery](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualquery) para recorrer las regiones de su misma `AllocationBase`. La estructura sigue el [ABI Win64 documentado](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-memory_basic_information), comprobando tamaño y bytes devueltos. No se leen/escriben páginas reservadas o guardas; sólo sus atributos.

La [reserva y el commit de stack](https://learn.microsoft.com/en-us/windows/win32/procthread/thread-stack-size) son cantidades distintas. El banco cuenta regiones comprometidas, reservadas y guardas. Las páginas comprometidas incluyen las que Windows añadió al ejecutar, además de infraestructura y guardas. No equivalen al número exacto de bytes usados simultáneamente. Se declara `precise_stack_high_water_measured=false`.

## Circuito y escena

La ruta es el [global de 66 nodos](SOLVER_GLOBAL_66_NODOS.md), SVC-9 Figs. 9-11/9-8/9-17, con semiconductores nominales, 48 kHz, BUS 100 Hz/100 mV, contorno 2 Hz/20 mV y R14=25 kΩ. Para ambos R61 se ejecutan dos caminos: DC dentro del worker; DC fuera del worker y procesamiento dentro. El estado final de ambos caminos debe coincidir <1 pV.

En la muestra 4096 se corrompe intencionalmente una componente del predictor para exigir el reintento validado. Después se comprueban un dato inválido y un presupuesto de una iteración, conservando exactamente todo el estado al rechazarse. No cambia la política de fallo del motor.

## Resultado local

Los resultados de la tabla son de la compilación anterior al [criterio de corrección DC](DC_GLOBAL_SEMILLA_COMPLETA.md). La nueva corrida `evidence/circuit66_stack_full_dc_512.json` pasa los cuatro workers/32768 muestras a 512 KiB, pero observa 324 KiB comprometidos (300 normales +24 guardas), tanto con DC dentro como fuera; quedan 188 KiB sin commit. El pico exacto sigue sin medirse.

Windows x86_64, Ryzen 5 5600X, Rust 1.97.0, release. Cada reserva pasa los cuatro workers: 32768 muestras por reserva, 98304 en total; un reintento forzado por worker, dos rechazos atómicos por worker, KCL <10 pA y diferencia final entre caminos de inicialización exactamente cero.

| Reserva observada | Commit antes | Commit después DC/procesamiento | Guardas incluidas | Reserva sin commit restante |
| --- | --- | --- | --- | --- |
| 2048 KiB | 36–40 KiB | 288 KiB | 24 KiB | 1760 KiB |
| 1024 KiB | 36–40 KiB | 288 KiB | 24 KiB | 736 KiB |
| 512 KiB | 36–40 KiB | 288 KiB | 24 KiB | 224 KiB |

El camino sin DC dentro del worker conserva 36–40 KiB al inicio y crece a 288 KiB durante los pasos. Por tanto, sólo mover la inicialización fuera del hilo no evita el crecimiento observado. El circuito matriz por sí solo tampoco describe toda la demanda de stack.

Archivos `evidence/circuit66_stack_regions_2048.json`, `_1024.json` y `_512.json`. Los dos últimos incluyen hash del módulo FFI; la corrida exploratoria inicial de 2 MiB se conserva con sus metadatos originales.

## Límites y admisión

Se confirma ejecución en workers de 512 KiB para esta compilación y escena. No se establece un mínimo de reserva ni un margen suficiente para RackForge, otro compilador, debug, WebAssembly o una voz completa. El host añadirá sus propias llamadas. La cota por páginas depende de Windows y de cuándo compromete memoria; no debe presentarse como pico exacto del algoritmo.

La implementación FFI está restringida al ejemplo Win64; en otras plataformas el banco devuelve una limitación explícita. La ruta de audio mantiene su gate de heap cero. C7 sigue abierto por deadlines y por la futura verificación en el host.

```powershell
cargo build --release -p rf-d-circuit --example circuit66_admission
./tools/run_circuit66_admission.ps1 -Mode stack -StackKib 1024 -Output evidence/circuit66_stack_regions_1024.json
./tools/run_circuit66_admission.ps1 -Mode stack -StackKib 512 -Output evidence/circuit66_stack_regions_512.json
```

Lección RACE: medir almacenamiento de una matriz, memoria comprometida del worker y pico de stack como cantidades separadas; registrar fases, infraestructura y escenas de reintento junto al camino nominal.
