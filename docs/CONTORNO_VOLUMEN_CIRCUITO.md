# Contorno de volumen: circuito y límite del biestable

## Perfil y fuentes

Se transcribe el contorno de volumen de placa 2 de **SVC-9 PDF p. 9, Fig. 9-7**, su gatillo común y el cableado de panel de **p. 19, Fig. 9-17**. La copia SVC-204D completa contiene el mismo esquema en **p. 65, rotulado Fig. 9-5**: los identificadores de figura difieren entre copias. Valores de placa: SVC-9 tabla 7-6 pp. 26–27; controles: tabla 7-3 p. 21; conexión de decay final y jack normalizado: Fig. 9-15 p. 17. Descripción funcional: SVC-204D §2.10 pp. 13–14; conexión al primer VCA: §2.9 p. 12.

Los escaneos se revisaron completos y mediante ampliaciones de pines, polaridades y cruces. Quedan sólo en `references-local/contour-review/`, ignorado. El [grafo legible por máquina](../evidence/loudness_contour_graph.json) contiene terminales, unidades, piezas, puertos, fuentes y conflictos. No redistribuye el dibujo.

## Recorridos eléctricos

| Bloque | Conexiones que lo reconstruyen |
| --- | --- |
| Gatillo de teclado | Pin 20 → CR10 → R60 → C7 a masa → R55 → base Q20; emisor Q20 a masa. Q20 colector tiene R23 hacia alimentación y gobierna Q12 por el resistor de base conflictivo. |
| S-trigger | Pin 19 → R49 → colector Q20. Contacto externo cerrado pone su extremo a masa; abierto elimina esa rama. No equivale al V-trigger positivo del teclado. |
| Reset común | Q12 emisor a masa; colector por R25 a alimentación. Colector Q12 → R28/C4 → base Q25. Colector Q20 → R36/CR8 → base Q15 (revisión independiente 2026-10-06). CR9 lleva el reset a la referencia de sustain. |
| Biestable | Q25/Q15 emisores a masa. R38: colector Q15 → base Q25; R39: alimentación → colector Q15; R56: colector Q25 → base Q15. CR6 realimenta desde el divisor R24/R27 de salida hacia Q15. |
| Ataque | Alimentación → emisor PNP Q16; R41/R40 fijan su base desde colector Q25. Colector Q16 → R42 de placa → R13 de panel → C2 a masa. |
| Decay | Colector Q25 → base Q17; Q17 colector a alimentación, emisor por R43 a −10 V y por R44 a **base** Q18. Q18 colector → R16 de panel → C2; Q18 emisor a referencia de sustain. |
| Sustain | R19 de panel: +10 V → cursor → masa, total 5 kΩ. Cursor → R51 → base PNP Q19, con shunt de 4,7 kΩ a masa. Emisor Q19 establece referencia Q18; colector Q19 descarga por R46 a masa. CR9 ánodo en esa referencia y cátodo al reset. |
| Seguidor | C2 → R16 de **placa**, 10 kΩ → base Q3. Emisor Q3 → base Q2. Ambos colectores comparten alimentación por R15 de placa, 560 Ω. Emisor Q2 es salida pin 7. R24 une salida a feedback; R27 lleva feedback a −10 V. |
| Decay final | ON abre rama rápida CR4. OFF conecta C2 → CR4 → resistor LHC 1,5 kΩ → reset. La rama por R16 de panel sigue presente. No se reinicia C2 ni se fuerza la salida a cero. |
| Carga posterior | Pin 7 de placa 2 → pin 9 de placa 4 → R59, 68 kΩ → base Q18 de **placa 4**. Es una carga activa con corriente de base; no un shunt de 68 kΩ a masa. |

**R16 de panel y R16 de placa son piezas distintas. Q18 de placa 2 y Q18 de placa 4 también.** En el dibujo, el transistor Q18 girado tiene la base abajo en R44, no en la referencia de sustain. El seguidor Q3/Q2 de volumen es NPN/NPN; el del filtro Q22/Q21 incluye PNP y requiere derivación propia.

## Valores y conflictos preservados

- C2=10 µF, +50/−10 %; C4=0,01 µF y C7=0,1 µF, ±10 %. La memoria guarda voltajes orientados por los terminales del grafo; carga `q=C·v`, en C.
- R13 y R16 de panel: 1 MΩ, ley de audio; R19: 5 kΩ lineal. El programa recibe **resistencias eléctricas**, sin inventar una curva posición→Ω. Topes cero se unen como nodos exactos, sin resistencias epsilon. La regresión de unión no acredita aún convergencia de todo el contorno en esos topes.
- R25 de gatillo: 3,3 kΩ en esquema, 1 kΩ en BOM. Resistor a base Q12: dibujo aparenta R9/10 kΩ, mientras R9 también nombra 4,7 kΩ en filtro y BOM. Hay duplicaciones de R41 y R60 entre etiquetas/lista. Se usan alias por posición y se exponen candidatos; no se adjudica una revisión física a ninguno.
- La alimentación de contornos de ~9,3 V proviene del seguidor Q26 desde riel bruto +15 V, según §2.10 p. 14. Aquí **se impone** 9,3 V: Q26/R62/R63 y el riel bruto no están cerrados.

