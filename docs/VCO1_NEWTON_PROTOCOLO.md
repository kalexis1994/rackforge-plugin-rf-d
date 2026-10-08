# VCO1: Newton conjunto y continuación corta, protocolo previo

2026-10-07. Partir del ensamblaje congelado e92b8ee, sin cambios de
algoritmos, tarjetas, contactos, memorias o gates anteriores. 134 filas
completas, ambos 741, BJT/JFET, Schmitt/reset y panel. Se conserva la
frontera nominal SW6 3/10, alpha=.5 y mixer impuesto.

## Solve

Newton conjunto, eliminación con pivote escalado existente. Sólo se
salta un coeficiente exactamente cero; no se elimina una rama física.
Presupuesto fijo 64 iteraciones/24 halvings. Line search Armijo1e-4 sobre
norma de corrección, conservando memoria entrante en todos los trials.
Rechazo de dominios como rechazo del trial, sin clamps del dispositivo.
Convergencia exige residual KCL <=1e-13 A, restricciones <=1e-11 V y
corrección <=2e-9 V o <=2e-12 A. Fallo devuelve Error, sin candidato parcial.

Free conserva todas las KCL, sin reset/timer/rampa impuestos. Para DC
condicionado de arranque, StartupRampZero representa la misma fuente
C1=0 del banco anterior: sustituye sólo KCL de RAMP_C1 por su restricción
y reconstruye Istartup=-KCLoriginal. Es eliminación exacta de la corriente
de esa fuente, no un nuevo umbral. La frontera de arranque sólo permite
Mode::Dc; no puede persistir en Euler. Se exporta su corriente explícita.

## Banco fijado

Dos DC condicionados iniciados cerca de las referencias independientes
anteriores: perturbaciones de voltaje 10 uV y corrientes 1 nA. Son warm
starts de laboratorio: **no admiten inicialización propia desde cero**.
Comparar todas las 134 incógnitas y la corriente de arranque con SPICE y
el residual del circuito original más la fuente de arranque.

Continuación libre corta: C4 10/100 pF × dt125/250/500 ns, durante 8 us.
64/32/16 pasos por perfil, 224 en total. Cada historia entrante se mantiene
fija y sólo el estado completo aceptado pasa al paso siguiente. La
referencia independiente usa las incidencias Decimal100 del ensamblaje
con la interfaz binary64 de cada primitiva ya declarada y eliminación
Decimal100 con pivote absoluto; no lee Rust ni sus raíces. No atribuir
precisión Decimal100 a todo el estado después de sus interfaces binary64.

Gates por fila frente a la referencia: voltajes 2e-7 V; corrientes 2e-10 A;
corriente de arranque 2e-10 A. Reference local root residual <=2e-14 A,
restricciones <=2e-12 V y corrección <=2e-10 V/2e-13 A. El régimen corto
no cubre un periodo ni el evento de reset: no admite frecuencia, ondas
estacionarias, refinamiento temporal o escucha.

Repetición pura, presupuesto mínimo rechazado y retry desde la misma
entrada; invalidación de estado/control/dt sin publicación. Test aislado
128 solves con cero heap. Compilación optimizada fija para este bloque,
con compiler/comandos/binarios ligados por hash; no se admite deadline.
Preservar fallos y repetir la misma etapa antes de reparar.

## Siguiente frontera

Semilla propia derivada, arranque robusto en los controles reservados,
trayectoria de 30 ms, refinamiento y calibración propios. Después transferir
R6/R45 al mixer activo y contrastar ambos lados. No cambiar el rechazo
previo de DC libre, arranque calibrado o campaña larga.
