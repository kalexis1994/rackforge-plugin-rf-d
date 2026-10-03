# RF-D

Proyecto de recreación del **Minimoog Model D clásico** para RackForge. Su sonido se investigará mediante **RACE — RackForge Architecture for Circuit Emulation**: circuito documentado, leyes de control, calibración de servicio, comparación de audio y presupuesto de tiempo real. Este repositorio es independiente del host y de otros plugins RF.

## Estado

La [variante RMS de junturas](docs/BIESTABLE_JUNTURAS_RMS_RESULTADOS.md)
conserva signos en la parte simétrica y convierte todos los acoplamientos,
forzamientos y mapas nodales. Ataque/cola mejoran, prefijo empeora y reset
queda prácticamente igual; se conserva la comparación completa. Cola N4
da término forzado hipotético ~1,31 mV, con anclaje todavía desconocido.
El [corpus](docs/BIESTABLE_JUNTURAS_RMS_ENTRADAS.md) verifica **335 entradas**
de 57 informes y preserva ocho versiones fallidas anteriores de tests.
Siete regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: certificado espectral racional
de la parte simétrica para distinguir la pérdida de Gershgorin.

La [comparación dirigida de bloques](docs/BIESTABLE_COMPARACION_BLOQUES_RESULTADOS.md)
propaga seis grupos físicos con **64 núcleos de extremo y 64 de pico**.
Las ocho cotas bajan: prefijo N4 da término forzado ~33,72 µV y reset N4
~0,487 µV con anclaje cero hipotético. Ataque/cola siguen enormes.
El [corpus](docs/BIESTABLE_COMPARACION_BLOQUES_ENTRADAS.md) verifica **324 entradas**
de 55 informes y conserva ocho versiones fallidas anteriores de tests.
Ocho regresiones nuevas pasan al primer intento.
El anclaje y los restos no lineales siguen pendientes. **1 mV global sigue abierto**.
Próximo corte: cancelaciones internas del grupo de junturas y cobertura completa.

La [propagación por celdas](docs/BIESTABLE_PROPAGACION_CELDAS_RESULTADOS.md)
reconstruye **64 inversas estructuradas** y distribuye el residual en cada
celda. Las ocho cotas tangentes bajan; reset N4 da término forzado
~0,529 µV con anclaje cero hipotético, mientras ataque/cola siguen enormes.
Se conserva el anclaje desconocido y se distinguen extremo y pico interior.
El [corpus](docs/BIESTABLE_PROPAGACION_CELDAS_ENTRADAS.md) verifica **313 entradas**
de 53 informes y ocho versiones fallidas de tests; nueve regresiones nuevas pasan.
**1 mV global sigue abierto**.
Próximo corte: estructura de bloques para la estabilidad de ataque/cola,
restos no lineales, anclaje y recorrido completo.

El [descriptor ponderado ideal](docs/BIESTABLE_DESCRIPTOR_PONDERADO_RESULTADOS.md)
cubre la variación de coeficientes en **64 celdas de ocho intervalos**:
todas certifican la inversa ideal, conservando los rechazos binary64.
Los pesos fijados mejoran prefijo/cola y empeoran ataque; se archiva toda
la comparación. Las cotas tangentes variables mantienen pendientes restos
no lineales, anclaje y recorrido completo. **1 mV global sigue abierto**.
El [corpus](docs/BIESTABLE_DESCRIPTOR_PONDERADO_ENTRADAS.md) verifica 305
entradas y ocho versiones fallidas de tests; nueve regresiones nuevas pasan.
Próximo corte: conservar más estructura del operador y su propagación temporal.

El [descriptor continuo](docs/BIESTABLE_DESCRIPTOR_CONTINUO_RESULTADOS.md)
separa 94 voltajes y 25 tasas de memoria. Ocho inversas de matrices levantadas
119×119 quedan certificadas; los mapas binary64 mantienen sus gates fallidos.
Se preserva y corrige un error de norma integrada del forzamiento con un
contraejemplo temporal. Las cotas válidas pertenecen sólo a operadores
congelados: las cotas sin pesos son enormes fuera de reset.
El [corpus](docs/BIESTABLE_DESCRIPTOR_CONTINUO_ENTRADAS.md) reconstruye 295
entradas y siete versiones fallidas; once regresiones nuevas pasan.
Siguiente corte: pesos declarados, coeficientes ideales y variación temporal,
restos no lineales, anclaje y cobertura. **1 mV global sigue abierto**.

La [variante de tasas correlacionadas](docs/BIESTABLE_TASAS_CORRELACIONADAS_RESULTADOS.md)
conserva cancelaciones entre C(v)*v′ y Qpol′: los intervalos completos
certificados bajo 10 pA pasan de 31 a 105. En reset N4, el límite puntual
baja de 2,666 nA a 6,419 pA sin cambiar estados ni sonido. Los 391 casos
con media sobre el umbral permanecen. El [corpus](docs/BIESTABLE_TASAS_CORRELACIONADAS_ENTRADAS.md)
verifica 272 entradas; nueve regresiones nuevas pasan al primer intento.
Siguiente corte: propagación con memoria, restricciones, estabilidad,
anclaje y cobertura. El criterio global de 1 mV sigue abierto.