## Actualización: contorno cargado con memoria de dispositivo

El [banco SPICE posterior](CONTORNO_PLACA4_RESULTADOS.md) resuelve contorno,
gatillo y placa 4 con carga Gummel–Poon condicionada. Diez escenas y tres
contrastes pasan; conserva entrada de audio, alimentación y Q21 impuestos.
No reemplaza los gates de los modelos históricos siguientes ni identifica
semiconductores vintage.

## Primer oráculo, alcance exacto

[`loudness_contour_reference.py`](../tools/loudness_contour_reference.py) cierra 28 voltajes desconocidos en el caso interior, diez BJTs y cinco diodos con decay final OFF (cuatro ON). Se omiten las cargas del contorno de filtro sobre los gatillos comunes, las capacitancias de juntura, fugas adicionales y rebotes. La salida puede recibir corriente o carga resistiva impuesta. No hay selector de fase ADSR, temporizador de ataque ni tabla de curvas.

BJTs: Ebers–Moll con `Is=10⁻¹⁴ A`, `βF=100`, `βR=5`, `T=298,15 K`. Diodos: Shockley con `n=1,5`, `Is=10⁻⁸ A` para 1N34A y `10⁻¹² A` para 1N4004. **Todos son supuestos de laboratorio sin identificación vintage**, incluyendo la temperatura de juntura. Los límites de exponencial 45, Newton 80 iteraciones/24 divisiones y las semillas son decisiones numéricas, no piezas ni leyes audibles. Se conserva el método Ebers–Moll/Nagel–Pederson ya registrado en [FUENTES](FUENTES.md).

La KCL suma corrientes salientes. Cada capacitor estampa Euler implícito:

```text
I(a→b) = C/dt · [(Va−Vb) − v_anterior]
```

Todos los intentos retienen las mismas tres cargas y el mismo `dt`. Se acepta sólo con KCL <10 pA y corrección Newton completa <10 nV. CR10 necesita una semilla algebraica finita al saltar la fuente de teclado; no se altera C7. Una solución candidata se devuelve como estado nuevo; un fallo conserva el objeto anterior.

## Resultado que impide promover el contorno

La [sonda reproducible](../tools/loudness_contour_probes.py) prepara reposo, avanza doce intervalos de 1 ms y aplica +10 V al teclado desde intervalo 10. **En intervalo 12, la semilla anterior agota Newton. Dos semillas diferentes cierran la misma KCL con el mismo historial, pero producen raíces distintas.**

El [informe](../evidence/loudness_contour_fold.json) retiene ambas raíces, los rechazos y `selected=null`. La diferencia máxima entre raíces es **4,963694 V**; colector Q25 resulta ~3,836036 V o ~0,021881 V. La salida inmediata difiere ~1,576 mV. Jacobianos obtenidos por diferencias finitas centrales reproducen ambos resultados y los doce pasos previos con error máximo **2,66×10⁻¹⁵ V**. Esto es reproducción del modelo algebraico condicionado; no demuestra unicidad, estabilidad dinámica del biestable ni sonido correcto.

La ruta habitual `step` **no elige una raíz alternativa**. `probe_step_roots` sólo enumera soluciones. Antes de integrar el contorno a la voz hace falta estudiar estabilidad y dinámica de conmutación, con las capacitancias relevantes, contrastar semillas y refinar el tiempo. No se añade un reset o un toggle digital para ocultar este límite.

## Regresión y próximos cierres

Actualización: el [cierre cargado de 94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) ya incorpora R59/Q18 y todas las cargas de audio. Una [búsqueda más amplia](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) encuentra **tres** raíces del mismo paso; las dos anteriores eran las observadas con sus semillas iniciales. La dinámica de juntura omitida puede ocultar un modo creciente en la intermedia. La conmutación física sigue sin admitir.

```powershell
python tools/loudness_contour_probes.py
python -m unittest discover -s tests -p test_loudness_contour_reference.py -v
```

Tres pruebas: reproducción independiente de la ambigüedad, las 28 columnas del Jacobiano/cargas/atomicidad y unión exacta de topes/dominos inválidos. RACE: C1 parcial documentado y C5 de reproducción numérica local; C2/C3 del circuito completo, conmutación, tolerancias pobladas, C6 y C7 abiertos.

Siguiente bloque independiente: seguidor Q3/Q2 con feedback CR6 y carga de salida, conservando la corriente tomada de C2. Después: estabilidad del biestable, alimentación compartida, contorno de filtro y cierre simultáneo con el VCA. El límite físico del contorno no desaparece por portar el seguidor.
