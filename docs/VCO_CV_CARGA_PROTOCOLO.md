# VCO CA3046: CV y carga con trims calibrados

Protocolo previo, 2026-10-17. SVC-9 pp.5/19, CA3046/SVC-204D,
SW6 3/10, R6=.5, C4=10 pF, dispositivos nominales de laboratorio a 25 C.
Continuación de [calibración](VCO1_CALIBRACION_PROTOCOLO.md) y
[Radau](VCO1_RADAU_CICLOS_PROTOCOLO.md). No hay instrumento físico.
Aquí «físico» identifica las ecuaciones del circuito documental completo;
concordancia entre métodos no identifica parámetros de una unidad vintage.

## Dominio y preguntas

Conservar R11=521.3126579373712 ohm y R8=0.2613404652606161 del ajuste
archivado; no redondear a los trims aproximados de bancos locales viejos.
CV KEYBOARD [-3.1,-2.1,-1.1,-.1] V, otras cinco líneas -2.1 V;
BUS [-.125,0,.125] V impuesto a través de R45 una sola vez. Mantener
libre NEG4_REF con su red y cargas; carga externa adicional de ese rail=0 A.
Estas son fronteras de placa; no ley MIDI, posición física del panel o CV
dinámico. La fuente de fase nominal actual conserva otros trims y forma.

1. Matriz de doce arranques propios, C1=0 retenido sólo durante DC.
   Comparar todos los 134 nodos/corrientes y forcing contra OP SPICE nuevo,
   con todas las memorias 741 y junturas presentes. No sembrar el nativo
   con raíces SPICE. Controlar KCL y constraint con el forcing retirado de
   la suma a tierra apropiadamente. Puertos R6/R45 por ley original.
2. Cuatro esquinas CV/BUS: dos pasos Radau locales desde cada DC, h=4/32
   ticks (tick=125 ns/65536), cada uno con historia propia sin encadenarlos.
   Contraste de las dos etapas frente a Decimal100 desde historia HIGH/LOW;
   Newton independiente sin semilla de raíz nativa. Es un control local
   de cargas e incidencia, no una trayectoria de frecuencia de toda la matriz.
3. Reusar los cuatro transitorios BUS=0 de la calibración. Obtener ocho
   transitorios nuevos de 30 ms a BUS=±.125 V, Gear2/125 ns; además Trap2
   a KEYBOARD=-2.1 V, BUS=.125 V. Medir tras 15 ms, forma, frecuencia,
   amplitudes, duty y balance de Qa/Q10/C1. No exigir invariancia ante la
   carga: su diferencia es un resultado, no un error que deba corregirse.
4. Dos historias nativas completas desde DC propio, KEYBOARD=-2.1 V,
   BUS=.125 V, 30 ms, máximos aceptados 250/125 ns. Radau, HIGH/LOW,
   estimador y búsqueda admitidos, sin fuente periódica impuesta. Comparar
   refinamiento y ambos métodos SPICE con las mismas fronteras/trims.
   Un punto reservado cargado no acredita el resto del rango.

## Gates congelados

- DC/etapas: error nodal <=2e-7 V, ramas/forcing <=2e-10 A.
  Newton nativo <=1e-13 A/1e-11 V y corrección <=2e-9 V/2e-12 A;
  ratios <=1. Decimal100 <=2e-14 A/2e-12 V y corrección
  <=2e-10 V/2e-13 A. Balance global <=1e-11 A.
- Pasos Radau locales: todos los 268 componentes contra Decimal100,
  incluyendo cargas y flujos. No contar replays como nuevas raíces.
- Historias completas: error adaptativo <=1 (2 uV nodos/2 nA ramas),
  HIGH/LOW normalizado, reloj entero, máximo 20 intentos por trío,
  Newton 64 iteraciones/24 mitades, mínimo full=8 ticks. Sin relajar
  gates ante fallo; conservar entrada y replay antes de corregir/refinar.
- Frecuencia entre resoluciones/métodos <=1 cent; extremos saw/tri/pulse
  <=5 mV. Dispersión periódica <=1e-5, balance Qa/Q10/C1 <=.002.
  Balance excluye Q7 y cuadratura, conforme al contrato anterior.
- Forma por fase del último ciclo, DC sin retirar: DC <=5 mV; norma
  vectorial de armónicos 1–8 <=2 % por onda. Sin ganancia/alineación
  adicional, sólo coordenada entre los resets reales de cada historia.
  Error pico crudo y sensibilidad de carga son diagnósticos separados.
- Frecuencia creciente con KEYBOARD en cada carga. BUS=0 debe conservar
  las métricas archivadas, sin reajuste de trims ni corrección por nota.
  Constatar fidelidad al código/evidencia anterior; no imponer A440 exacto.

## Evidencia y almacenamiento

Un tmp/lab-current vacío al inicio/final; nombres de trabajo propios,
sin carpetas por escena, Cargo/cache/rlib nuevos. Compiler, librería,
ngspice y macromodelo congelados por hash. No cambiar fuentes admitidos.
Derivar adaptadores de fine/linear/Radau por enlaces exactos, manteniendo
aritmética y búsqueda admitidas. No generar WAV ni tocar la escucha actual.

Retirar exports transitorios/ejecutables después de registrar digest del
flujo completo, métricas y una ventana acotada exacta de los últimos dos
ciclos con contexto para reanálisis; guardar también cruces asentados de
toda la historia, DC y etapas elegidas. No declarar que el prefijo retirado
permite un nuevo análisis de todos sus estados: sólo es regenerable desde
fuentes/controles. El flujo nativo compacto exporta observaciones de cada
endpoint; no es archivo de todos los 134 estados. Etapas seleccionadas
conservan HIGH/LOW completo. Cuadratura de corriente Radau, no Euler.
Recibos nuevos <=32 MiB sin QA, área transitoria <=256 MiB y reserva
1 GiB; proceso nativo <=2400 s y SPICE <=180 s por escena. Fallos conservan
fuentes, deck/inputs, stdout/stderr y replay; snapshots pequeños comprimidos.
Tests previos heredados por identidad, sin sumar ensayos de laboratorio
como nuevos unit tests. Admitir sólo la matriz DC, etapas locales y el
punto dinámico efectivamente contrastados; no motor tocable o fidelidad física.
