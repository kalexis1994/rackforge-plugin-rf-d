# Programa de frecuencia y KEY para la fuente nominal

## Alcance previo

Extensión de laboratorio del ciclo CA3046/SVC-204D nominal admitido en
[VCO de fase](VCO_FASE_NOMINAL_PROTOCOLO.md). El ciclo DRIVE/TRI y su
frecuencia/época provienen del circuito; su transposición temporal es un
adaptador musical experimental. No demuestra otras formas/corrientes
del VCO físico ante CV, trims, modulación o carga dinámica. Conservar la
incertidumbre de esa reducción, sin atribuirle calibración MIDI/teclado.
Fuente eléctrica de la red de salida: SVC-9 pp.5/19, R6/R45 una sola vez.
Cadena/contornos/FIR de [render](NOMINAL_RENDER_PROTOCOLO.md), sin cambios.

Frecuencia nominal f0 de vco_phase_profile, en Hz. Dominio del adaptador
[f0/2, 2 f0], finito; fase en ciclos. Programa fijo de hasta ocho eventos,
ordenados, únicos, a microsegundo entero y anteriores al final. Primer
evento t=0, f0, KEY OFF: conservar el DC anterior. Final múltiplo de
125 us hasta 301 ms. Cada evento reúne frecuencia y estado KEY; KEY ON
10 V/OFF 0 V sin reiniciar C2/C5 o ninguna memoria del circuito.

En un segmento de frecuencia constante, phi(t)=phi_e+(t-e) f. Al cambiar
frecuencia, calcular phi_e con la ley anterior en e, conservando fase.
Gate sin cambio de frecuencia conserva la ley anterior y sus bits.
El segmento inicial usa exactamente (t-epoch) f0 de la referencia;
no sustituirlo por una suma algebraicamente equivalente con otro redondeo.
Evaluación inmutable por tiempo absoluto: Newton puede consultar etapas
fuera de orden sin avanzar un acumulador o publicar fase de un rechazo.
No suavizar el reset del ciclo ni reiniciar fase al cambiar nota.

Derivar variantes del motor/arranque/lector/productor mediante reemplazos
acotados y verificables, manteniendo intactos los fuentes admitidos.
Sólo pasar la ley de fase como parámetro, convertir parámetros eléctricos
a la misma estructura y cortar los pasos en eventos del programa.
Conservar Newton, cargas, memoria HIGH/LOW, estimador, interpolación,
red de cuatro terminales, FIR, latencia y propiedad del Accepted pendiente.
Máximos de diagnóstico 2/1 us; si ese contraste falla, registrar fallo y
replay y comprobar 1/0.5 us bajo los mismos gates antes de admitir avance.
La selección por defecto del laboratorio sigue fina, sin promoción RT.

## Gates

- Fuente nominal: puertos/tensiones/potencia/admitancias idénticos por
  bits al observador admitido en 4097 tiempos, con BUS variable válido.
  Fases de programas frente a Decimal100 <=1e-12 ciclos; continuidad en
  cada retune por bits. Control negativo de reiniciar época debe diferir
  >1e-3 ciclos en algún cambio. Invalidar dominio/tiempo/eventos sin mutar.
  Red estática: suma de corrientes <=2 fA+2e-12|I| y tangente conservativa.
- Nominal real 0–10 ms, KEY ON 1 ms: motor con programa y control anterior
  independiente fino 1 us. DC/estado HIGH/LOW, todos los Accepted completos,
  incrementos/etapas/diagnósticos y RAW/AA8 iguales por bits. Comparar el
  prefijo archivado fino; conservar todos los parámetros y relojes.
- Programa real 0–24 ms: KEY ON 1 ms; f0→1.5 f0 en 6.25 ms y →0.5 f0 en
  12.5 ms sin soltar KEY; OFF 18.75 ms. Cuerpo hasta 23 ms, soporte hasta
  24 ms. Cortes exactos de los eventos, memoria intacta y fase continua.
  Cuotas/capacidad cero, pending al primer Frame, retry con cuota cero y
  Clone/workspace nuevo. Comparar todas las muestras/índices con batch FIR.
- Newton <=1 pA/2 nV, estimador <=1, heap cero medido en procesamiento.
  Refinamiento eléctrico 2/1 us en conjunto y ventanas 1–6.25, 6.25–12.5,
  12.5–18.75 y 18.75–23 ms: RMS relativo <=.001, máximo/pico <=.003,
  media <=1 uV; pre-KEY absoluto <=1 uV. Mismos gates para fallback 1/.5.
- Tasa 192/384 kHz sobre la misma historia, FIR admitidos: RMS relativo
  <=.0001, máximo/pico <=.0003, media <=.1 uV en esas ventanas. Eso no
  demuestra ausencia universal de alias ni banda de otras transposiciones.
- Cuatro tests nuevos: ley de fase/continuidad, entradas inválidas,
  validación de programa y selección de frontera. Sólo ejecutar esos
  cuatro; heredar tests anteriores y comprobar equivalencia estructural.
- No otro WAV o nota larga; conservar escucha anterior por hash. Un único
  tmp/lab-current vacío al terminar, compiler/rlib congelados, sin Cargo,
  cache, inputs sonoros privados o librería nuevos. Recibos <=8 MiB sin QA.
  Preservar fallo, fuentes/input y replay antes de cambiar el experimento.
  No declarar nuevas filas originales si sólo se heredan por identidad.

La admisión será del adaptador y de las escenas ensayadas, manteniendo
separada la fuente nominal activa anterior. No convierte este programa
en VCO físico general, plugin tocable o respuesta musical calibrada.
