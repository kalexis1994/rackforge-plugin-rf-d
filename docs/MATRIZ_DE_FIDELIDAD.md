# Matriz de fidelidad vigente

2026-10-07. [Perfil CA3046 documental nominal](OBJETIVO.md); no hay acceso
físico presente o futuro. Los parámetros activos, tolerancias y población
vintage conservan sus incertidumbres. Equivalencia numérica con un oráculo
no significa identidad sonora con el hardware.

| Bloque | Topología / cálculo disponible | Implementación o contraste actual | Brecha siguiente |
|---|---|---|---|
| Teclado/glide/ruedas | Alcance del manual y controles de laboratorio | Fuentes impuestas | Leyes eléctricas y comportamiento mono/legato |
| VCO1 | CA3046, convertidor, Schmitt/reset, ondas y panel trazados | [Oráculo funcional y calibrado](VCO1_RESULTADOS_CIRCUITO.md), parámetros condicionados | Núcleo nativo con carga cerrada; panel/CV/rieles completos |
| VCO2/VCO3 | Alcance documental | Sin núcleo nativo de voz admitido | Derivación y bancos propios |
| Ruido/modulación | Hipótesis/manual | Sin cálculo completo admitido | Topología, espectro y destinos |
| Mezclador ON | Cinco rutas y contactos límite de la red nominal | [837 casos con C27](MEZCLADOR_C27_RESULTADOS.md); [puerto cargado 5×5](MEZCLADOR_PUERTO_CARGADO_RESULTADOS.md) | Generadores con impedancia real, OFF y taper |
| Ladder/VCAs/salida | Q29/Q30, ladder, recuperación, C10, dos VCAs y ruta J4/J5/J7 | [Cierre ON/C27 nativo](MEZCLADOR_CADENA_RESULTADOS.md), ambos R61, cuatro escenas/64 pasos; algoritmos anteriores conservados | Controles y fuentes completos; población física y RT |
| Contorno de volumen | Gatillo, seguidor y cargas documentados; laboratorio con rechazos conservados | [Puerto C2/reset cargado](PUERTO_CONTORNO_CADENA_71.md); C2/reset aún impuestos en el nativo de 71 nodos | Conmutación estable e integración del contorno completo |
| Contorno de filtro | Alcance y puntos de entrada documentados | Frontera impuesta | Circuito y banco propios |
| Voz SPICE conjunta | VCO1 y cadena con contorno de laboratorio | [Cuatro escenas cortas admitidas](VOZ_SEIS_ACTIVO_RESULTADOS.md); [largo rechazado y auditado](VOZ_SERIAL_CAMPANA_RESULTADOS.md), una de cuatro completa | Contrastes largos sin medir; causas de abortos pendientes |
| Audio / producto | Escuchas de alcance parcial conservadas | Sin voz nativa instalable admitida | Voz completa, adaptador de escucha, deadlines, host y paquete |

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

La [QA reciente](../evidence/voice_mixer_chain_port_tests01.json) cubre 185,
con tres ejecuciones nuevas y 182 heredadas. No convierte los nominales
BJT/JFET en parámetros de un instrumento real. R61=200 Ω/200 kΩ sigue siendo
una discrepancia documental; α no identifica taper y ramas omitidas no
representan contactos OFF. Mantener manuales/audio/binarios en local ignorado.

El [historial de esta matriz](MATRIZ_DE_FIDELIDAD_HISTORICA_2026-10-07.md)
conserva todos los estados y resultados anteriores. El
[snapshot por hash](../evidence/voice_documentation_snapshot01.json)
respalda esa copia exacta; ningún algoritmo, dato numérico o gate cambia.
