# Integración Rust del conjunto229 y contrato de memoria

2026-10-13, antes de compilar/medir. Basea69a1e9; QA3372 fuentes/7933 privados.
Promover la voz condicionada y controlador del laboratorio a módulos públicos
conditioned_voice/conditioned_engine. No es un plugin o admisión DSP/RT.
[Circuito admitido](RADAU_EN_SITIO_RESULTADOS.md) conserva sus fuentes, páginas,
hipótesis y fronteras; sin constantes audibles nuevas o identificación vintage.

## API y ownership

Workspace conserva dos Stamp inicializados entre calls. El caller lo construye
y lo presta por &mut al paso del circuito o advance_to del motor temporal.
Cada step repone el Stamp actual antes de usarlo; no conserva J/factores de
otra historia/trial. Actual/trial permutan referencias al aceptar como antes.
El checkpoint contiene estado229 HIGH/LOW, parámetros, settings, reloj y
propuesta entrante; no incluye scratch. Restore no requiere restaurar un
workspace: el próximo step reconstruye todo. Confirmación atómica del conjunto.

Engine conserva sólo el checkpoint; el caller puede reutilizar un workspace
serialmente entre motores, sin alias simultáneo permitido por &mut. La fachada
step de una sola llamada conserva compatibilidad pero crea scratch local;
las rutas reutilizables deben llamar Workspace::step. Exportar solver, contorno
y cargas como submódulos ligados a la voz; transformaciones crate/imports
explícitas, ecuaciones/copias originales protegidas por receta y SHA.

## Contrato medido

Workspace≤4 MiB, Stamp≤2 MiB y Engine/Checkpoint≤16 KiB, medidos con size_of
en el target GNU x86_64. Sin heap/I/O/locks/logs en step/advance; constructor,
fixtures, serialización y observador quedan fuera del intervalo medido.
Instrumentar allocator sólo en el test/driver, no en el código de producción.
Medir aceptación, destino inválido, presupuesto rechazado, recuperación y
reutilización tras otra historia. Cero asignaciones no demuestra deadline.
Stack experimental32 MiB; no inferir máximo real de stack o presupuesto host.

Biblioteca nueva, compiler/flags idénticos a la referencia. Exportación
aditiva en lib.rs; el resto de fuentes históricas y privados queda intacto.
248 tests anteriores heredados por identidad, no reejecutados: observar
integración nueva con regresiones propias y conservar conteos separados.

84 parejas congeladas ON/OFF,2/1 µs y coarse/mid/end: mismo kernel de laboratorio
como control,1834 campos e iteraciones/trials por bits. Reusar Workspace a través
de todos los casos y repetir A→B→A, con error intermedio, frente a un scratch
fresco. Matrices/residual/candidatas completos por bits;396 J/b/correcciones
contra el banco admitido antes de heredar181368 filas. Raíces por bytes para
heredar38472 ecuaciones; cercanía no permite heredar.

Cuatro recorridos propios8.438→11.442 ms usando la biblioteca nueva y su motor,
no un adaptador que invoque el kernel de tools.40 exports completos por bytes
contra la campaña admitida, con sus restores, replays, corrupciones y rollbacks.
Sólo esa identidad permite heredar el grafo temporal y gates de cargas/LTE/
eventos/balances. Compilar biblioteca y drivers≤120 s cada uno, banco/auditor
600 s, perfil990 s, campaña4000 s;96 MiB privados nuevos, reserva1 GiB.
El presupuesto incluye rlib y ejecutables; ningún cache Cargo nuevo requerido.
Preservar fallo/replay antes de reparar. Sin audio/duración, SPICE, contorno desde
silencio, periodicidad asintótica, fidelidad física o DSP/RT nuevos.