Los [recintos de Q(v) y magnitud del residual](docs/BIESTABLE_MAGNITUD_RESIDUAL_RESULTADOS.md)
acotan balance constitutivo y magnitud acumulada en 496 intervalos y un
soporte mixto. La media cumple 10 pA en 105; el límite puntual certifica
31 intervalos completos. Reset conserva una cota amplia por pérdida de
correlación de tasas: próximo corte, estrecharla antes de propagar.
El [corpus](docs/BIESTABLE_MAGNITUD_RESIDUAL_ENTRADAS.md) reconstruye 262 entradas
y seis versiones fallidas. Siete regresiones nuevas pasan, con el primer
intento numérico preservado. 1 mV global, física, audio y deadline siguen abiertos.

El [recinto racional de la integral](docs/BIESTABLE_INTEGRAL_ACOTADA_RESULTADOS.md)
acota resto y redondeo sobre 496 intervalos y un soporte mixto; todos pasan
el contraste acotado de Gauss16. Confirma 105 medias polinómicas bajo 10 pA
y 391 por encima, sin inconclusas. Son cotas del interpolante, con cota
inferior de magnitud del residual; aún falta una cota superior y propagación.
El [corpus](docs/BIESTABLE_INTEGRAL_ACOTADA_ENTRADAS.md) reconstruye 254 entradas
con cinco versiones fallidas anteriores. Siete regresiones nuevas pasan
al primer intento. Próximo corte: recinto de Q(v), magnitud superior y
estabilidad con cobertura completa. El criterio global de 1 mV sigue abierto.

El [balance de carga integrado](docs/BIESTABLE_BALANCE_GAUSS_RESULTADOS.md)
compara carga interpolada y Q(v) constitutiva, con puentes en el soporte
mixto del knee. Gauss 8/16 pasa en los 496 intervalos y ese soporte;
el [primer contraste Simpson](docs/BIESTABLE_BALANCE_CARGA_RESULTADOS.md)
conserva sus 371 fallos. El residual medio cumple 10 pA en 105 intervalos
y conserva 391 incumplimientos. El [corpus](docs/BIESTABLE_BALANCE_CARGA_ENTRADAS.md)
reconstruye 246 entradas y cinco versiones de pruebas fallidas.
Siguiente corte: cota de cuadratura y magnitud/propagación del residual.
El criterio global de 1 mV, física, audio y deadline siguen abiertos.

La [reconstrucción interior](docs/BIESTABLE_CARGA_INTERIOR_RESULTADOS.md)
consulta 1.488 puntos y certifica las 21 restricciones capacitivas en los
496 intervalos del polinomio. KCL pasa 315 consultas y conserva 1.173
incumplimientos. Se acota un cruce del knee en el historial antiguo,
fuera del último intervalo consultado. El [corpus](docs/BIESTABLE_CARGA_INTERIOR_ENTRADAS.md)
reconstruye 230 entradas. Estos certificados pertenecen al interpolante;
el error temporal global de 1 mV, física, audio y deadline siguen abiertos.

El [contraste con las ecuaciones continuas](docs/BIESTABLE_CARGA_CONTINUA_RESULTADOS.md)
conserva 496 puntos: todos pasan KCL con su BDF fino, mientras la
reconstrucción cúbica queda bajo 10 pA en 106 y conserva 390 incumplimientos.
Se verifican KCL, C10 serie y regla de la cadena de QBE/QBC, incluido un
soporte que cruza el knee. El [corpus ampliado](docs/BIESTABLE_CARGA_CONTINUA_ENTRADAS.md)
reconstruye 222 entradas y conserva cuatro versiones de pruebas fallidas.
Siguiente gate: reconstrucción dentro de intervalos y cambios de pieza
antes de promover un estimador. El criterio global de 1 mV sigue abierto.

Los [testigos del defecto de carga](docs/BIESTABLE_DEFECTO_CARGA_RESULTADOS.md)
verifican 72 identidades BDF2, 18 BE y 512 pasos RC con error forzado
exacto, incluyendo el término de memoria publicada de C10 serie.
El [diagnóstico sobre trazas propias](docs/BIESTABLE_DEFECTO_MUESTREADO_RESULTADOS.md)
conserva 496 puntos y separa diferenciación, reloj y coeficientes.
El [corpus](docs/BIESTABLE_DEFECTO_CARGA_ENTRADAS.md) reconstruye 215
entradas; doce pruebas nuevas pasan. No añade solves no lineales ni
conoce todavía el defecto exacto del circuito. Siguiente gate: tasa de
carga frente a ecuaciones continuas antes de usar un estimador temporal.
El gate global de 1 mV, física, audio y deadline siguen abiertos.

