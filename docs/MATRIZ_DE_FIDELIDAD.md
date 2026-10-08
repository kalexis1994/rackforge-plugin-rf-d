# Matriz de fidelidad vigente

2026-10-08. [Perfil CA3046 documental nominal](OBJETIVO.md); no hay acceso
físico presente o futuro. Los parámetros activos, tolerancias y población
vintage conservan sus incertidumbres. Equivalencia numérica con un oráculo
no significa identidad sonora con el hardware.

| Bloque | Topología / cálculo disponible | Implementación o contraste actual | Brecha siguiente |
|---|---|---|---|
| Teclado/glide/ruedas | Alcance del manual y controles de laboratorio | Fuentes impuestas | Leyes eléctricas y comportamiento mono/legato |
| VCO1 | CA3046, convertidor, Schmitt/reset, ondas y panel trazados | [Oráculo funcional y calibrado](VCO1_RESULTADOS_CIRCUITO.md), parámetros condicionados | Núcleo nativo con carga cerrada; panel/CV/rieles completos |
| Cargas de juntura VCO | Leyes de las tarjetas condicionadas | [Depleción nativa](VCO_CARGA_JUNTURA_RESULTADOS.md), Q/C/ΔQ/I/G y derivadas en 1280 casos | Transporte/difusión, térmica y BJT/JFET completos |
| BJT de VCO | Subset condicionado de las tarjetas NPN/PNP | [Stamp de cuatro terminales](VCO_BJT_NOMINAL_RESULTADOS.md), transporte/difusión/depleción a 25 °C; 1536 vectores y doce probes SPICE | No identifica población física; JFET/741 e integración pendientes |
| JFET de VCO | Una mitad E402 nominal, B=1, cargas GS/GD físicas | [Stamp de tres terminales](VCO_JFET_NOMINAL_RESULTADOS.md), 2028 vectores, inversión y doce probes SPICE | Fuente común de ambas mitades en el circuito, 741 e integración; matching físico no identificado |
| LM741 de VCO | Macromodelo TI nominal y defaults ngspice a 25 °C | [Stamp completo de 37 incógnitas](VCO_741_NATIVO_RESULTADOS.md), cinco memorias, 60 stamps y seis raíces independientes | Newton y trayectoria propios, integración VCO; no equivalencia física del integrado |
| Puerto LM741 | Mismo macromodelo nominal, memoria por candidato | [Solver dinámico cargado](VCO_741_PUERTO_RESULTADOS.md), nueve trayectorias/672 pasos y 371 solves locales SPICE; cinco tangentes | Acoplamiento real en VCO; LTE/continuo y RT no admitidos |
| VCO2/VCO3 | Alcance documental | Sin núcleo nativo de voz admitido | Derivación y bancos propios |
| Ruido/modulación | Hipótesis/manual | Sin cálculo completo admitido | Topología, espectro y destinos |
| Mezclador ON | Cinco rutas y contactos límite de la red nominal | [837 casos con C27](MEZCLADOR_C27_RESULTADOS.md); [puerto directo 5×5 a 125 ns](MEZCLADOR_DIRECTO_RESULTADOS.md) | Generadores con impedancia real, OFF y taper |
| Ladder/VCAs/salida | Q29/Q30, ladder, recuperación, C10, dos VCAs y ruta J4/J5/J7 | [Entrada directa ON/C27 nativa](MEZCLADOR_DIRECTO_RESULTADOS.md), ambos R61, 12 escenas/192 pasos y zona previa; algoritmos anteriores conservados | Controles y fuentes completos; población física y RT |
| Contorno de volumen | Gatillo, seguidor y cargas documentados; laboratorio con rechazos conservados | [Puerto C2/reset cargado](PUERTO_CONTORNO_CADENA_71.md); C2/reset aún impuestos en el nativo de 71 nodos | Conmutación estable e integración del contorno completo |
| Contorno de filtro | Alcance y puntos de entrada documentados | Frontera impuesta | Circuito y banco propios |
| Voz SPICE conjunta | VCO1 y cadena con contorno de laboratorio | [Cuatro escenas cortas admitidas](VOZ_SEIS_ACTIVO_RESULTADOS.md); [largo rechazado y auditado](VOZ_SERIAL_CAMPANA_RESULTADOS.md), una de cuatro completa | Contrastes largos sin medir; causas de abortos pendientes |
| Audio / producto | Escuchas de alcance parcial conservadas | Sin voz nativa instalable admitida | Voz completa, adaptador de escucha, deadlines, host y paquete |

