# Coste sin cambiar las doce leyes

Previo, 2026-11-06. Base60bd2e2, referencia SVC-9 Fig.9-11 p.13.
Mismos parámetros,18 memorias,12 leyes BE/BC, tres cutoff fijos y dominio
de laboratorio de RECOVERY_PORT_RESULTADOS. No ampliar admisión física.

## Variantes acotadas

1. Evaluación conjunta del defecto y su derivada. Para |z|<.001, Horner
   de sum(z^k/k!,k=2..9) y derivada expm1(z)=z+defecto. El resto exacto
   del polinomio es <=exp(.001)*.001^10/10! <2.76e-37, antes de redondeo.
   En la otra rama, una sola expm1 compartida. Misma ecuación, residual
   completo2e-13, Newton modificado6, dos etapas SDIRK, presupuesto12.
2. Si falta margen, predictor de uniones desde los defectos anteriores:
   z0=zp-P*n_seed. Primera etapa usa el defecto del paso aceptado; segunda
   usa el de la primera. Es sólo semilla: evaluar todas las leyes y residual
   antes de aceptar; rechazo atómico y estado previo en cualquier fallo.
   La semilla no añade memoria física ni suaviza señal o control.
3. Si falta margen, especialización algebraica del punto fijo para que
   el compilador conozca el índice de las matrices. Conservar los tres
   índices y elegir fuera del bucle interior, mismos valores y orden.

No alterar h=1/384000, FIR, tolerancia, leyes, compiler/flags, corriente BC,
dispositivos, prioridad del proceso o presupuesto para mejorar el banco.
Conservar cada variante medida y todos los rechazos. No escoger la mejor
repetición. No usar flags de cálculo relajado o instrucciones exclusivas
de esta CPU como sustituto de una reducción medible del trabajo.

## Verificación fijada antes de medir

- Ley conjunta frente a Decimal de80 dígitos: positivos/negativos, cero,
  umbral y vecinos de bits, rejilla en[-40,40]. Error absoluto normalizado
  <=1e-28+5e-15*|valor| para defecto y derivada, comparar tras factor Iexp
  para cada una de las12 uniones en tres puntos. El error absoluto puede
  dominar cerca de cero: no usar una división por señal nula.
- Comparar1537 pasos de cada DC con Python/fullNewton12, nodos<=1e-10 V,
  puertos<=1e-14 A, carga<=1e-11 V. También1537 pasos de entrada acotada
  con saltos/rampas para cada DC frente al kernel previo, mismos límites.
  Estos saltos son regresión numérica, no nueva admisión de sonido.
- Publicar máximos del residual de ambas etapas y balance híbrido
  en las etapas conservadas. Verificar12 leyes y presupuesto, entradas
  inválidas, estado corrupto, presupuesto0/1 y retry por bits, cero heap.
- Banco1200 bloques128 con FIR, primer bloque incluido (80 frames por
  latencia y luego128). Plazo2.6667 ms, objetivo50% para TODAS las filas.
  Cero heap; generar entrada y registrar resultados fuera del DSP.
  Medir primero el baseline actual y después las variantes en orden;
  publicar costes absolutos y relativos de ese banco, sin causalidad de
  comparaciones entre sesiones. Una variante que falla queda rechazada.
- Si un banco pasa, confirmarlo en un banco largo predefinido4800 bloques,
  con la misma entrada y orden; todos los intentos se conservan. No afirmar
  RT de voz: faltan VCO, contornos, controles generales y host.

Reusar corpus/puertos anteriores para admisión física, contrastar estados
propios nuevos con el kernel previo y declarar cobertura nodal dispersa.
No nueva campaña SPICE, biblioteca, WAV o caché. Un tmp/lab-current, procesos
<=240 s, exports<=32MiB, recibos nuevos<=6MiB sin QA; streams diferenciales
o métricas/digests en vez de duplicar matrices y millones de muestras.
Conservar8769 inputs, fuentes, fallos y escucha, retirando sólo temporales
nombrados dentro del área comprobada después de guardar sus recibos.
