# Receta pública y render offline condicionado de J7

2026-10-13, base aa496b5, antes de compilar y medir. QA anterior:3407 fuentes,
7981 privados. Experimento finito; no se cambia solver, topología o gates.

## Receta y procedencia

`conditioned_recipe::Recipe` restaura la historia sintética nominal propia
ON o OFF ya publicada en `tests/support/conditioned_seed.rs` (A o D), con
229 HIGH/LOW, reloj8.438 ms y propuesta1024 ticks. No busca una raíz ni
arranca desde silencio. Exponer historia ON/OFF y resolución1/2 µs como enums;
la receta tiene identidad `rf-d/conditioned-j7-ca3046/v1`. No reusar esta
historia para otros parámetros, notas o presets sin recondicionarla.

Origen eléctrico: [voz pública](CONJUNTO_PORTABLE_RESULTADOS.md), su
`tools/conditioned_portable_runner.rs::scene` y
`tests/support/mixer_chain_lab.rs::lab_parameters/controlled_boundary(0,true)`.
Transcribir cada campo explícitamente; comparar todos los parámetros y
cargas frente a esa escena. Las leyes de dispositivo y constantes internas
conservan las fuentes, dominios e incertidumbres de los módulos históricos.

| Parámetro | Unidad/valor | Procedencia y alcance |
| --- | --- | --- |
| VCO CA3046 | seis CV−2.1 V, R8α.5, R11=500 Ω, C4=10 pF | SVC-9 p5/p19; [stamp](VCO1_STAMP_PROTOCOLO.md), escena nominal, conflicto C4 BOM separado |
| OSC1/panel y mixer | α.5; otras cuatro ramas OFF | OSC1 pertenece al VCO conectado al BUS, no a una onda impuesta; fuentes de otras ramas[0,.2,−.3,.1,.4] V conservadas aunque OFF |
| Filtro | cutoffα1, scale250 Ω, rangeα.1, R14=25 kΩ | fronteras de escena; contorno de filtro0 V, Q21base2 V impuestos; no control musical calibrado |
| R61/R30 | 200/830 Ω | alternativa condicionada heredada, no identificación de unidad vintage |
| BJTs cadena | Is10⁻¹⁴ A, βF100, βR5,298.15 K | tarjetas nominales sintéticas; headphoneβF160 |
| Diodos conversión/headphone | Is1.293303751274349e−9 A, n1.5 | hipótesis nominal heredada, sin identificación física |
| Salida HI/LO | 10/100 kΩ | cargas simultáneas resueltas, R20parteinferior2500 Ω |
| Headphones | tip/ring32 Ω, SW18ON, R21inferior2000 Ω | cargas físicas en red resuelta; dt heredado1/48000 s es campo de frontera, no paso temporal del solver |
| Balances placa4 | 12.5/50 Ω | trims sintéticos fijos |
| Alimentación | ±10 V, contornos9.3 V | fuentes impuestas, sin cerrar riel bruto15 V/Q26 de contornos |
| Volumen/R59 | C2/Q3/Q2→68 kΩ→baseQ18placa4 | [SVC-9 p9/p13/p19, tablas p26–27/30–31](CONTORNO_VOLUMEN_CIRCUITO.md); carga real, no loudness impuesta |

`Parameters::new` sustituye loudness de frontera por0 porque se resuelve
el contorno. Los placeholders algebraicos de la cadena no son fuentes
externas nuevas; permanecen los mismos campos del laboratorio. Ninguna
constante anterior es un ajuste a una grabación o un preset de fábrica.

## Reloj, fuentes y export

Tick=125 ns/65536. Eventos:8.438 ms KEY0/contactoabierto;
8.442 ms KEY10 V/contactocerrado;9.942 ms KEY0/contactoabierto.
Final11.442 ms: duración nueva reejecutada3.004 ms en ventana ya admitida.
No son notas MIDI: KEY dispara el contorno y los CV del VCO no cambian.
`Recipe::apply` exige el reloj exacto y el decay correcto; cambia únicamente
fuentes, conserva todas las cargas/estado y propuesta. Tres regresiones
propias: parámetros/cargas, historia/metadata y eventos/atomicidad.

Once cortes idénticos al calendario admitido: reposo4 µs, cinco cortes cada
.3 ms durante gatillo, cinco cada.3 ms después. `advance_to` sólo acepta un
par por llamada; iterar hasta cada target y aplicar el próximo evento allí.
Motor y Workspace públicos; I/O únicamente en el ejemplo offline.

Export binario LE: RFJ7TR01 + registros(u64ticks,5f64[J7,saw,ramp,BUS,cursor]);
RFSTPS01 + registros(u64inicio,u64final,u32half,u32attempts,f64LTE,u32next);
RFGRID01 +12 registros(u64ticks,458f64HIGH/LOW). Primera muestra de la historia,
dos endpoints finos por accepted; sin sustituir la onda del circuito.

## Gates y presupuesto

Una rlib nueva sin cache Cargo; tres tests propios y cuatro de ownership
reejecutados con esa rlib. Cuatro recorridos ON/OFF1/2 µs; comparar todos
los clocks/STEP/LTE/propuestas, cinco observables y12 estados completos
contra los exports admitidos. Comparación IEEE-754 por bits, sin cercanía.
Replay exacto de ON1 µs. No exporta cada solve activo o todos los estados
internos entre cortes, ni hereda un grafo nuevo por esos cinco observables.

32 MiB máximo de outputs nuevos; reserva1 GiB, stack experimental32 MiB.
Compilación≤120 s, perfil≤990 s con guard900 s, campaña≤4000 s. Preservar
fallo/replay/fuentes antes de reparar. Las fuentes y7981 privados anteriores
se verifican por SHA; exports y auxiliares nuevos se añaden al inventario.

## Adaptación audible

Guardar voltios crudos. WAV mono PCM16 a48 kHz, escala fija0.01 V/FS,
sin normalización, saturación, DC removal, fades o repetición. Filtrar la
interpolación lineal de endpoints por sinc a18 kHz con ventana Blackman,
soporte±32/Fs, normalización de kernel. Prolongación constante sólo para
la convolución en los bordes, declarada; no es circuito simulado adicional.
Cuadratura Gauss-Legendre8/16: diferencia≤0.25 LSB y PCM≤1 LSB, antes de
publicar; kernel probado con señal constante y rechazo de clocks inválidos.

Frames=floor(duración·Fs), centros(n+.5)/Fs; publicar truncamiento final
y duración WAV separados. Dos adaptaciones por decay desde1 µs: tiempo
nativo y microscopio100× (mismas tensiones, frecuencia/tiempo100×más lentos).
Los100× no son una envolvente original, una nota musical o una mayor ventana
del circuito. No demuestra fidelidad física, periodicidad o DSP/RT.

Siguiente: medir una ventana propia más larga y funcional, con eventos y
comparación temporal, antes de escuchar una nota de duración musical.