El [VCO1 nativo ensamblado](VCO1_STAMP_RESULTADOS.md) conserva 134
incógnitas, dos 741 completos, BJT/JFET, Schmitt/reset y cargas del panel.
40 casos y todas las derivadas admiten el stamp, con arranque DC C1=0
condicionado y snapshots SPICE. No admite DC libre, arranque calibrado
rechazado, arranque propio, ciclos completos o refinamiento nativo.
El [Newton conjunto](VCO1_NEWTON_RESULTADOS.md) pasa dos DC condicionados
y seis continuaciones libres de 8 us/224 pasos desde semillas importadas
de laboratorio; no identifica periodos o eventos de reset.
El [arranque propio posterior](VCO1_ARRANQUE_RESULTADOS.md) sí pasa diez
raíces desde circuito e incidencias independientes. Los ciclos de paso
fijo se rechazan en el reset. La copia privada con subpasos completa 30ms,
pero no pasa dispersión entre períodos y no es producción admitida.
El [stamp de subpasos/control temporal](VCO1_SUBPASOS_RESULTADOS.md)
verifica48 stamps y28 raíces disponibles;20 raíces independientes fallan.
La campaña del controlador se rechaza por precisión de representación,
con KCL fuera de gate y corrección menor que1ULP en la referencia −4V.

El [bloque de incrementos](VCO1_INCREMENTOS_RESULTADOS.md) recupera
50 raíces con memoria hi/lo y referencia completa Decimal100. El
controlador mantiene los gates y transporta ambas componentes. Campaña
rechazada a 2,434338 ms por LTE confirmado en Q6 (2,013 µV > 2 µV).
No admite ciclo completo/refinamiento; sigue grilla más fina. Pila de
laboratorio 8 MiB declarada; heap cero no admite RT.

## Estado de la nota larga

El [preflight02](../evidence/voice_serial_preflight02.json) admitió recursos,
no el circuito. Gear500/Gear250/Trap125 se detuvieron a
136,630269/150,293268/15,940421 ms; Gear125 completó 350 ms. La
[auditoría final](VOZ_SERIAL_CAMPANA_RESULTADOS.md) conserva los cuatro recibos y
archivos. Banco rechazado, tres parejas no medidas y ningún error de
recursos/almacenamiento. Los prefijos no cubren tiempo ausente.

El [diagnóstico Gear500](../evidence/voice_serial_prefix_nominal50001.json)
y la [auditoría decimal](../evidence/voice_serial_prefix_decimal01.json)
conservan reloj y 15 vectores bit a bit frente al candidato anterior;
las otras tres columnas difieren hasta 4,24×10⁻²² V. No hay identidad bit a
bit global ni causa de aborto demostrada. El mensaje de Q7 no diagnostica
por sí solo todo el sistema.

## Cómo interpretar las admisiones

- **Topología:** conexiones y valores respaldados para la revisión declarada.
- **Cálculo:** pasa los escenarios/gates de su protocolo con hipótesis explícitas.
- **Nativo:** implementación y memoria contrastadas para ese subconjunto.
- **Audio externo:** requiere procedencia y condiciones comparables; permanece abierto.
- **RT/producto:** deadline, recursos y flujo de host deben medirse; permanecen abiertos.

La [QA reciente](../evidence/voice_vco1_newton_tests01.json) cubre 220,
con tres ejecuciones nuevas y 217 heredadas. No convierte los nominales
BJT/JFET en parámetros de un instrumento real. R61=200 Ω/200 kΩ sigue siendo
una discrepancia documental; α no identifica taper y ramas omitidas no
representan contactos OFF. Mantener manuales/audio/binarios en local ignorado.

El [historial de esta matriz](MATRIZ_DE_FIDELIDAD_HISTORICA_2026-10-07.md)
conserva todos los estados y resultados anteriores. El
[snapshot por hash](../evidence/voice_documentation_snapshot01.json)
respalda esa copia exacta; ningún algoritmo, dato numérico o gate cambia.