El [forzamiento relativo a ventanas refinadas](docs/BIESTABLE_FORZAMIENTO_RESULTADOS.md)
separa residual de ecuaciones y desajuste de memoria publicada. Completa
1.536 intervalos finos propios y 512 pasos de propagación; los predictores
lineal y cuadrático pasan sus gates. El
[intento inicial](docs/BIESTABLE_FORZAMIENTO_INTENTO_INICIAL.md) conserva
dos bloqueos de reloj y un error de formato del RHS. El
[corpus](docs/BIESTABLE_FORZAMIENTO_ENTRADAS.md) reconstruye 201 entradas
y cuatro pruebas fallidas; once pruebas nuevas verifican este bloque.
Este forzamiento se extrae de una referencia ya calculada y no es un
estimador independiente. Siguiente gate: error de diferenciación de cargas
sobre historiales reales. El gate temporal global de 1 mV permanece abierto.

La [curvatura derivada del circuito y su publicación](docs/BIESTABLE_CURVATURA_RESULTADOS.md)
propaga 1.536 segundas variaciones con ambos historiales y cero ajuste a
respuestas. El [contraste reservado](docs/BIESTABLE_RESPUESTA_CUADRATICA_RESULTADOS.md)
completa 9.216 solves nuevos: predictor cuadrático 72/72 individual y
72/72 par, frente a 54/72 individual lineal, con sus 18 fallos conservados.
El [corpus ampliado](docs/BIESTABLE_CURVATURA_ENTRADAS.md) reconstruye 186
entradas y tres pruebas fallidas; este bloque suma once pruebas nuevas.
Siguiente gate: derivar el forzamiento temporal sobre los historiales reales.
El gate de 1 mV desde DC, identificación física, audio y deadline siguen abiertos.

El [controlador E4G8 con Newton compensado](docs/BIESTABLE_CONTROLADOR_COMPENSADO_RESULTADOS.md)
reproduce decisiones y reloj: 6.486 publicados, 12.968 provisionales y 49
rechazos conservados. Sus estados publicados son idénticos al ensayo de
reloj fijo. Cinco regresiones nuevas pasan; D4/E4 siguen fallando 1 mV.
Próximo gate: sensibilidad y memoria acumulada con sellos auditados.

La [trayectoria completa con reloj guardado](docs/BIESTABLE_RELOJ_COMPLETO_COMPENSADO_RESULTADOS.md)
completa 6.486 intervalos desde un DC fresco idéntico: máximo nodal 6,21 pV
y memoria 8,77 pV, ambos bajo 10 nV. Cuatro regresiones nuevas pasan.
Siguiente gate: controlador adaptativo propio con sus rechazos y sombras;
el contraste temporal global de 1 mV sigue abierto.

La [variante del integrador con residual original](docs/BIESTABLE_INTEGRADOR_COMPENSADO_RESULTADOS.md)
completa 64/64 intervalos con memoria propia: máximo nodal 2,34×10⁻¹⁵ V,
320 residuales y 64 Jacobianos idénticos a sus contrastes. Cuatro regresiones
pasan en el segundo intento; el fallo del adaptador queda conservado.
Próximo gate: trayectoria completa con reloj guardado, luego refinamiento.

La [auditoría de 64 intervalos guardados](docs/BIESTABLE_VENTANAS_ESTATICAS_RESULTADOS.md)
pasa 64/64 mapas compensados; el ordinario pasa 54/64 y el mixto histórico
24/64. Los 256 solves pasan sus gates algebraicos y cuatro regresiones nuevas
preservan todos los fallos. Siguiente contraste: variante explícita del
integrador con el mismo residual, reloj e historial, sin admisión global.

Los [sellos analíticos binary64](docs/BIESTABLE_SELLOS_BINARIOS_RESULTADOS.md)
con recíprocos compensados pasan los cuatro mapas frente a Decimal; el
ordinario conserva reset fallido. Cuatro regresiones nuevas verifican los
ocho solves y la reutilización de datos. Es una candidata de laboratorio;
el próximo gate es su contraste durante integración, con el solver intacto.

La [transcripción estática independiente](docs/BIESTABLE_PRECISION_ESTATICA_RESULTADOS.md)
pasa cuatro comparaciones de corrientes, 28 solves matriciales y cinco
regresiones nuevas. Los mapas anteriores difieren de la referencia Decimal
en ataque y reset. FD Decimal pasa en los tres pasos más finos; 48 inyecciones
completan sus solves. El siguiente corte contrasta sellos analíticos binary64.

La [auditoría de sensibilidad FD](docs/BIESTABLE_RESULTADOS_SENSIBILIDAD_FD.md)
resuelve 40 matrices con precisión racional y pasa tres regresiones nuevas.
Reset falla en los cinco pasos probados y ambas rutas estática/dinámica;
se conserva el gate de 10⁻⁸ y no se selecciona un paso nuevo. El siguiente
corte debe auditar la precisión del residuo estático de la cadena de audio.

La [propagación de las 25 memorias](docs/BIESTABLE_PROPAGACION_DE_MEMORIA.md)
completa 1024 intervalos hipotéticos y pasa 32 contrastes no lineales en
cuatro ventanas, con diez regresiones nuevas. La eliminación racional
cierra los cuatro solves FD; el contraste de mapas pasa 3/4 y conserva
**reset fallido (1,35×10⁻⁶ frente a 10⁻⁸)**. Son verificaciones locales
condicionadas al reloj E4G8; el refinamiento global, física y audio siguen pendientes.

