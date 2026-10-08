# Reset VCO1: SDIRK y rigidez local del macromodelo

2026-10-08. Base 5d073dd. Perfil CA3046 nominal a 25 °C, C4=10 pF, controles/mixer impuestos. C4=100 pF no se ensaya con el nuevo método. Circuito y código Rust de producción intactos. [Protocolo SDIRK](VCO1_SDIRK_PROTOCOLO.md). Este bloque implementa un método en laboratorio y analiza dinámica local; no admite una voz o un integrador de producción.

## Cargas, flujos y etapas

SDIRK2 conserva F(x)+Q'(x)=0, cargas no lineales y cuatro flujos inductivos. Etapa2 guarda la historia x0 y aplica el forcing de cargas/flujos de etapa1; no mezcla voltajes históricos. El forcing de todas las restricciones algebraicas es cero. Ambas etapas conservan hi/lo y gates Newton/masa; sólo endpoints provisionales pueden avanzar el reloj. Correcciones de primer orden en lo, γ/a/γh binary64 explícitos y solver 64/24 heredados.

La [primera medición](../evidence/voice_vco1_sdirk_probe01.json) contrasta **48 raíces internas**, dos historias y cuatro pasos, contra terminales/incidencias/cargas/pivotes Decimal100. Error máximo 7,00911e-12 V / 9,25248e-16 A. Primer intervalo Q6: ratio local0,00137275549 para half30,5176 ps, frente al rechazo Euler1,00655 desde la misma historia. Las cuatro escenas de esa historia pasan error local. En la historia posterior XIC3.7 los ratios son5,7665..27,4152 y todas las raíces convergen: la coincidencia de raíces no admite precisión temporal.

## Dos continuaciones condicionadas rechazadas

El intento01 alcanza **70,770263671875 ns /2198 pasos**, con half mínimo15,2588 ps. El texto PrecisionLimit del runner agrupa error local y fallo de solve. El [diagnóstico separado](../evidence/voice_vco1_sdirk_floor01.json), bajo [protocolo](VCO1_SDIRK_PISO_PROTOCOLO.md), sí confirma las seis raíces y el rechazo LTE: XIC3.7, −2,000038009805446 µV, ratio1,0000190049.

El [segundo controlador](../evidence/voice_vco1_sdirk_probe4_01.json) usa half mínimo7,62939 ps: γh≈2,2346 ps queda dentro del dominio efectivo existente. [Protocolo previo](VCO1_SDIRK_CONTROL4_PROTOCOLO.md): único cambio del runner es full mínimo16→8 ticks, sin modificar dt del kernel, máximo500 ns, presupuesto o gates. Repite las mismas48 raíces con resultados idénticos. Alcanza **186,9354248046875 ns /17424 pasos**; máximo error aceptado0,999573633. También rechaza. El [diagnóstico final](../evidence/voice_vco1_sdirk_floor4_01.json), con [protocolo](VCO1_SDIRK_PISO4_PROTOCOLO.md), confirma seis raíces y LTE XIC3.7=−2,0040517544723773 µV, ratio1,0020258772.

Ambos objetivos de50 µs quedan rechazados, con originales/replays byte idénticos, 542 columnas de endpoints/etapas hi/lo, reloj y gates completos. En cada intento se contrastan cuatro intervalos aceptados: dos raíces por intervalo, primero/último/dos mayores cambios nodales. Ambos bancos de ocho raíces pasan. Son historias condicionales; no una trayectoria global independiente. Euler anterior usa6408 y31574 pasos para llegar hasta los tiempos finales respectivos, frente a2198/17424 de SDIRK. Es una comparación de cobertura y conteo, no de CPU, exactitud continua o audio.

## Descriptor local

[Protocolo](VCO1_POLOS_RESET_PROTOCOLO.md): G=∂F/∂x y M=∂Q/∂x en tres historias, ensamblados Decimal100 antes de convertir a float. Modos de M δx'+G δx=0 por tres shifts1 fs/1 ps/1 ns. El [análisis01](../evidence/voice_vco1_reset_modes01.json) no admite candidatos con su normalización componente a componente. La [normalización nueva](VCO1_POLOS_RESET_NORMALIZACION.md) define un residual hacia atrás del lápiz equilibrado, sin cambiar gates eléctricos. El [análisis02](../evidence/voice_vco1_reset_modes02.json) conserva G/M idénticos y registra11/14/10 coincidencias entre shifts; vectores y residuales completos quedan retenidos.

Modo rápido coincidente: λ≈−1,31085e14 s⁻¹, escala≈**7,629 fs**, dominante IC3_OUT. Otro λ≈−2,70e12 s⁻¹, escala≈**0,370 ps**, dominante XIC1.17. Dominancia de un componente no identifica la rama causante. No son enclosures de eigenvalor ni prueba de estabilidad global; sistemas equilibrados llegan a condiciones≈5e12. No aparecen modos positivos coincidentes entre los tres shifts, lo que no descarta modos inestables ausentes. La escala aislada L3/RL3=1 fs es de la tarjeta del macromodelo, no un polo acoplado demostrado o una bobina del Moog.

## Amortiguación y decisión

Para el problema lineal, R_Euler(z)=1/(1−z), R_SDIRK(z)=(1+(1−2γ)z)/(1−γz)². Para z negativo de módulo grande, sus magnitudes tienden a1/|z| y4,828427/|z|. Con el modo rápido encontrado y h30,5176 ps: |R_Euler|≈0,000249913 y |R_SDIRK|≈0,00120420. SDIRK es L-estable y de mayor orden, pero esa propiedad no asegura mayor supresión de un modo rígido para un paso finito. Este cálculo no atribuye por sí solo todo el rechazo a ese modo; amplitudes, acoplamientos y reducción de orden de la DAE quedan abiertos.

Cerrar estas campañas. Antes de probar otro integrador o grilla, derivar un contrato de equivalencia del puerto 741: terminales, carga, corrientes/retornos y memoria frente a la tarjeta completa, con tratamientos de sus dinámicas internas y error declarado. No eliminar estados/inductores ni alterar parámetros por conveniencia sin ese contrato y contraste. Mantener tarjeta completa, métodos y rechazos como oráculos de laboratorio.

La [QA](../evidence/voice_vco1_sdirk_tests01.json) conserva235 tests heredados, cero tests unitarios nuevos/repetidos. Audita124 comparaciones de raíces de etapas:48 repetidas en dos intentos, dos bancos de8 raíces de intervalos y dos diagnósticos de6; no124 casos únicos ni tests unitarios. Cero SPICE/audio nuevos. Ciclos completos, frecuencia/refinamiento, calibración, carga activa, fidelidad física, heap del nuevo método y deadlines siguen pendientes; pila8 MiB sólo de laboratorio.
