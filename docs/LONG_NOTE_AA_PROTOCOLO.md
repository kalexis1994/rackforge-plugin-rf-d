# Nota nominal larga y conversión con antialias

## Escena, unidades y separación de sistemas

CA3046/SVC-204D y puertos SVC-9 pp.9/19/13/10 del
[arranque](CHAIN_STARTUP_PROTOCOLO.md). Mismas ecuaciones e inicializador.
Un VCO de fase periódico, sierra fija. KEY ON 1 ms, OFF 200 ms; salida
0–300 ms y circuito hasta 301 ms para completar el soporte derecho del FIR.
Conservar estado HIGH/LOW y memorias, sin reiniciar al prolongar la nota.
El prefijo hasta 75 ms coincide con la nota anterior antes de su KEY OFF.

Lectura pasiva de J7 a 384 kHz con el mismo polinomio Radau admitido.
Reloj racional; 115585 puntos hasta 301 ms inclusive. Submuestreo exacto
por dos de esa lectura para el control a 192 kHz, sin otra integración.
Todos los octavos hasta 75 ms deben igualar por bits la lectura previa de
48 kHz de cada máximo eléctrico. Sin pasos forzados a fronteras de audio.

## FIR y fuentes de la derivación

Diseño digital de salida, no componente del Moog ni nueva carga en J7.
Paso 0–20 kHz, transición 20–24 kHz, rechazo desde 24 kHz hasta Nyquist
de entrada. FIR simétrico tipo I, sinc de corte 22 kHz con ventana Kaiser
beta=10,06126. Ganancia DC unitaria de los coeficientes, no normalización
de la señal. 385 coeficientes a 192 kHz y 769 a 384 kHz: semisoporte y
retardo causal de 1 ms en ambos. Tasas de salida 48 kHz, factores 4 y 8.

Con m=-M..M: h[m] proporcional a 2 fc/Fs sinc(2 fc m/Fs)
I0(beta sqrt(1-(m/M)^2))/I0(beta), después dividir por sum(h).
Coeficientes f64 congelados; diseñador NumPy y contraste independiente
Decimal de sinc/Bessel. Estas elecciones son un contrato de conversión,
no constantes audibles atribuidas al hardware. Fuentes primarias:

- DSP-AA-1: [SciPy, firwin](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.firwin.html),
  secciones definición, cutoff, scale y Notes: fase lineal, corte de media
  amplitud y escala DC. No se ejecuta SciPy en este banco.
- DSP-AA-2: [SciPy, ventana Kaiser](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.kaiser.html),
  Notes, ecuación I0 y soporte simétrico.
- DSP-AA-3: [SciPy, kaiserord](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.kaiserord.html),
  Notes/Examples: estimación empírica y necesidad de medir el rechazo.
- DSP-AA-4: [SciPy, resample_poly](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html),
  definición/Notes: filtrar antes de reducir tasa y declarar fronteras.

Conversión offline centrada: compensar el retardo de 1 ms usando futuro
realmente integrado; para tiempo negativo usar J7 inicial constante, cero
en este DC. No inventar ceros al final, cortar colas o desplazar KEY en la
escena eléctrica. 14401 puntos de salida: cuerpo [0,14400) y ancla final.

## Gates fijados antes de medir

- FIR: ripple absoluto <=0,001 dB en 0–20 kHz, rechazo >=90 dB desde
  24 kHz, DC dentro de 1e-12, simetría <=1e-15, retardo 1 ms. Grilla FFT
  densa con extremos de bandas explícitos y cota de interpolación mediante
  sum(abs(m² h[m])); contraste Decimal de coeficientes <=2e-15. No es una
  prueba formal con aritmética de intervalos; declarar redondeo f64.
- Native versus convolución independiente NumPy: máximo <=1e-14 V sobre
  nota y fixtures. Impulso, DC y cosenos 1/19/20/24/30/47/60/90 kHz:
  error frente a transferencia analítica <=1e-11. El bypass de 30 kHz
  debe exponer alias a 18 kHz y fallar el rechazo, sin cambiar gates.
- Nota: máximos eléctricos 2/1 us, Newton 1 pA/2 nV, estimador <=1,
  heap cero, replays exactos y rechazos atómicos. Comparar salida filtrada
  del par en conjunto y ventanas ataque 1–75, sostenido 75–200, liberación
  200–300 ms: RMS relativo <=0,001, máximo/pico <=0,003, media <=1 uV.
  Pre-KEY por diferencia absoluta <=1 uV, sin dividir por señal casi cero.
- Antialias de esta escena: 192 versus 384 kHz con la misma historia,
  RMS relativo <=0,0001, máximo/pico <=0,0003, media <=0,1 uV en las mismas
  ventanas. Esto mide convergencia de tasa, no elimina por demostración
  todo alias originado antes de la tasa más alta.
- Capacidad, no finitos, factor y soporte insuficiente deben rechazar sin
  salida parcial; repetición válida exacta. Sin heap/IO en lector/FIR.

Recibos <=8 MiB sin QA; compiler/rlib congelados y un tmp/lab-current vacío
al terminar. Conservar fuentes, entradas y replay inalterado de cualquier
fallo antes de corregir. Sin Cargo, caches o carpetas de muestras nuevas.
Después de aprobar, una única exportación WAV float32 útil para escucha,
300 ms y 48 kHz mono. Convención explícita 1 V=1 FS, sin ganancia dinámica,
normalización, fade o dither. El WAV es una vista regenerable de la salida,
no un nuevo input privado obligatorio. No admitir RT o fidelidad física.