La ruta [E4G8 desde DC](docs/BIESTABLE_CRECIMIENTO_DESDE_DC.md) completa 3 ms con 6486 intervalos y 1724 consultas válidas. Crecimiento 0,125 reduce los intentos sólo de 6590 a 6534 y conserva **8,234 mV** frente a D4: falla 1 mV. La sensibilidad E4/E4G8 pasa únicamente su selección consultada con 0,426 mV, sin admitir refinamiento global ni un controlador nuevo.

Los [contraejemplos exactos de memoria BDF2](docs/BIESTABLE_DEFECTO_Y_MEMORIA.md) pasan cinco regresiones: la diferencia completo/medios puede ocultar error previo común o cancelarse con errores distintos. Las identidades escalares explicitan el límite de la inferencia, sin calibrar el circuito.

Las [ventanas de crecimiento con memoria E4 común](docs/BIESTABLE_VENTANAS_DE_CRECIMIENTO.md) añaden 335 intervalos y contrastan umbrales 0,25/0,125. En la cola reducen intentos de 122 a 103, con más pasos aceptados; seis regresiones pasan y el primer fallo del resumen queda conservado. Es evidencia condicionada, con el gate global desde DC aún abierto.

El [barrido BDF2 de doble paso D4/E4](docs/BIESTABLE_BARRIDO_DOBLE_PASO.md) completa 3 ms con **9446 intervalos publicados**, 18884 medios provisionales aceptados y 866/866 consultas conservativas. El máximo consultado es **7,81 mV** en ATTACK_GATE_LOWER: todavía falla 1 mV. El prefijo muestreado pasa con 4,615 µV, sin cota continua. Se conservan los informes anteriores y la gráfica distingue interpolación y consultas.

El [prototipo del estimador BDF2 por doble paso](docs/BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md) verifica 12 sondas con tres rutas de carga, memoria intermedia y FD. Compara el paso completo con dos medios BDF2 y conserva el completo como candidato; su alcance local se amplía con el nuevo barrido desde DC, cuyo gate global permanece abierto.

La [auditoría de los máximos con historial común](docs/BIESTABLE_MAXIMOS_CON_HISTORIAL_COMUN.md) completa 664 consultas, incluidos los máximos interpolados de los 94 nodos. El mayor punto consultado es 26,79 mV en ATTACK_GATE_LOWER; el gate condicional de 1 mV permanece fallido y el contraste original desde DC no cambia.

El [experimento con historial doble común](docs/BIESTABLE_HISTORIAL_COMUN.md) añade 1992 intervalos B3 desde dos estados C3 idénticos. El máximo interpolado condicional baja a 28,95 mV frente a 126,37 mV desde DC, pero sigue fallando 1 mV. La consulta de ese máximo da 2,12 mV; se revisan también los máximos de todos los nodos para no confundir ese punto con el máximo de la trayectoria.

El [observador con dominio temporal explícito](docs/BIESTABLE_DOMINIO_DE_OBSERVACION.md) completa 772/772 consultas manteniendo los 386 instantes pedidos. El prefijo pasa el gate diagnóstico muestreado con 59,0 µV máximos; el pico completo persiste en 0,126368 V. El refinamiento global sigue pendiente; la nueva observación conserva los fallos anteriores.

Las [consultas entre muestras B3/C3](docs/BIESTABLE_OBSERVACION_ENTRE_MUESTRAS.md) conservan 386 instantes: el pico consultado sigue en 0,126368 V. Detectan 139 consultas subpicosegundo fallidas por tiempos casi coincidentes con extremos guardados; quedan registradas y se prepara una ruta de observación dentro del dominio temporal. El prefijo no se admite con cobertura incompleta.

La [tercera malla BDF2 C3](docs/BIESTABLE_TERCERA_MALLA_BDF2.md) completa 3 ms y verifica 4364 intervalos adicionales. El máximo B3/C3 baja a 0,126368 V y la diferencia final a 39,9 µV. El gate global de 1 mV sigue fallando; se conservan los informes anteriores y continúa la observación entre muestras.

La [auditoría de prefijo y consulta temporal](docs/BIESTABLE_PREFIJO_Y_CONSULTA_TEMPORAL.md) distingue error de comparación entre muestras de discrepancia del integrador: el punto de trigger baja de 3,75 mV interpolados a 39,4 µV consultados, pero el pico de la transición sigue en 0,563 V al resolver ambos candidatos al mismo instante. El refinamiento continúa pendiente.

El [barrido BDF2](docs/BIESTABLE_BARRIDO_BDF2.md) completa 3 ms con ambas políticas y verifica 3236 intervalos. Su discrepancia entre políticas baja a 0,563 V y a 0,141 mV al final; el máximo todavía supera el gate de 1 mV. Euler y sus fallos quedan conservados.

