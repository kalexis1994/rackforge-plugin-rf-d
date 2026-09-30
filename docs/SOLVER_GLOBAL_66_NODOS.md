# Solver global analítico de 66 nodos

## Alcance y procedencia

`circuit66.rs` es una alternativa experimental al [cierre por puertos Q26/Q28→J7](CUTOFF_LADDER_J7_NATIVO.md). Resuelve simultáneamente 66 voltajes. Conserva las redes de SVC-9 Fig. 9-11 (PDF p. 13), Fig. 9-8 (p. 10), Fig. 9-17 (p. 19) y Table 7-8 (pp. 30–31). Los valores y derivaciones corresponden a [cutoff](CUTOFF_NATIVO_Q26_Q28.md), [ladder](LADDER_SALIDA_NATIVA.md), [recuperación](RECUPERACION_SALIDA_NATIVA.md), [VCA1](VCA1_SALIDA_NATIVA.md), [VCA2](VCA2_SALIDA_NATIVA.md), [conversión](PUERTO_NATIVO_C4_CONVERSION_SALIDA.md) y [salida](PUERTO_NATIVO_C2_SALIDAS.md).

Las constantes de red se transcriben nuevamente en el ensamblador global para hacer explícitas todas las terminales. Esto introduce riesgo de divergencia entre implementaciones: los vectores monolíticos, el contraste con la ruta por puertos y la comprobación completa del Jacobiano son gates obligatorios para futuras modificaciones. No son parámetros identificados de una unidad física.

Se conservan Ebers–Moll de ambas junturas, los diodos Shockley, rails ideales y Euler implícito. El perfil CA3046 de la voz y las incertidumbres de R61/semiconductores no cambian. BUS, contorno, teclado, modulación y las dos leyes de volumen siguen siendo fronteras impuestas; todavía no es una voz completa.

## Ecuaciones y discretización

Cada resistor añade `I=(Va−Vb)/R` A y conductancia `1/R` S. Cada BJT añade sus tres corrientes terminales y las nueve derivadas locales; las terminales que eran puertos impuestos pasan a ser columnas/filas del sistema. La polaridad PNP se aplica a las corrientes y a los argumentos exponenciales; ambas polaridades se cancelan en sus derivadas. Los diodos conservan orientación, Is, idealidad y temperatura separados entre placas.

Los 17 capacitores explícitos conservan `I=C/dt*(Va−Vb−V_anterior)` A: cuatro celdas de ladder, C24/C27, C5/C1/C9, C6/C15 del VCA, C4/C2, C19/C15/C21 de placa 3 y C18. C10 se elimina exactamente con `y=(C10/dt)/(1+(C10/dt)Rserie)` S; su corriente es `y*(Vtap−VbaseQ30−V_C10_anterior)`. No se pierde la carga de C10 al eliminar el nodo de la rama serie.

El DC usa la ruta por puertos como semilla y después cierra las 66 KCL simultáneamente con capacitores abiertos. La semilla es una herramienta numérica. En audio, el predictor extrapola dos estados aceptados; al fallar reintenta desde el último estado. Todos los ensayos reciben el mismo historial de los 18 capacitores. La publicación es atómica.

Se conservan posiciones eléctricas, cargas positivas declaradas, parámetros BJT/diode positivos, dt>0 s y el dominio exponencial ≤45. Newton y búsqueda están acotados a 16/16. El sistema global exige KCL <10 pA en todas las filas, en vez de los 100 pA exteriores de la partición original. Los estados, residuales y matrices son arrays fijos; no hay recursión ni heap en procesamiento. Una matriz densa `66×66` ocupa 34 848 bytes; falta cuantificar el pico de stack y el margen del hilo de audio del host.

## Eliminación de ceros

El almacenamiento sigue siendo denso. La variante de eliminación con pivote escalado omite un candidato de pivote o una actualización de fila sólo si el coeficiente es **exactamente cero**. Conserva el mismo orden de pivotes y operaciones para los coeficientes restantes. No elimina conductancias pequeñas mediante un umbral. La regresión incluye una matriz con pivotes y fill-in, otra con coeficientes de 10⁻⁴⁰ y 10⁴⁰, y rechazo de singularidad; coincide con la eliminación densa.

## Contraste y precisión de la referencia

