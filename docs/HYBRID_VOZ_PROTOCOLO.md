# VCO nominal de fase unido a los dos contornos y J7

## Alcance fijado antes de medir

CA3046/SVC-204D nominal, misma escena y tarjetas que la
[nota completa](VOZ_NOTA_OBSERVABLE_PROTOCOLO.md). Un solo VCO, sierra,
R6=0,5, seis CV=-2,1 V, 25 °C, segundo VCA a 2 V. La fase y los
52 armónicos proceden del [núcleo admitido](VCO_FASE_NOMINAL_PROTOCOLO.md).
No se ajusta ganancia, fase, DC ni controles a los resultados nuevos.

El experimento bifurca el estado completo a **40 ms** de la referencia
de 100 ms. Proyecta HIGH/LOW de sus 118 incógnitas de cadena, incluidos
C2/C5, uniones de los latches, C27, ladder, recuperación, dos VCA y
acoplamiento de salida. No hace otro DC ni reinicia condensadores.
KEY permanece a 10 V hasta 75 ms y pasa a 0 V hasta 100 ms.
La ventana 40–100 ms está reservada respecto del ajuste de fase 8–40 ms.
Esto no admite arranque, ataque completo, otra frecuencia o CV general.

## Unión eléctrica

Los terminales DRIVE/TRI del VCO periódico excitan la red resistiva
original R6/R45 y el selector de sierra, con BUS como incógnita de la
cadena. Se añade I_BUS y dI_BUS/dV_BUS en cada etapa Radau. Las cinco
ramas del mezclador antiguo están OFF: R6/R45 se cuentan una sola vez.
La corriente de masa y la reacción de DRIVE/TRI siguen observables en
el puerto de cuatro terminales. La realimentación de BUS sobre la fase
y las memorias internas del VCO está aproximada; se contrasta su efecto
en J7. Fuente: SVC-9 p.5/19 y derivación ya admitida del puerto VCO.

## Gates previos

- Newton Radau: residual ≤1 pA y corrección ≤2 nV; 80 iteraciones,
  24 halvings de línea. Bajo el gate de residual se permite mejorar la
  corrección de nodos débiles. No cambia las ecuaciones de carga.
- Error coarse/dos fine en las 118 incógnitas:
  500 µV + 1e-4·|V|, como el estimador observable de la referencia.
  Publicación atómica sólo al aprobar; hasta 32 subdivisiones.
- Dos recorridos propios desde la misma semilla, paso full máximo
  64/32 µs; reloj entero y grilla común de 125 µs, 481 observaciones.
- J7 frente a cada referencia completa: RMS relativo ≤3 %, pico
  relativo ≤6 %, error medio ≤10 µV. Sin alineación ni normalización.
- C2/C5: |error| ≤2 mV + 0,001·|V_ref|.
- BUS: |error| ≤0,5 mV + 0,002·|V_ref|.
- R59/R60: |error| ≤20 nA + 0,01·|I_ref|.
- Refinamiento propio: J7 RMS ≤0,5 %, pico ≤1,5 %, media ≤5 µV;
  C2/C5 ≤0,5 mV + 1e-4·|V|; BUS ≤0,1 mV + 1e-4·|V|;
  cargas ≤2 nA + 0,002·|I|.
- Raíces seleccionadas frente a las 119 ecuaciones originales con
  cursor Amount explícito y red VCO original: residual ≤20 pA,
  corrección ≤2 nV. La auditoría evalúa candidatos nativos;
  no es una segunda trayectoria independiente.
- Rechazos inválidos y replay válido exacto, heap contado durante
  integración; tiempos medidos por recorrido, sin declarar RT.

## Datos y límites

Biblioteca/compiler congelados, sin Cargo ni nueva biblioteca.
Sólo `tmp/lab-current` para ejecutable, semilla y exports. Recibos
guardan grilla compacta y raíces seleccionadas comprimidas, con SHA
de los bytes originales. Sin WAV ni nueva carpeta de muestras.
Un fallo conserva fuentes, semilla, export y replay sin modificaciones
antes de corregir. No se debilitan estos gates para admitirlo.
La referencia eléctrica documental no demuestra fidelidad al Moog físico.

## Corrección de representación tras el rechazo del BUS

El primer recorrido con 52 armónicos pasa J7 y cargas, pero falla el
gate de BUS. Se conserva en `hybrid_voice_native03.json` con replay.
Se sustituye sólo la representación de DRIVE48/TRI54 en esta unión por
interpolación lineal compacta del mismo ciclo nativo aislado, incluyendo
el reset. Antes de derivar: error máximo de compacción ≤50 µV en ambas
fuentes y diferencia entre extremos de ciclo ≤100 µV. Extremos se unen
por su promedio; este cambio cuenta dentro del error de 50 µV.
Frecuencia/época conservadas, sin ajuste al BUS o J7 reservado. Todos
los gates anteriores de trayectoria permanecen iguales.

La curva es una fuente de tiempo continuo para el solver adaptativo;
no un generador antialias para muestrear directamente a 48 kHz. El API
de 52 armónicos anterior conserva su alcance. Generalizar esta unión
a un motor de audio exige controlar banda/oversampling y deadline.