El [integrador BDF2 sobre carga](docs/BIESTABLE_BDF2_CARGA.md) conserva dos estados anteriores y pasa el contraste de siete intervalos con Jacobiano FD y carga publicada. Un RC sintético muestra el refinamiento esperado de segundo orden. Los barridos completos posteriores conservan el gate de refinamiento pendiente; el solver espacial y las hipótesis físicas siguen compartidos.

Los [tiempos de transición](docs/BIESTABLE_TIEMPOS_DE_TRANSICION.md) muestran un adelanto de B2 de ~2,32 µs en ATTACK_OUT y ~2,59 µs en la caída final de Q25. Quedan diferencias de forma aun al alinear eventos como diagnóstico; las trazas conservan sus tiempos originales y el refinamiento sigue pendiente.

El [barrido con memoria compensada](docs/BIESTABLE_BARRIDO_COMPENSADO.md) completa 3 ms con ambas políticas y verifica 4152 medios intervalos. El refinamiento aún falla: diferencia máxima de 5,147 V en ATTACK_OUT y 6,45 mV al final. La cobertura completa y la conservación de carga ya se verifican; queda resolver la sensibilidad temporal de la transición.

El [laboratorio de contorno y cadena de 94 nodos](docs/CONTORNO_CADENA_94_Y_ESTABILIDAD.md) calcula C2/reset dentro del circuito con 21 cargas. El refinamiento temporal conserva el rechazo cerca de 12,4 ms. Una [búsqueda de 102 semillas encuentra tres raíces](docs/BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md); cargas de juntura de diagnóstico revelan un modo creciente en la intermedia que el modelo instantáneo omitía. No se selecciona una rama ni se admite la conmutación física.

El [dominio de las junturas y sus cargas](docs/CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) registra doce puntos Q25/Q15 y verifica 300 sondas sintéticas de depleción/difusión con cuadratura independiente. Ninguno de esos puntos reproduce el sesgo de la medida Cob de las hojas adquiridas. Las primitivas conservan carga e historial; sus parámetros físicos y la partición BJT siguen abiertos. Las [lecciones para RACE](docs/LECCIONES_RACE_CONMUTACION.md) resumen los gates transferibles.

El [registro de fabricación 2N3392 y datos dinámicos](docs/FABRICACION_3392_Y_DATOS_DINAMICOS.md) incorpora GE/RCA 1987 y PN100A Process 10. Conserva la diferencia entre 2 pF típico y mínimo según fabricante y demuestra que los doce puntos del biestable quedan fuera del intervalo IC de su curva de conmutación. Ningún parámetro físico promovido.

El [BJT intrínseco con carga conservativa](docs/BJT_INTRINSECO_CARGA_CONSERVATIVA.md) tiene corrientes/cargas terminales, Jacobiano y memoria ligada a parámetros. Pasa 72 casos independientes contra ngspice 46, incluyendo matrices AC 3×3 a dos frecuencias. Es una hipótesis explícita de baja inyección con parámetros sintéticos; no se incorpora al motor ni admite todavía la conmutación del contorno.

El [BJT cargado en transitorios](docs/BJT_CARGADO_TRANSITORIOS.md) resuelve tres nodos y sus cargas en 252.000 pasos sin reset. Pasa refinamiento frente a ngspice: error propio máximo 1,35 mV, refinamiento independiente 127 µV. Conserva un aborto del oráculo y dos barridos que superaron los gates. La conmutación del biestable Model D sigue pendiente.

La [sonda del biestable con carga no lineal](docs/BIESTABLE_CARGA_NO_LINEAL.md) incorpora Q25/Q15 al laboratorio de 94 nodos, conserva las 21 memorias anteriores y añade cuatro cargas de juntura. Pasa doce escenarios con masas AC independientes y Jacobiano FD. El modo intermedio crece en una escala local de 144–158 ns; a 1 ms siguen apareciendo tres soluciones. El seguimiento temporal refinado permanece pendiente.

La [trayectoria adaptativa desde DC](docs/BIESTABLE_TRAYECTORIA_ADAPTATIVA.md) publica 2982 medios intervalos con cargas continuas. Una política completa 3 ms; la más estricta se detiene a 2,444 ms por el paso mínimo. La comparación alcanza 5,006 V en ATTACK_OUT: conserva el rechazo y **no admite todavía el refinamiento de la transición**.

El [diagnóstico del rechazo y del cero de carga](docs/BIESTABLE_RECHAZO_Y_ORIGEN_CARGA.md) reproduce el segundo medio paso fallido con Jacobiano híbrido/FD. C2 queda entre voltajes representables respecto del gate de KCL; además, la escala relativa de Q cambia por un desplazamiento convencional que no altera la corriente. La [versión de incrementos compensados](docs/BIESTABLE_INCREMENTOS_COMPENSADOS.md) corrige ese intervalo, conserva el fallo original y prepara el nuevo barrido.