Los 128 pasos congelados del oráculo Python de 66 nodos usan diferencias finitas y un solver monolítico independiente. El global Rust dio error máximo interno **53,37 nV**, J7 **0,248 nV** y relación señal/error numérica **126,0 dB**. En tres instantes por cada R61, las 66 columnas del Jacobiano analítico se cotejan por diferencias simétricas de 0,1 µV, con criterio `|J−Jfd|<10⁻⁸ S+3×10⁻⁶|Jfd|`. Se comprueban también C18/C10, corriente de cola, HI/LO, datos inválidos, presupuesto agotado y predictor rechazado.

El contraste extendido de 8192 muestras detectó un límite de la referencia nativa previa: el colector Q12 de conversión (nodo 45) difería **2,439 µV** en la muestra 8, aunque J7 difería sólo 39,76 nV. Incumplía el criterio interno fijado de 2 µV. En ese instante el primer VCA aceptaba variaciones de base pequeñas con su tolerancia de 100 pA; las etapas posteriores amplificaban esa diferencia de sesgo.

Se probaron, por separado, tolerancias más estrictas en VCA2 y en conversión C4. Ninguna corrigió ese máximo y se restituyeron. Exigir **10 pA en el primer VCA** redujo el máximo interno a **1,322 µV** (muestra 16), J7 a **21,48 nV**, C10 a **0,06108 nV** y corriente de cola a **0,0001822 pA**. La relación señal/error numérica de esa traza es **141,512 dB**. El criterio de 2 µV se conserva; se hizo más estricta la convergencia del circuito que servía de referencia. La regresión VCA1 exige ahora <10 pA. Los vectores Python y los criterios previos de audio no se relajaron.

`evidence/circuit66_precision_gate.json` registra el ensayo rechazado y la corrección. El benchmark `--compare --emphasis` exige, en 8192 muestras, J7 <1 µV, todos los nodos <2 µV, C10 <1 µV, cola <1 nA y relación numérica >90 dB. El script de comparación se detiene si falla ese gate. El test global de heap cubre DC y C10 abierto/cerrado sin asignaciones.

## Costo y admisión

La comparación alterna cinco corridas por método, del mismo ejecutable release, Windows/Ryzen 5 5600X. Cada corrida reinicializa y ejecuta 8192 muestras de calentamiento y 8192 medidas. Ambos métodos reciben BUS 100 Hz/100 mV, contorno 2 Hz/20 mV, R14=25 kΩ y las mismas cargas. Registro completo y versión de Rust en `evidence/circuit66_deadline_comparison.json`.

| Medida de cinco corridas | Resultado |
| --- | --- |
| Media de medias por puertos | 24,0369 ms/bloque |
| Media de medias global | 2,5589 ms/bloque |
| Razón de costo por puertos/global | 9,39 |
| Peor bloque global | 3,257 ms |
| Bloques globales fuera de plazo | 640 de 640 |
| Fallos de convergencia, ambos métodos | 0 |

La comparación de señal de 8192 muestras también pasó. La ganancia de costo es una medida local del escenario; **2,559 ms aún exceden los 1,333 ms disponibles**. Se admite como alternativa experimental contrastada y se mantiene la ruta por puertos como referencia. No se admite como motor de audio del plugin.

La mejora de costo no cambia C6: no hay comparación de audio vintage ni afirmación de identidad sonora. El solver global sigue experimental y C7 permanece abierto mientras exceda 1,333 ms por bloque de 64 a 48 kHz. Faltan también pruebas de extremos de controles, duración mayor, pico de stack, estabilidad/aliasing con osciladores y admisión en el host.

```powershell
cargo test --workspace
cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output -- --global --emphasis
cargo run --release -p rf-d-circuit --example bench_ladder_recovery_output -- --compare --emphasis
./tools/compare_circuit66_deadlines.ps1
```

## Lecciones para RACE

El [ensayo posterior de ordenación por grado mínimo](ORDENACION_GLOBAL_RECHAZADA.md) conservó la señal pero aumentó el costo medio 3,416 %. Se rechazó y se restituyó el código anterior; el parche y las mediciones quedan registrados.

- Contrastar voltajes internos junto a la salida: una salida precisa puede ocultar error de sesgo en etapas anteriores.
- Elegir tolerancias por sensibilidad de la cascada; una cota KCL local no asegura por sí sola una cota de voltaje global.
- Conservar puertos como referencia funcional, y medir la anidación antes de usarla en audio.
- Comprobar el Jacobiano completo, incluido el retorno y las bases controladas por otras etapas.
- Medir señal y plazo con los mismos controles; registrar reintentos, fallos y bloques excedidos.
- Omitir ceros exactos permite ahorrar operaciones sin inventar un umbral eléctrico para conductancias débiles.
