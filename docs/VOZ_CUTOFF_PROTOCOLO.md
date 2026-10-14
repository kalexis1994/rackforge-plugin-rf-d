# Cutoff cargado: cierre y reapertura del panel

2026-10-14, base `59b60328b27f812a76e5bc6589ddf629fd30ba22`, QA `voice_retrigger_tests01.json`. Perfil vintage CA3046 documental, sin unidad física. Biblioteca assembly congelada, sin modificarla ni recompilarla.

## Pregunta y receta

Ejercitar el panel de cutoff en la voz VCO→BUS→ladder/VCA→J7, conservando el contorno de volumen, estado de filtro y cargas de salida. Desde cada final propio a 156,446 ms: continuidad de 4 µs con α=1, 8 ms con α=0,5 y 8 ms de vuelta a α=1. KEY 0 V/S abierto/decay ON/R16 1 kΩ y CV del VCO permanecen fijos. α es la fracción eléctrica desde −10 V del potenciómetro de 5 kΩ, dominio [0,1], no Hz ni escala musical calibrada. Origen: [panel y Q26/Q28](CUTOFF_NATIVO_Q26_Q28.md), `cutoff::reduce_panel`, SVC-9; las demás constantes conservan la [receta nominal](RECETA_CONDICIONADA_PROTOCOLO.md). Contorno de filtro pin16=0 V sigue impuesto: este bloque no conecta un nuevo generador de contorno.

Las duraciones son estímulos de laboratorio. Tick 125 ns/65536, inicio 82022760448 y offsets [0,2097152,4196401152,8390705152]. 16,004 ms nuevos; historia total 164,012 ms y WAV de 164 ms/7872 muestras a 48 kHz, truncamiento de 12 µs. Cortes de 0,8 ms en fases largas, 22 relojes y 25 checkpoints por perfil.

## Estado, red y puertas

Extender la receta RFDCY001→RFCTF001 con un f64 de cutoff: 3736 bytes, estado desde offset72; conservar 458 HIGH/LOW, reloj, propuesta, resistencia y fuentes. Conversión inicial cambia únicamente magic/phase e inserta α=1. Eventos α1→0,5→1 preservan todo lo anterior. Cuatro Accepted completos por resolución en la unión y cuatro después de cada evento deben coincidir por bits con la familia block usando el mismo cutoff.

Máximos de semipaso 2/1 µs; LTE 2 µV/2 nA, veinte intentos. Red original Python/Decimal100 con resistores reales del panel y FD: coarse/mid/end de bordes, resets y TURN/LATCH; KCL 20 pA, restricciones 200 pA, correcciones 1 µV/1 nA. Refinamiento de 229 estados al mismo reloj 2 µV/2 nA; resets ≤10 ns, transiciones ≤100 ns. Flujos C2 completos: balance ≤2 µV/s y componentes seleccionados ≤10 fA. Nueve balances ΔQ orientados ≤1 pA×duración por fase, total y unión desde 8,438 ms; cuadratura de todos los estadios nativa. Restauración/replay hasta 16 Accepted, máximo tres motores sombra; corrupciones/destinos inválidos rechazados atómicamente.

Audio con dos derivaciones completas iguales y refinamiento ≤2 µV/7 LSB; sinc 18 kHz/Blackman, escala 0,01 V/FS y DC heredados. Sin loop, fades o normalización. CLI identifica todas las trazas, checkpoints, código, clocks, eventos y familias; fixtures completos para comprobar rechazos específicos antes de publicación.

## Recursos y alcance

Privados nuevos ≤96 MiB, reserva 1 GiB, stack offline 32 MiB. Perfil ≤1800 s/proceso ≤1900 s, campaña ≤4000 s y auditor ≤600 s. Fallos/fuentes/replay sin cambios conservados antes de reparar. Sin Cargo/cache/SPICE o biblioteca nuevos; no fidelidad física, periodicidad, voz desde silencio, calibración del panel, heap/deadline o RT. El contorno de volumen sigue evolucionando: no atribuir todo cambio entre ventanas de J7 únicamente al cutoff.