El [puerto conjunto C2/reset con carga de toda la cadena](docs/PUERTO_CONTORNO_CADENA_71.md) añade corrientes, matriz de admisión `2×2` y gradientes de los 71 nodos. Pasa 36 casos independientes DC/temporales con diferencia máxima de admisión **2,04 pS**, candidato temporal coherente y heap cero. En un escenario alto de C2, CR6 devuelve 0,495 mA a reset: esa carga deberá entrar en el biestable, cuya conmutación todavía requiere resolver la estabilidad.

El [cierre simultáneo de seguidor, R59 y cadena de 71 nodos](docs/SEGUIDOR_VCA_CADENA_71.md) calcula la base Q18 y la carga devuelta a C2/reset. Pasa veinte destinos DC y 256 pasos independientes, con error máximo de nodo **2,50 nV**, conservación de dieciocho cargas y heap cero. Los saltos se recuperan explícitamente con historial fijo; el costo de 16,12–16,96 ms por bloque todavía excede el plazo. El biestable y las fuentes reales del contorno siguen pendientes.

El [perfil de etapas VCA](docs/ETAPAS_VCA_Y_REPRODUCIBILIDAD.md) contrasta ocho etapas y reduce 38,46 % el costo de las escenas con saltos frente a 32: 9,708 ms de kernel acumulado por bloque, todavía fuera del plazo. Pasan 1152 pasos Rust con 8/16/32 etapas y heap cero. El banco con un estado temporal común reproduce exactamente los resultados entre workers y conserva aparte la variación del arranque DC.

Los [saltos VCA con historial fijo](docs/SALTOS_VCA_HISTORIAL_FIJO.md) pasan 384 muestras independientes, incluyendo apagado y restauración: error interno máximo 7,15 nV. La API rescata 16 rechazos sin subpasos físicos ni borrar cargas. Es una ruta experimental explícita, todavía demasiado costosa; el banco de stack conserva una diferencia de 1,30 pV frente a su gate de identidad de 1 pV.

La [inicialización DC por continuación VCA](docs/DC_VCA_CONTINUACION.md) añade una ruta explícita de preparación para uno o ambos controles en cero. Pasa 18 semillas frente a raíces independientes (1,57 nV), reconstruye las 18 cargas y acepta 1152 pasos posteriores de reposo. Conserva los gates por etapa y heap cero. El salto abrupto durante audio sigue pendiente.

Los [topes exactos de R21](docs/R21_EXTREMOS_EXACTOS.md) ya identifican cursor→masa y PIN22→cursor en el solver global. Pasan 128 pasos de integración Python independiente (máximo de nodo 0,22 nV), Jacobianos, corrientes de los cortos, heap cero y stack con cambios entre topes. El barrido acepta 17408 muestras y conserva los seis fallos previos.

La [dirección Newton reutilizada](docs/DIRECCION_NEWTON_REUTILIZADA.md) conserva en bits los 23224 valores de las capturas de apagado y reduce 23,18 % el costo de la política precisa: **2,953 ms/bloque**. Mantiene heap cero y los gates de voltaje. Todavía excede el deadline de 1,333 ms.

El [criterio temporal de voltaje](docs/CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) corrige las 96 sondas de apagado (máximo interno 0,150 nV frente a las raíces independientes). Pasa de nuevo el estrés de 752384 muestras y heap cero. Su primera implementación costó 3,939 ms/bloque, luego reducido reutilizando direcciones; aún no cumple tiempo real. Los saltos abruptos y el contorno real siguen pendientes.

El [apagado sintético de VCAs](docs/APAGADO_VCA_GLOBAL_66.md) registró 20/96 sondas con error interno >1 µV en la política anterior, hasta 1,318 mV. El criterio de voltaje corrige esa brecha; los saltos de una muestra siguen fallando. Estos estímulos no modelan el contorno.

La [inicialización DC global con semilla completa](docs/DC_GLOBAL_SEMILLA_COMPLETA.md) resuelve cutoff máximo y contrasta 14 puntos independientes con error máximo 2,25 nV. Añade criterio de corrección de voltaje para nodos débiles. Conserva dos rechazos exploratorios de semillas desplazadas; apagado de Q21 sigue pendiente.

El [barrido de extremos global](docs/EXTREMOS_CONTROLES_GLOBAL_66.md) detectó fallos de arranque con cutoff máximo y de transición al apagar Q21. [R20 admite sus extremos exactos](docs/R20_EXTREMOS_EXACTOS.md), con 128 pasos independientes y SW18 ON/OFF; R21 exacto está cerrado en el solver global. El barrido actualizado mantiene seis casos fallidos de arranque/apagado.

El [banco de stack Win64](docs/STACK_GLOBAL_66_WIN64.md) pasa hilos de 512 KiB. La compilación DC observaba 324 KiB; con [topes R21](docs/R21_EXTREMOS_EXACTOS.md) se observan 328 KiB comprometidos durante procesamiento/reintentos. La observación por páginas deja pendiente el pico exacto y la admisión en RackForge.

El [refinamiento temporal global](docs/REFINAMIENTO_TEMPORAL_GLOBAL_66.md) añade 26880 pasos a 48/96/192 kHz, con dos señales y ambos R61. Las diferencias entre pasos se reducen con cocientes de 1,98–1,99; las diferencias de discretización siguen siendo medibles a tasas de audio.

