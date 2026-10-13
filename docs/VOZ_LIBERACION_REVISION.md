# Revisión documental del reset de volumen

Revisión visual de fuentes privadas originales, no nuevos parámetros o
equipo físico. SVC-204D PDF pp12–14 (§2.9/2.10, impresas2-7..2-9) y p65;
SVC-9 PDF p9. Renders nuevos de Poppler y ampliación de p65, hashes y comandos
en [el recibo](../evidence/voice_release_review01.json). PDFs/PNG quedan ignorados.

## Recorridos verificados

- Teclado por CR10/R60 carga C7; R55 alimenta baseQ20. El contacto S-trigger
  actúa sobre el nodo de colectorQ20 por R49. Son caminos eléctricos distintos.
- ColectorQ20 gobierna baseQ12. ColectorQ12, con R25 de pullup, llega a Q25
  por R28/C4: acoplamiento del pulso, no asignación digital de estado.
- ColectorQ20 también llega por R36/CR8 a baseQ15. Cruza el camino C4 sin
  unirse a su terminal derecho; la orientación de CR8 permite el reset
  hacia Q15. R38/R56 forman la realimentación entre Q25/Q15.
- Q25 colector gobierna la red de ataqueQ16 y el driver de decayQ17/Q18.
  C2 recibe corriente por los controles de ataque/decay y carga al seguidor
  Q3/Q2. La baseQ18 de placa4 conserva su carga real por R59.

La descripción funcional indica reset/off sin gatillo, ataque mediante
acoplamiento AC y final decay tras liberar; asigna comportamiento equivalente
al contorno de volumen. No cuantifica el retardo de esta escena, ni permite
convertir el instante KEY0 en un reset ideal. La trayectoria de C7, corriente
R36/CR8, estado Q25/Q15 y balance de C2 son las observaciones para comprobarlo.

## Conflictos y corrección de localizador

El texto tiene designadores que no se trasladan literalmente al esquema
de volumen (por ejemplo el switch de decay llamado Q13); mantener aliases
por posición. R25 esquema3.3 kΩ/BOM1 kΩ y designador de resistor a baseQ12
siguen como conflictos anteriores. Tarjetas Is/β/T, cargas de juntura,
9.3 V impuesto y potenciómetros eléctricos10/100 kΩ siguen condicionados.

La nota de [la documentación anterior](CONTORNO_VOLUMEN_CIRCUITO.md) identificó
p65 como Fig9-5. La revisión directa confirma **Figure9-7** en ambas copias;
**9-5 es la página impresa**, no el número de figura. Se conserva el documento
anterior por bytes y se registra aquí la corrección de localizador, sin
cambiar grafo, parámetros o gates. Páginas PDF65 y9 siguen siendo correctas.

Si la continuación calcula conmutación y descarga, será consistencia del
modelo condicionado con ese recorrido y descripción. No acredita tiempos
de una unidad vintage, fidelidad audible o completitud de la voz.
