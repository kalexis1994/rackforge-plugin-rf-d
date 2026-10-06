# Siguiente corte de la voz refinada

2026-10-06. Protocolo prospectivo; ninguna escena nueva de este documento
se cuenta como medida. Requiere la [auditoría del banco corto](VOZ_REFINAMIENTO_UNION_RESULTADOS.md).

## Gate de entrada

La extensión temporal sólo procede con identidad desactivada, control
activo y las cuatro escenas conjuntas de 40 ms admitidas, incluidos los
tres contrastes y balances de ambos C2. Si cualquiera rechaza, el próximo
trabajo será reproducir su export y localizar la diferencia o el aborto,
con fuente/deck/recibo nuevos y sin aflojar límites. Una medida adicional
no sustituye un rechazo ni cambia retroactivamente el banco corto.

## Nota completa de 350 ms, si pasa el banco corto

Conservar build08, tres correcciones, KLU, tarjetas y tolerancias del
banco corto. No modificar trim, CV, cutoff, EMPHASIS, Q21, cargas,
alimentaciones, ataque 10 kohm, decay 100 kohm, sustain inferior 2500 ohm
o decay final ON. Extender duración a **350 ms**, teclado ON desde **10 ms**
y OFF desde **200 ms**, ambas transiciones **10 µs**. Es el patrón de
frontera del banco largo de contorno; ahora el VCO también se resuelve.
No supone que el release termine a 350 ms.

Medir Gear2 500/250/125 ns y Trap2 125 ns desde DC propio, nunca continuar
desde un export corto o unir estados de escenas distintas. Reconstruir
el deck base histórico por SHA y cambiar sólo duración, dos tiempos de
teclado, política temporal y export en anclajes únicos comprobados.
Registrar un diff de deck explícito y todo byte fuera de esos anclajes.
Retener los 18 vectores del banco corto; añadir uno sólo con propósito
de medición declarado y sin alterar la red.

Presupuesto fijo **7200 s por proceso** por la duración mayor. No es un
nuevo límite de Newton. Separar timeout, aborto, export incompleto y
fallo de medición. Antes de ejecutar, estimar tamaño a partir de bytes
y filas reales del banco corto y verificar espacio libre para conservar
los cuatro exports completos, más 2 GiB de margen; registrar esa cuenta.
No borrar fuentes, builds o rechazos para ocultar un límite de recursos.

## Gates congelados para las tres parejas

Exigir reloj finito estrictamente creciente desde cero, 350 ms completos,
paso máximo propio, activación confirmada y hashes de fuente/runtime
antes y después. Pares: 500→250 ns, 250→125 ns, Gear2→Trap2/125 ns.

- Frecuencia después de 10.01 ms: diferencia ≤1 cent por cruces
  ascendentes de rampa a −2 V; informar cantidad y dispersión de períodos.
- C2 de contorno, salida del seguidor, BUS, recuperación y salida principal:
  máximo ≤5 mV en grilla absoluta de 5 µs durante 0–350 ms, sin alineación.
- RMS AC de salida: diferencia ≤1% del segundo miembro +10 µV en cada
  ventana: reposo 2–8 ms, ataque 20–80 ms, held 120–190 ms,
  release 230–340 ms. Quitar únicamente la media de cada ventana.
- Defecto de carga acumulado de ambos C2: máximo ≤0.1 nC sobre toda
  la trayectoria no uniforme, incluidos eventos y carga del seguidor.

Los cuatro escenarios deben pasar cobertura y balance; las tres parejas
deben pasar todos los límites. Informar también DC, picos, contorno held
y valor final, sin imponer objetivos retrospectivos de amplitud o duración.
Held no equivale a sustain asentado. No extrapolar una grilla a una cota
continua de los eventos rápidos.

## Escucha posterior a la admisión y auditoría

Sólo después de los gates, adaptar **los 350 ms completos** de salida
principal del nominal Gear2/125 ns. Interpolación lineal del reloj a
384 kHz; FIR simétrico 1025 taps, Kaiser beta 8.6, cutoff 21600 Hz,
padding reflejado y delay compensado; decimación a 48 kHz. Media global
retirada, escala fija 8 V/full scale, fades de 10 ms, PCM16 mono:
**16800 frames**. Rechazar no finitos, clipping o número de frames distinto.
Conservar antes/después de DC/FIR, pico y todos los hashes. No normalizar
por pico, repetir ciclos, sintetizar fase ADSR o rellenar un prefijo.

La primera escucha tendría una nota de VCO/ladder/ambos VCA/contorno
resueltos bajo fronteras de laboratorio. No admite otras notas o extremos
de panel, contorno de filtro, fuente compartida real, piezas vintage,
portabilidad nativa o deadline. Los controles reservados, otras fuentes
y la extensión de escucha tendrán bancos separados con gates previos.