El [ensamblado global ordenado](docs/ENSAMBLADO_GLOBAL_ORDENADO.md) y las [exponenciales compartidas](docs/EXPONENCIALES_GLOBAL_66.md) reducen el costo medio a 2,233 ms/bloque, con los gates independientes y heap cero. El [estrés largo](docs/ESTRES_LARGO_GLOBAL_66.md) añade 752384 muestras a 44,1/48/96 kHz con ambos R61, sin fallos y con cambios de controles, EMPHASIS y cargas. El deadline de 1,333 ms sigue excedido.

Las [48 ventanas contrastadas con Python](docs/VENTANAS_INDEPENDIENTES_ESTRES_GLOBAL.md) añaden 192 pasos alrededor de switches y en tramos tardíos, con historiales eléctricos compartidos: máximo interno 0,205 µV y J7 0,398 nV. Amplían el contraste numérico de la escena.

**Corpus documental reunido.** Hay manual de servicio completo (82 páginas), esquemas, manual de operación temprano, boletines de fábrica, patente y hojas de componentes; sus hashes y límites están en el [registro de fuentes](docs/FUENTES.md). El proyecto [avanza sin acceso físico](docs/VALIDACION_SIN_HARDWARE.md): la primera ruta tiene como blanco la placa osciladora **CA3046** documentada. Ya existe un [subgrafo de VCO 1](docs/VCO1_CA3046.md), referencias ejecutables de sus primeras etapas, un [bus de mezcla de cinco fuentes](docs/MEZCLADOR_PANEL.md) y un [punto DC condicionado del ladder completo](docs/LADDER_EBERS_MOLL_DC.md) con [recuperación y EMPHASIS temporales](docs/TRANSITORIO_FILTRO_ACOPLADO.md). Faltan la identificación de parámetros de una placa real, el motor de audio y el plugin instalable. No hay afirmación de fidelidad sonora. El nombre RF-D designa el proyecto; no implica afiliación con Moog Music.

## Objetivo musical

La [columna resistiva del ladder en DC](docs/COLUMNA_RESISTIVA_LADDER_DC.md), las [dos pilas activas](docs/PILAS_ACTIVAS_LADDER_DC.md), el [cierre Ebers–Moll de 16 nodos](docs/LADDER_EBERS_MOLL_DC.md), su [núcleo de pequeña señal](docs/LADDER_PEQUENA_SENAL.md), la [recuperación activa Q5–Q8](docs/RECUPERACION_ACTIVA_FILTRO.md), el [lazo de EMPHASIS en pequeña señal](docs/LAZO_EMPHASIS_PEQUENA_SENAL.md) y el [transitorio no lineal acoplado](docs/TRANSITORIO_FILTRO_ACOPLADO.md) con [Jacobiano analítico](docs/JACOBIAN_ANALITICO_FILTRO.md) tienen referencias ejecutables. La [carga pasiva del primer VCA](docs/CARGA_VCA1_FILTRO.md) ya está unida a la red AC y al [transitorio de 27 nodos](docs/TRANSITORIO_CARGA_VCA1.md). El [barrido de supuestos](docs/BARRIDO_SESGO_LADDER_DC.md) y la [malla de sensibilidad de EMPHASIS](docs/SENSIBILIDAD_EMPHASIS.md) delimitan escenarios; faltan parámetros de una placa real y motor de audio.

Recrear la voz **monofónica** de un Model D para bajos, leads y articulación en vivo: tres osciladores, ruido, mezclador, filtro ladder, contornos de filtro y volumen, glide, ruedas y ruta de salida. Los presets y el cambio de sonidos en RackForge serán funciones del host/plugin; no se presentarán como memoria del instrumento histórico.

El [objetivo técnico](docs/OBJETIVO.md) define qué queda dentro de la emulación y qué exige una decisión de revisión. No se mezclan características de los Model D originales con las reediciones de 2016/2022 sin evidencia y una decisión explícita.

## Cómo empezar

La [representación por incrementos y memorias compensadas](docs/BIESTABLE_INCREMENTOS_COMPENSADOS.md) cierra el intervalo de C2 antes rechazado, con los mismos gates, y verifica 32 pasos posteriores. El criterio adaptativo v2 usa voltajes de nodos y junturas independientes del origen de Q; el [barrido completo](docs/BIESTABLE_BARRIDO_COMPENSADO.md) conserva el fallo de refinamiento entre políticas.

1. Revisar el [mapa de revisiones](docs/REVISIONES.md), el [plan de investigación](docs/PLAN.md) y el [protocolo sin hardware](docs/VALIDACION_SIN_HARDWARE.md); fijar la revisión documental antes de derivar constantes DSP.
2. Usar el [registro de fuentes](docs/FUENTES.md) para localizar la página exacta y los [hallazgos técnicos](docs/HALLAZGOS.md) para definir cada contraste.
3. Derivar cada [bloque de circuito](docs/BLOQUES.md) en unidades eléctricas y registrar incertidumbres en la [matriz de fidelidad](docs/MATRIZ_DE_FIDELIDAD.md).
4. Preparar las escenas de [CAPTURAS.md](docs/CAPTURAS.md) como pruebas simuladas y usar audio público sólo en los contrastes permitidos por su procedencia.
5. Aplicar los [gates de RACE](https://github.com/kalexis1994/rackforge-race/blob/main/docs/06-circuitos.md) y el [contrato de plugins RackForge](https://github.com/kalexis1994/rackforge/blob/main/docs/PLUGIN_DEVELOPMENT.md) al implementar y publicar.

La [derivación parcial de VCO 1](docs/VCO1_CA3046.md) explica los límites de la referencia ejecutable. Las referencias básicas usan la biblioteca estándar; el nuevo laboratorio de 94 nodos/modos requiere NumPy, registrado en `requirements-lab.txt`. Tras instalar esa dependencia puede ejecutarse `python -m unittest discover -s tests -v`.

La ruta experimental BUS→J7 dispone de [vectores de admisión numérica](docs/VECTORES_PORTABILIDAD_AURICULARES.md). Ya existen un [puerto Rust de la placa 3](docs/PUERTO_NATIVO_PLACA3_AURICULARES.md), la [frontera R77/R21](docs/PUERTO_NATIVO_PANEL_AURICULARES.md), la [salida desde C2 hasta J7](docs/PUERTO_NATIVO_C2_SALIDAS.md), la [conversión Q1/Q12/Q17 con C4](docs/PUERTO_NATIVO_C4_CONVERSION_SALIDA.md), el [segundo VCA unido hasta J7](docs/VCA2_SALIDA_NATIVA.md), el [primer VCA con R2/C6/C15 hasta J7](docs/VCA1_SALIDA_NATIVA.md), la [recuperación Q5–Q8](docs/RECUPERACION_SALIDA_NATIVA.md), el [ladder nativo](docs/LADDER_SALIDA_NATIVA.md) y el [lazo C10/EMPHASIS](docs/EMPHASIS_NATIVO_C10.md). Los bloques tienen oráculos independientes: el nuevo cierre BUS→J7 coincide con un modelo monolítico Python de 62 nodos en ambos R61 y en una traza de 192 muestras con cambios de R14/SW18 (error máximo J7 25,6 nV, relación señal/error **numérica** 115 dB). El [perfil de costo](docs/PERFIL_COSTO_CADENA_NATIVA.md) localiza la anidación de solves; [compartir la factorización de tangentes](docs/OPTIMIZACION_TANGENTES_MULTI_RHS.md) redujo el costo parcial. El cierre C10 tarda ~22,6 ms por bloque de 64 frente a 1,33 ms disponibles. La corriente de Q28 y las leyes de volumen siguen siendo límites impuestos. Aún no es una voz ni cumple el presupuesto de tiempo real; equivalencia numérica no implica fidelidad sonora. Puede comprobarse con `cargo test --workspace`.

El [control Q26/Q28 nativo](docs/CUTOFF_NATIVO_Q26_Q28.md) incluye C18, ambas junturas BJT y las ramas de cutoff, contorno, teclado, modulación y jack. La [cadena integrada hasta J7](docs/CUTOFF_LADDER_J7_NATIVO.md) calcula la cola desde el circuito y coincide con un oráculo monolítico de 66 nodos en 128 pasos (error J7 22,4 nV). Tarda ~25,7 ms por bloque de 64 frente a 1,33 ms disponibles. BUS y las fuentes de contorno/teclado/modulación siguen impuestos; falta una voz completa y el gate de tiempo real.

El [solver global analítico experimental de 66 nodos](docs/SOLVER_GLOBAL_66_NODOS.md) conserva el mismo circuito y evita los solves anidados. Se contrastó contra Python, por diferencias finitas de todo el Jacobiano y en 8192 muestras contra la ruta por puertos. Cinco comparaciones alternadas dieron **9,39 veces menos costo medio**: **2,559 ms** por bloque frente a **24,037 ms**. Conserva los criterios de error y cero heap; todavía excede los **1,333 ms** disponibles y no se admite como motor del plugin.

## Límites de recursos

El [contorno de volumen de placa 2](docs/CONTORNO_VOLUMEN_CIRCUITO.md) tiene grafo y oráculo de transistores, gatillo y cargas capacitivas. Las primeras semillas detectaron dos raíces; el cierre cargado y la búsqueda ampliada registran tres, sin elegir una. El [puerto nativo del seguidor Q3/Q2](docs/SEGUIDOR_VOLUMEN_NATIVO.md) pasa 60 casos independientes con error máximo de nodo 7,63 nV y entrega corrientes/tangentes para el acoplamiento posterior. No equivale todavía a una envolvente física validada ni a una voz completa.

Manuales descargados, esquemas, fotos internas, mediciones y WAV de referencia pertenecen a `references-local/` o `captures/`, fuera de Git. El repo guarda identificadores, hashes, derivaciones, pruebas y resultados. Ningún paquete `.rfplugin` incluirá material original que no se pueda distribuir.
