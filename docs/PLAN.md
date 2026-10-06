# Prioridad vigente

La [unión VCO/contorno](CONTORNO_VCO_UNION_RESULTADOS.md) rechaza las cuatro
escenas monolíticas. El ensayo por R45 falla el control previo aun con
dos parejas completas: el puerto no cierra y el VCO siguiente rechaza.
Prioridad: reproducir y resolver el VCO aislado con BUS variable, conservando
tarjeta, R45 y gates; luego cerrar la unión y extender la nota completa.
El [diagnóstico aislado](RESET_VCO_AISLADO_RESULTADOS.md) reproduce el reloj
y los seis vectores originales al observar once nodos adicionales. Dos
bancos de equivalencia terminal pasan; el control VCO y ambas series de
regularización rechazan. La [sonda Newton local](NEWTON_RESET_RESULTADOS.md)
conserva exactamente el baseline y observa ambos JFET rechazados sin
limitadores, con grandes correcciones en el polo L2 interno del 741.
La [historia de L2](POLO_741_RESET_RESULTADOS.md) conserva exactamente
cuatro trayectorias y refuta la hipótesis del RHS variable en 811 grupos.
La reformulación condicional queda no medida. Próximo: KCL de 16/17 y
acoplamientos G4/EOS, escala de incógnitas y protocolo de representación
si la medición lo justifica. El reloj local difiere del oficial: contrastar
builds antes de atribuirle la causa y volver al cierre de puerto.
El [contorno cargado](CONTORNO_PLACA4_RESULTADOS.md) mantiene diez escenas
y tres contrastes con entrada senoidal; la [voz con contorno fijo](VOZ_ACOPLADA_RESULTADOS.md)
mantiene alcance nominal y rechazos de cutoff bajo/mute. Contorno de filtro,
alimentación común, Q21, ruta portable y deadlines pendientes.
La continuación formal del biestable sigue aplazada. Las secciones
siguientes son historial y no el orden actual.

# Plan de investigación RACE para RF-D

No habrá acceso a una unidad física. El [protocolo sin hardware](VALIDACION_SIN_HARDWARE.md) define qué podemos comprobar y qué afirmaciones quedan fuera de alcance.

## Fase A — Perfil documental y circuito

1. El corpus de manuales, esquemas, boletines y datasheets está indexado en [FUENTES.md](FUENTES.md); resolver conflictos mediante [REVISIONES.md](REVISIONES.md).
2. Congelar la primera variante en la placa osciladora CA3046 Fig. 9-3 de SVC-204D. No fusionar Fig. 9-2, la primera placa discreta ni reediciones.
3. Transcribir cada placa a grafo de nodos, valores, conexiones y estados de control. Documentar calibración de fábrica, tolerancias y componentes no identificados.

**Salida:** perfil documental en [OBJETIVO.md](OBJETIVO.md), mapa de nodos reproducible y derivaciones por bloque. La falta de un serial físico no impide modelar el circuito nominal.

## Fase B — Solver y banco de pruebas

El [refinamiento de memoria](BIESTABLE_MEMORIA_JUNTURAS_RESULTADOS.md)
cierra el soporte 33 con dieciséis macroceldas, manteniendo curva, radio,
reloj y 22 memorias reales en P fija. **34 soportes hasta ≈350 µs**,
local nuevo **≤0,644 µV**, acumulado **≤0,793 µV**. El control de ocho celdas
rechaza y se conserva; 32/64 quedan no medidas por primera admisión.
Una inversa y tres tasas reutilizadas por identidad; 24 budgets y 192
subcertificados nuevos idénticos a los del control original en todos sus bytes.
Diez pruebas pasan al primero. Corpus de 763 entradas, 214 informes y 259
hashes propios, con 20 fuentes históricas y las tres excepciones CRLF.
No hay solves, candidatos o sistemas P nuevos ni reinicio del anclaje.
Próximo: [continuación refinada 34–39](BIESTABLE_CONTINUACION_REFINADA_PLAN.md).
**1 mV global sigue abierto.**

El [segundo banco preparado](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_RESULTADOS.md)
certifica **33 soportes contiguos hasta ≈337,5 µs**, acumulado **≤0,793 µV**.
Los cuatro anchos admiten el soporte 32 y rechazan el 33: mejor cota rechazada ≈1,164 µV
para radio 1 µV. Se conserva el primer hueco y seis plantillas no alcanzadas.
Cinco inversas/preparaciones, 495 tasas, 64 budgets y 512 subcertificados
se reproducen contra el control completo. El grupo de cuatro junturas domina
el forcing acotado del nodo 66 en el interior; su término directo es pequeño.
Once pruebas aceptadas: nueve primarias al primero y dos archivísticas al
segundo. Corpus de 723 entradas, 184 informes y 228 hashes propios; 19
fuentes históricas más el fallo propio del fixture archivado con fuente exacta.
Próximo: [refinar memoria en el hueco](BIESTABLE_HUECO_MEMORIA_JUNTURAS_PLAN.md).
**1 mV global sigue abierto.**

La [continuación con preparación explícita](BIESTABLE_CONTINUACION_PREPARADA_RESULTADOS.md)
certifica **32 soportes contiguos hasta ≈325 µs**, acumulado **≤0,793 µV**.
Renueva nueve candidatos, una inversa uniforme y 99 consultas de tasa;
una preparación identifica el dominio nuevo en 64 budgets y 512 subcertificados.
Transporta las 22 memorias reales en P fija. Pico local nuevo ≤0,524 µV,
nodo 66 dentro del soporte 31; C7 termina con ≤461,567 nV.
Diez pruebas nuevas pasan al primero, con comparación completa contra control;
corpus de 688 entradas, 159 informes, 202 hashes propios y 19 fuentes históricas.
Parada por límite declarado. Próximo:
[segundo banco preparado, soportes 32–39](BIESTABLE_CONTINUACION_PREPARADA_SEGUNDA_PLAN.md).
Este banco no mide rendimiento nuevo. **1 mV global sigue abierto.**

La [preparación exacta de acciones](BIESTABLE_ACCIONES_PREPARADAS_RESULTADOS.md)
reproduce **64 presupuestos y 512 subcertificados idénticos en bytes** frente
al control y archivo original. Una pasada balanceada AB/BA reduce el wall
**24,39 %**, de 286,72 s a 216,79 s con preparación e identidades incluidas.
Son tiempos del laboratorio offline en este equipo. Se conservan **24 soportes
hasta ≈225 µs**, acumulado **≤0,793 µV**. Corpus: 657 entradas, 138 informes,
180 hashes propios y 18 fuentes históricas conservadas. Las siete pruebas
primarias pasan al segundo, tras corregir una expectativa de representación
sin cambiar helper, banco o tiempos. Las dos del corpus pasan al segundo;
ambos fallos de fixtures quedan archivados. Próximo:
[continuación con preparación explícita](BIESTABLE_CONTINUACION_PREPARADA_PLAN.md).
**1 mV global sigue abierto.**

La [continuación compartida](BIESTABLE_CONTINUACION_COMPARTIDA_RESULTADOS.md)
certifica **24 soportes contiguos hasta ≈225 µs**, acumulado **≤0,793 µV**.
Ocho referencias nuevas transportan 22 memorias reales; pico local nuevo
≤0,418 µV. Se renuevan nueve candidatos, una inversa uniforme, 99 consultas
de tasa y 512 acciones, sin solves de trayectoria o sistemas nuevos de P.
Diecisiete artefactos completos y su manifiesto fijan todas las identidades.
Nueve pruebas nuevas pasan al primero; corpus de 643 entradas y 135 informes.
La parada es por límite declarado. Próximo:
[preparar acciones con equivalencia exacta](BIESTABLE_ACCIONES_PREPARADAS_PLAN.md).
**1 mV global sigue abierto.**

El [recinto compartido](BIESTABLE_RECINTOS_COMPARTIDOS_RESULTADOS.md)
vuelve a certificar los mismos 16 soportes hasta ≈125 µs, error acumulado
≤0,793 µV. Una inversa uniforme sustituye 64 recintos y requiere 99 consultas
de tasa frente a 6336; se recalculan las 512 acciones con defecto y cola.
Ocho pruebas nuevas pasan al primero; corpus de 613 entradas y 115 informes.
P, curvas, RHS y transporte real se conservan. Este bloque reduce costes
de certificación offline; no amplía la cobertura temporal ni admite audio.
Próximo: [continuación con dominios nuevos](BIESTABLE_CONTINUACION_COMPARTIDA_PLAN.md).
**1 mV global sigue abierto.**

El [prefijo con referencias curvas](BIESTABLE_PREFIJO_CURVO_RESULTADOS.md)
certifica **dieciséis intervalos contiguos hasta aproximadamente 125 µs**,
con **error nodal acumulado ≤0,793 µV**. Añade ocho soportes con picos
locales ≤0,372 µV, transportando 22 memorias reales sin reset. Renueva
64 recintos de inversa, 6336 consultas de tasa y 512 acciones completas;
cero solves nuevos. Los archivos por soporte y su manifiesto conservan
el banco íntegro y todas sus identidades. La parada es por límite declarado,
sin hueco encontrado en este banco. Ocho pruebas nuevas aceptadas;
corpus de 600 entradas y 112 informes, con versiones anteriores conservadas.
Próximo bloque:
[recintos compartidos](BIESTABLE_RECINTOS_COMPARTIDOS_PLAN.md).
**1 mV global sigue abierto.**

La [referencia cuadrática de C7](BIESTABLE_REFERENCIA_CURVA_RESULTADOS.md)
certifica **ocho intervalos contiguos hasta aproximadamente 25 µs**,
con **error nodal acumulado ≤0,793 µV**. El nuevo soporte conserva sus
endpoints y alcanza una cota local ≤0,327 µV; la afín comparable rechaza
por ≈4,185 µV. Se renuevan 32 recintos de inversa, 3168 consultas de tasa
y 256 acciones completas en P fija, sin solves nuevos. El integrador y
los estados publicados permanecen intactos. Ocho pruebas nuevas aceptadas;
corpus de 578 entradas y 101 informes, con fallos conservados. Próximo bloque:
[continuación curva](BIESTABLE_PREFIJO_CURVO_PLAN.md).
**1 mV global sigue abierto.**

El [forcing temporal firmado de C7](BIESTABLE_FORCING_C7_RESULTADOS.md)
certifica **siete intervalos contiguos hasta aproximadamente 12,5 µs**,
con **error nodal ≤0,793 µV**. Un cambio auxiliar de coordenadas conserva
el signo temporal y paga defecto, restos y todos los acoplamientos Bp;
restaura las 22 memorias reales antes de transportarlas. Ocho regresiones
primarias y dos del corpus pasan al primero, sin solves o tasas nuevos.
Corpus de 564 entradas y 97 informes. Próximo bloque:
[referencia curva con endpoints conservados](BIESTABLE_REFERENCIA_CURVA_PLAN.md).
**1 mV global sigue abierto.**

El [prefijo con acciones dirigidas](BIESTABLE_PREFIJO_DIRIGIDO_RESULTADOS.md)
certifica **seis intervalos contiguos hasta aproximadamente 6,25 µs**,
con **error nodal ≤0,754 µV**. Añade 48 inversas, 4752 consultas de tasa
y 384 acciones en P retenida, sin solves de trayectoria. El siguiente
soporte no cierra en radio 1 µV: forcing de C7 domina ≈1,2904 µV.
La repetición separada recupera dos presupuestos enormes de 10 µV,
que rechazan, preservando sus fallos de registro originales. Dieciséis
pruebas nuevas aceptadas; corpus de 535 entradas y 94 informes. Próximo bloque:
[forcing de memoria y registro](BIESTABLE_FORCING_MEMORIA_PLAN.md).
**1 mV global sigue abierto.**

La [acción dirigida del residual](BIESTABLE_ACCION_RESIDUAL_RESULTADOS.md)
certifica **cuatro intervalos contiguos hasta aproximadamente 1,5625 µs**,
con error nodal **≤0,754 µV**. Basta mejorar el término algebraico directo
para cerrar el cuarto soporte, sin cambiar trayectoria o circuito.
Se reutilizan 16 inversas y tasas; 128 acciones incluyen defecto y cola,
sin solves, precondicionadores o métricas nuevos. Diez pruebas nuevas
pasan al primer intento; el [corpus](BIESTABLE_ACCION_RESIDUAL_ENTRADAS.md)
recupera 518 entradas de 90 informes. Próximo bloque:
[prefijo con forcing dirigido](BIESTABLE_PREFIJO_ACCION_PLAN.md).
**1 mV global sigue abierto.**

El [prefijo con 22 cotas transportadas](BIESTABLE_PREFIJO_22_RESULTADOS.md)
certifica **tres intervalos contiguos hasta aproximadamente 781,25 ns**,
con error nodal **≤0,754 µV**. El cuarto tramo rechaza con ≈1,0044 µV
en radio 1 µV; se conserva el último endpoint probado y la memoria conocida.
Hay 16 nuevos precondicionadores, 32 recintos y 3168 consultas LDL,
sin solves de trayectoria ni métricas nuevas. El fallo de salida de
un primer lanzamiento queda archivado. Diez pruebas nuevas pasan al
primer intento; el [corpus](BIESTABLE_PREFIJO_22_ENTRADAS.md)
recupera 507 entradas de 88 informes. Próximo bloque:
[acción algebraica del residual](BIESTABLE_ACCION_RESIDUAL_PLAN.md).
**1 mV global sigue abierto.**

La [comparación de 22 grupos y memoria por coordenada](BIESTABLE_MEMORIA_COORDENADA_RESULTADOS.md)
certifica **dos intervalos contiguos hasta 390,625 ns**, con error nodal
**≤0,588 µV** en la variante seleccionada. Ambos anclajes cierran el tubo
de 1 µV; el refinamiento mejora 16 de 21 cotas lineales. Se reutilizan
inversas, estados, residual y P, sin nuevos solves o precondicionadores.
Diez pruebas nuevas pasan al primer intento; el [corpus](BIESTABLE_MEMORIA_COORDENADA_ENTRADAS.md)
recupera 495 entradas de 86 informes. Próximo bloque:
[prefijo con memoria dirigida](BIESTABLE_PREFIJO_22_GRUPOS_PLAN.md).
**1 mV global sigue abierto.**

El [intento de continuación contigua](BIESTABLE_PREFIJO_CERTIFICADO_RESULTADOS.md)
valida transporte de memoria y puentes exactos de norma, pero el segundo
intervalo **195,3125→390,625 ns** rechaza: presupuesto ≈7,35 µV en
el tubo de 1 µV, dominado por el anclaje propagado. El primer intervalo
sigue certificado, con evidencia intacta y sin reiniciar DC.
Diez regresiones nuevas pasan al primer intento; el [corpus](BIESTABLE_PREFIJO_CERTIFICADO_ENTRADAS.md)
recupera 484 entradas de 84 informes. Próximo corte:
[refinar memoria por coordenada](BIESTABLE_MEMORIA_POR_COORDENADA_PLAN.md).
**1 mV global sigue abierto.**

La [comparación dirigida con métrica común de junturas](BIESTABLE_TUBO_BLOQUES_RESULTADOS.md)
certifica el **primer intervalo continuo de 195,3125 ns**, con error
nodal **≤0,586 µV** dentro de un tubo de 1 µV. El banco conserva
las otras ocho variantes rechazadas; no cambia estados, circuito o residual.
Diez regresiones nuevas pasan al primer intento; el [corpus ampliado](BIESTABLE_TUBO_BLOQUES_ENTRADAS.md)
recupera 472 entradas de 82 informes. La memoria final
queda disponible para [continuar sin reiniciarla](BIESTABLE_CONTINUACION_CERTIFICADA_PLAN.md).
El gate global de **1 mV sigue abierto**, junto a física, voz y deadline.

La [primera reconstrucción y prueba de tubo no lineal](BIESTABLE_PRIMER_TUBO_RESULTADOS.md)
cubre un soporte de **195,3125 ns** con dos estados reales y memoria Q(v).
Los **24 recintos medios del descriptor** son invertibles, pero los
**tres cierres rechazan**: el presupuesto escalar excede sus radios.
En ese corte, la duración de error continuo certificado quedó en cero. Se conserva
el experimento para estudiar [comparación dirigida por bloques](BIESTABLE_PRIMER_TUBO_BLOQUES_PLAN.md).
El [corpus ampliado](BIESTABLE_PRIMER_TUBO_ENTRADAS.md) incluye 80 informes
y trece versiones fallidas de pruebas. Los gates globales de 1 mV,
física, audio y deadline siguen abiertos.

La [publicación tipada del evento y el arranque propio](BIESTABLE_POST_KEY_ARRANQUE_RESULTADOS.md)
conservan las 25 cargas y certifican el anclaje high+low a **~37,51 nV por nodo**.
Los **512 intervalos hasta ~2,332 ms** pasan KCL, ramas y restauración,
con BE inicial y BDF2 después; diferencia frente al arranque histórico
**~3,59 pV nodales** en los mismos endpoints. Es un resultado del integrador
offline, sin cambios en el motor nativo ni prueba de error temporal continuo.
El [corpus](BIESTABLE_POST_KEY_ARRANQUE_ENTRADAS.md) reconstruye
**450 entradas de 78 informes**, conservando diez versiones fallidas.
Diez regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: [primer soporte continuo,
anclaje convertido y resto no lineal](BIESTABLE_PRIMER_SOPORTE_CONTINUO_PLAN.md).

El [estado consistente post-KEY](BIESTABLE_POST_KEY_RESULTADOS.md)
resuelve 119 ecuaciones sin avanzar el reloj, conservando las 25 cargas.
Dos semillas convergen; un recinto parametrizado por la incertidumbre DC
acota el error local a **~37,51 nV nodales**, con V77_post≈9,646 V.
Se conservan el rechazo de la primera escala y el gate backward binary64.
La publicación racional de ese corte pasaba KCL y restricciones; su
publicación en el integrador quedaba pendiente. El [corpus](BIESTABLE_POST_KEY_ENTRADAS.md)
reconstruye **439 entradas de 76 informes** y diez versiones fallidas.
Diez regresiones nuevas pasan, preservando ambos intentos primarios.
**1 mV global sigue abierto.** Próximo corte: [estado high+low, arranque
sin historia y primer tramo contiguo](BIESTABLE_POST_KEY_PUBLICACION_PLAN.md).

El [DC nominal certificado y la auditoría del evento KEY](BIESTABLE_DC_EVENTO_RESULTADOS.md)
acotan la raíz local KEY=0 a **~74 pV nodales** y la memoria inicial a
**~148 pV ponderados**, con cuatro cajas contractivas y 25 cargas verificadas.
CR10 exige un salto algebraico de al menos **~8,27 V** para permanecer
en el dominio al pasar KEY a 10 V. En ese corte, el estado post-KEY aún no estaba resuelto.
El [corpus](BIESTABLE_DC_EVENTO_ENTRADAS.md) reconstruye **423 entradas**
de 73 informes y conserva nueve versiones fallidas históricas de tests.
Ocho regresiones nuevas pasan; la suite primaria conserva sus dos intentos.
**1 mV global sigue abierto.** Próximo corte: [consistencia post-KEY](BIESTABLE_ESTADO_POST_KEY_PLAN.md),
recinto de cargas, publicación del evento y primer tramo contiguo.

El [inventario de cobertura y métricas](BIESTABLE_COBERTURA_METRICAS_RESULTADOS.md)
verifica **6.486 intervalos desde DC y 1.536 refinados**, pero el soporte
certificado seleccionado cubre sólo **~0,342 µs de 3 ms (~0,0114 %)**.
La unión N2/N4 tiene cuatro tramos y cinco huecos; el error real aún no
está certificado. Se calculan **36 conversiones de norma y 990 consultas**;
no propagan regiones faltantes ni identifican errores de historias distintas.
El [corpus](BIESTABLE_COBERTURA_METRICAS_ENTRADAS.md) reconstruye **412 entradas**
de 71 informes; ocho regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** El [plan desde DC](BIESTABLE_COBERTURA_DESDE_DC_PLAN.md)
prioriza consistencia KEY 0→10 V, anclaje, prefijo contiguo, resto y reset.

El [presupuesto condicional del anclaje](BIESTABLE_PRESUPUESTO_ANCLAJE_RESULTADOS.md)
reconstruye **4.512 pares de celda/nodo** y 18 objetivos para el gate de 1 mV.
Ataque N2 permite ~0,185 µV de anclaje ponderado sin reserva, o ~0,092 µV
con 0,5 mV reservados hipotéticamente. No se ha acotado el error entrante
ni el resto no lineal. Reset conserva sus dos rechazos y no recibe presupuesto.
El [corpus](BIESTABLE_PRESUPUESTO_ANCLAJE_ENTRADAS.md) reconstruye **401 entradas**
de 69 informes; siete regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: inventario desde DC, anclajes
entre ventanas, conversiones de norma y estrategia de cobertura para reset.

El [radio balanceado en la misma métrica](BIESTABLE_JUNTURAS_BALANCEADA_RESULTADOS.md)
estrecha **14/48 tasas** con pesos de prueba fijados antes de medir.
Ataque N2 baja de ~9,16e9 V a **~6,72 µV** de término forzado hipotético;
las seis ventanas aceptadas quedan por debajo de 10 µV y no empeoran.
P, norma, conversiones y anclaje se conservan; reset mantiene sus dos rechazos.
La contracción interna sigue certificada en 32 celdas de prefijo y cola.
El [corpus](BIESTABLE_JUNTURAS_BALANCEADA_ENTRADAS.md) reconstruye **390 entradas**
de 67 informes; ocho regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: presupuesto admisible de anclaje,
resto no lineal y cobertura continua desde DC, manteniendo todos los rechazos.

El [certificado de tasa dirigida](BIESTABLE_JUNTURAS_DIRIGIDA_RESULTADOS.md)
conserva P, norma, conversiones y anclaje, y estrecha **40/48 tasas**.
Ataque N4 baja a término forzado hipotético **~5,22 µV**; ataque N2
sigue enorme (~9,16e9 V). Las seis cotas calculadas no empeoran frente a
la variante cuadrática anterior; reset conserva sus dos candidatos rechazados.
Sólo cambia M_JJ, con 1.584 consultas racionales y sin nuevas inversas del circuito.
El [corpus](BIESTABLE_JUNTURAS_DIRIGIDA_ENTRADAS.md) reconstruye **379 entradas**
de 65 informes y conserva ocho versiones fallidas históricas.
Ocho regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: balancear el radio en la base
D con regla fija, manteniendo P, conversiones y rechazos explícitos.

La [métrica cuadrática fija de junturas](BIESTABLE_JUNTURAS_METRICA_RESULTADOS.md)
acepta seis candidatos y rechaza los dos de reset. **32 celdas de prefijo
y cola** certifican contracción interna variable; ataque no obtiene esa prueba.
Las conversiones completas producen una comparación mixta: sólo cola N2
baja ligeramente; prefijo y ataque empeoran. Se preservan las ocho filas,
el mismo anclaje y los candidatos rechazados, sin promover la variante.
El [corpus](BIESTABLE_JUNTURAS_METRICA_ENTRADAS.md) reconstruye **368 entradas**
de 63 informes y conserva ocho versiones fallidas históricas.
Nueve regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: perturbación dirigida del
certificado de tasa, conservando P, conversiones y acoplamientos.

El [generador firmado de junturas](BIESTABLE_JUNTURAS_MODAL_RESULTADOS.md)
certifica modos congelados de las **64 celdas**: 48 son Hurwitz y las
16 de reset tienen una raíz real positiva del bloque interno aislado.
Ataque y cola combinan modos estables con crecimiento instantáneo de norma:
32 celdas identifican amplificación no normal potencial. No se modifica
ninguna propagación ni se infiere estabilidad del circuito variable completo.
El [corpus](BIESTABLE_JUNTURAS_MODAL_ENTRADAS.md) verifica **357 entradas**
de 61 informes y conserva ocho versiones fallidas anteriores.
Ocho regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: métrica cuadrática común
certificada para ataque/cola, con conversiones, acoplamientos y anclaje.

El [certificado espectral racional](BIESTABLE_JUNTURAS_ESPECTRO_RESULTADOS.md)
estrecha las **64 cotas** de junturas RMS, incluyendo incertidumbre del
recinto completo y **2.112 consultas LDLᵀ**. Certifica disipación interna
en las 16 celdas de prefijo; ataque/reset/cola conservan mu2 positiva.
Las ocho cotas nodales bajan: cola N4 da término forzado hipotético ~9,92 µV.
El [corpus](BIESTABLE_JUNTURAS_ESPECTRO_ENTRADAS.md) verifica **346 entradas**
de 59 informes, con ocho versiones fallidas anteriores preservadas.
Siete regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: generador firmado y
comportamiento modal frente a crecimiento de norma, conservando anclaje y restos.

La [variante RMS de junturas](BIESTABLE_JUNTURAS_RMS_RESULTADOS.md)
conserva signos en la parte simétrica y convierte todos los acoplamientos,
forzamientos y mapas nodales. Ataque/cola mejoran, prefijo empeora y reset
queda prácticamente igual; se conserva la comparación completa. Cola N4
da término forzado hipotético ~1,31 mV, con anclaje todavía desconocido.
El [corpus](BIESTABLE_JUNTURAS_RMS_ENTRADAS.md) verifica **335 entradas**
de 57 informes y preserva ocho versiones fallidas anteriores de tests.
Siete regresiones nuevas pasan al primer intento.
**1 mV global sigue abierto.** Próximo corte: certificado espectral racional
de la parte simétrica para distinguir la pérdida de Gershgorin.

La [comparación dirigida de bloques](BIESTABLE_COMPARACION_BLOQUES_RESULTADOS.md)
propaga seis grupos físicos con **64 núcleos de extremo y 64 de pico**.
Las ocho cotas bajan: prefijo N4 da término forzado ~33,72 µV y reset N4
~0,487 µV con anclaje cero hipotético. Ataque/cola siguen enormes.
El [corpus](BIESTABLE_COMPARACION_BLOQUES_ENTRADAS.md) verifica **324 entradas**
de 55 informes y conserva ocho versiones fallidas anteriores de tests.
Ocho regresiones nuevas pasan al primer intento.
El anclaje y los restos no lineales siguen pendientes. **1 mV global sigue abierto**.
Próximo corte: cancelaciones internas del grupo de junturas y cobertura completa.

La [propagación por celdas](BIESTABLE_PROPAGACION_CELDAS_RESULTADOS.md)
reconstruye **64 inversas estructuradas** y distribuye el residual en cada
celda. Las ocho cotas tangentes bajan; reset N4 da término forzado
~0,529 µV con anclaje cero hipotético, mientras ataque/cola siguen enormes.
Se conserva el anclaje desconocido y se distinguen extremo y pico interior.
El [corpus](BIESTABLE_PROPAGACION_CELDAS_ENTRADAS.md) verifica **313 entradas**
de 53 informes y ocho versiones fallidas de tests; nueve regresiones nuevas pasan.
**1 mV global sigue abierto**.
Próximo corte: estructura de bloques para la estabilidad de ataque/cola,
restos no lineales, anclaje y recorrido completo.

El [descriptor ponderado ideal](BIESTABLE_DESCRIPTOR_PONDERADO_RESULTADOS.md)
cubre la variación de coeficientes en **64 celdas de ocho intervalos**:
todas certifican la inversa ideal, conservando los rechazos binary64.
Los pesos fijados mejoran prefijo/cola y empeoran ataque; se archiva toda
la comparación. Las cotas tangentes variables mantienen pendientes restos
no lineales, anclaje y recorrido completo. **1 mV global sigue abierto**.
El [corpus](BIESTABLE_DESCRIPTOR_PONDERADO_ENTRADAS.md) verifica 305
entradas y ocho versiones fallidas de tests; nueve regresiones nuevas pasan.
Próximo corte: conservar más estructura del operador y su propagación temporal.

El [descriptor continuo](BIESTABLE_DESCRIPTOR_CONTINUO_RESULTADOS.md)
separa 94 voltajes y 25 tasas de memoria. Ocho inversas de matrices levantadas
119×119 quedan certificadas; los mapas binary64 mantienen sus gates fallidos.
Se preserva y corrige un error de norma integrada del forzamiento con un
contraejemplo temporal. Las cotas válidas pertenecen sólo a operadores
congelados: las cotas sin pesos son enormes fuera de reset.
El [corpus](BIESTABLE_DESCRIPTOR_CONTINUO_ENTRADAS.md) reconstruye 295
entradas y siete versiones fallidas; once regresiones nuevas pasan.
Siguiente corte: pesos declarados, coeficientes ideales y variación temporal,
restos no lineales, anclaje y cobertura. **1 mV global sigue abierto**.

La [variante de tasas correlacionadas](BIESTABLE_TASAS_CORRELACIONADAS_RESULTADOS.md)
conserva cancelaciones entre C(v)*v′ y Qpol′: los intervalos completos
certificados bajo 10 pA pasan de 31 a 105. En reset N4, el límite puntual
baja de 2,666 nA a 6,419 pA sin cambiar estados ni sonido. Los 391 casos
con media sobre el umbral permanecen. El [corpus](BIESTABLE_TASAS_CORRELACIONADAS_ENTRADAS.md)
verifica 272 entradas; nueve regresiones nuevas pasan al primer intento.
Siguiente corte: propagación con memoria, restricciones, estabilidad,
anclaje y cobertura. El criterio global de 1 mV sigue abierto.

Los [recintos de Q(v) y magnitud del residual](BIESTABLE_MAGNITUD_RESIDUAL_RESULTADOS.md)
acotan balance constitutivo y magnitud acumulada en 496 intervalos y un
soporte mixto. La media cumple 10 pA en 105; el límite puntual certifica
31 intervalos completos. Reset conserva una cota amplia por pérdida de
correlación de tasas: próximo corte, estrecharla antes de propagar.
El [corpus](BIESTABLE_MAGNITUD_RESIDUAL_ENTRADAS.md) reconstruye 262 entradas
y seis versiones fallidas. Siete regresiones nuevas pasan, con el primer
intento numérico preservado. 1 mV global, física, audio y deadline siguen abiertos.

El [recinto racional de la integral](BIESTABLE_INTEGRAL_ACOTADA_RESULTADOS.md)
acota resto y redondeo sobre 496 intervalos y un soporte mixto; todos pasan
el contraste acotado de Gauss16. Confirma 105 medias polinómicas bajo 10 pA
y 391 por encima, sin inconclusas. Son cotas del interpolante, con cota
inferior de magnitud del residual; aún falta una cota superior y propagación.
El [corpus](BIESTABLE_INTEGRAL_ACOTADA_ENTRADAS.md) reconstruye 254 entradas
con cinco versiones fallidas anteriores. Siete regresiones nuevas pasan
al primer intento. Próximo corte: recinto de Q(v), magnitud superior y
estabilidad con cobertura completa. El criterio global de 1 mV sigue abierto.

Los [testigos de defecto de carga](BIESTABLE_DEFECTO_CARGA_RESULTADOS.md)
ya derivan kernels BDF2/BE y el término RC de publicación. El
[diagnóstico muestreado](BIESTABLE_DEFECTO_MUESTREADO_RESULTADOS.md)
separa 496 aproximaciones de diferenciación, reloj y coeficientes.
No conoce la tasa exacta de carga ni cierra 1 mV desde DC. Próximo bloque:
contrastar Q' reconstruido frente a ecuaciones continuas, separando error
de interpolación y de los estados finos antes de cambiar el controlador.

El [controlador E4G8 con Newton compensado](BIESTABLE_CONTROLADOR_COMPENSADO_RESULTADOS.md)
reproduce decisiones y reloj: 6.486 publicados, 12.968 provisionales y 49
rechazos conservados. Sus estados publicados son idénticos al ensayo de
reloj fijo. Cinco regresiones nuevas pasan; D4/E4 siguen fallando 1 mV.
Próximo gate: sensibilidad y memoria acumulada con sellos auditados.

La [trayectoria completa con reloj guardado](BIESTABLE_RELOJ_COMPLETO_COMPENSADO_RESULTADOS.md)
completa 6.486 intervalos desde un DC fresco idéntico: máximo nodal 6,21 pV
y memoria 8,77 pV, ambos bajo 10 nV. Cuatro regresiones nuevas pasan.
Siguiente gate: controlador adaptativo propio con sus rechazos y sombras;
el contraste temporal global de 1 mV sigue abierto.

La [variante del integrador con residual original](BIESTABLE_INTEGRADOR_COMPENSADO_RESULTADOS.md)
completa 64/64 intervalos con memoria propia: máximo nodal 2,34×10⁻¹⁵ V,
320 residuales y 64 Jacobianos idénticos a sus contrastes. Cuatro regresiones
pasan en el segundo intento; el fallo del adaptador queda conservado.
Próximo gate: trayectoria completa con reloj guardado, luego refinamiento.

La [auditoría de 64 intervalos guardados](BIESTABLE_VENTANAS_ESTATICAS_RESULTADOS.md)
pasa 64/64 mapas compensados; el ordinario pasa 54/64 y el mixto histórico
24/64. Los 256 solves pasan sus gates algebraicos y cuatro regresiones nuevas
preservan todos los fallos. Siguiente contraste: variante explícita del
integrador con el mismo residual, reloj e historial, sin admisión global.

Los [sellos binarios](BIESTABLE_SELLOS_BINARIOS_RESULTADOS.md) compensados
pasan 4/4 mapas de un intervalo frente a Decimal; el ordinario falla en
reset. Próximo corte: ventanas más largas y variante explícita del integrador
con residuo/historial/gates originales, conservando discrepancias y fallos.
Después repetir el contraste temporal completo, sin admisión de audio aún.

La [precisión estática](BIESTABLE_PRECISION_ESTATICA_RESULTADOS.md) localiza
sensibilidad de los mapas FD de audio: corrientes coinciden, pero ataque/reset
fallan frente a la nueva referencia analítica Decimal. Pasan cinco regresiones
y 48 inyecciones. Siguiente bloque: contraste previo de sellos binary64,
seguido de ventanas de integración; no se cambia todavía el integrador.

La [sensibilidad FD](BIESTABLE_RESULTADOS_SENSIBILIDAD_FD.md) completa 40
matrices y tres regresiones. Ninguno de los cinco pasos ni de las dos rutas
cierra reset; no hay convergencia monótona ni cambio de paso seleccionado.
Próximo corte: auditoría independiente del residuo estático de la cadena de
audio y de las columnas de memoria señaladas antes de propagar más tiempo.

La [propagación de memoria](BIESTABLE_PROPAGACION_DE_MEMORIA.md) añade mapas
94×25 y 25×25, 1024 intervalos hipotéticos y 32 contrastes centrales, todos
completos. Diez regresiones conservan publicaciones, solve refinado y
fallos originales. El suplemento racional resuelve cuatro matrices FD,
pero reset falla el gate de mapa (1,35×10⁻⁶ >10⁻⁸). Próximo bloque:
sensibilidad FD estática/dinámica declarada antes de ejecutar; luego más
direcciones y longitud temporal. No hay cota acumulada admitida.

El [contorno cargado de 94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) conserva 21 cargas y deja C2/reset como incógnitas reales. El barrido temporal acepta 370 pasos antes de rechazos cercanos a la conmutación. La [búsqueda ampliada](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) encuentra tres raíces, y la auditoría de cargas rápidas muestra una inestabilidad omitida en la intermedia. Próximo corte: leyes de carga de juntura y dominio de los puntos de operación; no hay selección física de raíz admitida.

1. Crear un solver fuera de tiempo real para VCO, mixer, filtro, contornos, VCA y salida; derivar frecuencia, transferencia, puntos DC y transitorios.
2. Ejecutar las escenas de [CAPTURAS.md](CAPTURAS.md) como estímulos simulados, con controles y unidades reproducibles.
3. Contrastar las cifras con el manual, boletines y límites de datasheets. Reservar escenas para detectar sobreajuste de parámetros libres.

**Salida:** oráculo **numérico del circuito seleccionado**, con incertidumbre declarada. El oráculo no demuestra equivalencia con un ejemplar antiguo.

## Fase C — Referencias audibles públicas

1. Catalogar las grabaciones de autores/propietarios de Model D vintage candidatas en [VALIDACION_SIN_HARDWARE.md](VALIDACION_SIN_HARDWARE.md).
2. Clasificar escenas por identidad del instrumento, visibilidad de controles, formato y procesado. Las demos sin ajustes reconstruibles sirven para escucha musical, no para ajuste de constantes.
3. Comparar formas/rasgos y documentar coincidencias y fallas por fuente independiente; mantener aparte las reediciones.

**Salida:** informe de plausibilidad sonora por escena, sin reclamar proximidad cuantitativa a una unidad no medida.

## Fase D — Motor portable y plugin

La ruta global Q26/Q28→ladder→VCAs→J7 tiene Jacobiano analítico, optimizaciones contrastadas, [752384 muestras de estrés largo](ESTRES_LARGO_GLOBAL_66.md), [192 pasos independientes en ventanas de switches/tramos tardíos](VENTANAS_INDEPENDIENTES_ESTRES_GLOBAL.md), [refinamiento a 48/96/192 kHz](REFINAMIENTO_TEMPORAL_GLOBAL_66.md) y [observaciones de stack Win64](STACK_GLOBAL_66_WIN64.md). La media local aún excede el plazo de audio. El siguiente corte numérico debe completar extremos de controles y verificar recursos del host; VCO, mezclador cargado y contornos siguen pendientes para la voz completa.

1. Implementar contrato/estado, control, osciladores, mezcla, filtro, contornos/VCA, salida y adaptador RackForge.
2. Comparar cada bloque con el solver, incluyendo límites de controles y escenas reservadas.
3. Optimizar WebAssembly/tiempo real sólo después de medir errores; conservar ruta de referencia de precisión.

**Salida:** pruebas de circuito y audio, matriz por bloque, perfil de CPU y plugin `.rfplugin` sin material ajeno redistribuido.

## Fase E — Uso en vivo

El [puerto cargado C2/reset](PUERTO_CONTORNO_CADENA_71.md) añade admisión `2×2` y gradientes `71×2` desde raíces completas, veinte DC y dieciséis temporales. Mantiene la memoria entrante durante todos los ensayos y devuelve un candidato provisional. Próximo corte: estudiar estabilidad y dinámica del biestable incorporando su carga real, sin seleccionar una raíz por conveniencia.

El [cierre de 71 nodos](SEGUIDOR_VCA_CADENA_71.md) une Q3/Q2 con R59/base Q18 y la cadena hasta J7: veinte destinos DC, 256 pasos independientes, corrientes de C2/reset, memoria atómica y heap cero. Preparación y continuación son explícitas; se conserva un rechazo de semilla DC apagada. El costo todavía excede el plazo. El próximo corte obtiene las tangentes conjuntas y resuelve la ambigüedad del biestable antes de reintegrar el capacitor C2.

El [apagado con rampas de laboratorio](APAGADO_VCA_GLOBAL_66.md) localizó 20/96 sondas >1 µV. El [criterio temporal de voltaje](CRITERIO_VOLTAJE_TRANSITORIO_GLOBAL.md) las corrige y pasa el estrés largo. La [reutilización de direcciones](DIRECCION_NEWTON_REUTILIZADA.md) reduce el costo posterior sin cambiar bits. [R21 exacto](R21_EXTREMOS_EXACTOS.md) pasa integración independiente y recursos con ambos topes. La [continuación DC VCA](DC_VCA_CONTINUACION.md) resuelve 18 arranques de fuentes en cero mediante una API de preparación. Próximos cortes: resolver saltos conservando los historiales, recursos/host y circuito real de contorno; los saltos abruptos siguen agotando Newton.

El [barrido global de extremos](EXTREMOS_CONTROLES_GLOBAL_66.md) encontró dependencias de semilla DC con cutoff máximo, fallo al llevar Q21 a cero y extremos R20/R21 rechazados. [R20 exacto](R20_EXTREMOS_EXACTOS.md) y [R21 exacto global](R21_EXTREMOS_EXACTOS.md) ya pasan; la [semilla DC completa](DC_GLOBAL_SEMILLA_COMPLETA.md) resuelve cutoff máximo. La [continuación temporal VCA](SALTOS_VCA_HISTORIAL_FIJO.md) rescata saltos con historial fijo y el [perfil de ocho etapas](ETAPAS_VCA_Y_REPRODUCIBILIDAD.md) reduce 38,46 % el costo de esas escenas. Con estado temporal común se reproduce el render entre workers; permanece la sensibilidad del arranque. Próximos cortes: costo normal/peores muestras, contorno físico, dependencia de semillas y recursos del host; conservar los informes fallidos.

Probar Note On/Off, retrigger, legato, glide, ruedas, cambios de preset y recuperación de estado. Mantener la voz mono y describir las comodidades de RackForge como extensiones. Validar transiciones sin discontinuidades accidentales ni asignaciones en el hilo de audio.

## Contorno de volumen: avance y gate pendiente

El [grafo eléctrico y oráculo de placa 2](CONTORNO_VOLUMEN_CIRCUITO.md) reconstruye diez BJTs, gatillo, tres memorias capacitivas, panel y decay final. El biestable presenta dos raíces diferentes para el mismo paso; quedan registradas sin selección. El [puerto nativo Q3/Q2/CR6](SEGUIDOR_VOLUMEN_NATIVO.md) reproduce 60 casos y entrega tres corrientes/tangentes con heap cero. Siguiente cierre: R59/base Q18 real; después estabilidad de conmutación y cargas compartidas antes de unir contorno completo/VCA o afirmar Note On/Off físico. Los intervalos físicos nuevos no se recortan al `0..2 V` del laboratorio anterior.

## Primer corte de implementación

El [balance integrado con variante Gauss](BIESTABLE_BALANCE_GAUSS_RESULTADOS.md)
completa 496 intervalos y el soporte mixto, conservando los fallos Simpson.
Componer Q(v) no elimina el residual: 391 medias quedan sobre 10 pA.
Próximo corte: cota del resto de cuadratura y magnitud/propagación del
residual antes de convertir el balance firmado en error global desde DC.
Los intervalos seleccionados no son contiguos; no se suman como trayectoria.

La [reconstrucción interior de cargas](BIESTABLE_CARGA_INTERIOR_RESULTADOS.md)
certifica restricciones lineales sobre los 496 intervalos reconstruidos y
consulta 1.488 puntos. KCL conserva 1.173 incumplimientos. La cubierta del
knee localiza un cruce en el soporte antiguo, fuera del intervalo actual.
Próximo corte: reconstrucción constitutiva por piezas y residual integrado,
con tratamiento declarado del soporte mixto, antes de acumulación desde DC.
Los certificados del polinomio no se promueven a cotas de la trayectoria física.

El [contraste continuo de cargas](BIESTABLE_CARGA_CONTINUA_RESULTADOS.md)
completa 496 diagnósticos sin solves nuevos. Los residuales BDF finos pasan
10 pA; los cúbicos continuos conservan 390 incumplimientos. El interpolante
cuadrático reproduce esencialmente BDF2 y no es un contraste independiente.
El soporte de reset que cruza el knee se conserva. Próximo corte: residual
entre muestras, restricciones de carga y tratamiento declarado de cambios
de pieza; después error inicial y propagación antes de otra política global.

El [contraste E4G8 desde DC](BIESTABLE_CRECIMIENTO_DESDE_DC.md) ya completa 6486 intervalos y 1724 consultas. Evita 620 rechazos pero suma 564 ensayos aceptados: 56 intentos menos, con más evaluaciones modales aceptadas. Frente a D4 conserva 8,234 mV; no se promueve el umbral 0,125 ni se cierra refinamiento global. La [curvatura de circuito](BIESTABLE_CURVATURA_RESULTADOS.md) y el [forzamiento relativo a ventanas refinadas](BIESTABLE_FORZAMIENTO_RESULTADOS.md) ya propagan memorias propias, residual y publicación. El segundo se extrae de referencias conocidas y no es un estimador independiente. Próximo bloque: derivar el error de diferenciación de cargas sobre historiales reales y contrastarlo en soluciones conocidas, apoyado por los [contraejemplos exactos](BIESTABLE_DEFECTO_Y_MEMORIA.md), antes de otra política de refinamiento o promoción nativa.

Las [cuatro ventanas de crecimiento](BIESTABLE_VENTANAS_DE_CRECIMIENTO.md) completan ocho continuaciones desde memoria E4 común y verifican 335 intervalos. El umbral 0,125 evita rechazos en estas ventanas y reduce los intentos de cola, con más intervalos aceptados. Su estudio desde DC está en el corte E4G8; estos resultados condicionados no sustituyen los 7,81 mV fallidos del barrido global.

El [barrido de doble paso desde DC](BIESTABLE_BARRIDO_DOBLE_PASO.md) completa D4/E4 con 9446 intervalos y 866 consultas válidas. El máximo consultado de 7,81 mV sigue fallando el gate de 1 mV; el prefijo muestreado pasa con 4,615 µV. Próximo bloque: acumulación temporal y crecimiento con memoria publicada, apoyados por el contraejemplo exacto del umbral 0,25. Cada controlador nuevo tendrá política e informe propios; no promover aún el contorno al motor nativo.

El [prototipo de doble paso BDF2 v4](BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md) pasa doce sondas y el cúbico exacto, con FD, historial conservado y publicación del candidato completo. Su protocolo ya se ejecutó en D4/E4. No usar un divisor Richardson 1/3: los historiales compartidos cambian ese patrón local.

Los [máximos consultados con memoria común](BIESTABLE_MAXIMOS_CON_HISTORIAL_COMUN.md) confirman 26,79 mV tras revisar los 94 máximos por nodo y la rejilla retenida. El siguiente gate mantiene el control del máximo completo y exige otro estimador temporal, sin usar el punto de 2,12 mV como si fuese el peor de la región.

El [historial común B3/C3](BIESTABLE_HISTORIAL_COMUN.md) conserva 1992 intervalos nuevos y 4019 C3 heredados. El contraste condicional de 28,95 mV también falla. Próximo corte: consultas de todos los máximos por nodo y de la rejilla retenida, seguidas de un estimador BDF2/BDF2 con verificación de memoria y dominio antes de otro barrido desde DC.

El [observador dentro del dominio](BIESTABLE_DOMINIO_DE_OBSERVACION.md) completa las 772 consultas con 284 intervalos provisionales nuevos. El prefijo muestreado pasa 1 mV (59,0 µV máximos), sin cota continua, y el pico completo falla. Próximo bloque: continuaciones diagnósticas desde un historial doble común antes de la regeneración, para separar diferencias del prefijo y de la región rápida conservando el contraste original desde DC.

La [observación entre muestras](BIESTABLE_OBSERVACION_ENTRE_MUESTRAS.md) confirma el pico B3/C3 y localiza 139 consultas fuera del mínimo temporal de 1 ps. Próximo corte: conservar el instante pedido mediante anclaje anterior y dos intervalos provisionales dentro del dominio; verificar memoria intermedia y cobertura sin reemplazar el informe fallido.

La [tercera malla C3](BIESTABLE_TERCERA_MALLA_BDF2.md) añade 4364 intervalos y reduce el máximo B3/C3 a 0,126368 V, todavía por encima de 1 mV. Próximo corte: observaciones conservativas en rejilla fija y puntos medios, y control del error acumulado antes de la regeneración. Cobertura y diferencia final no admiten la trayectoria completa.

La [consulta temporal conservativa](BIESTABLE_PREFIJO_Y_CONSULTA_TEMPORAL.md) localiza una contribución de interpolación en el trigger y confirma que el pico de 0,563 V persiste en solves al mismo instante. Próximo bloque: BDF2 más estricto y observación entre muestras, sin relajar KCL ni convertir consultas provisionales en una trayectoria admitida.

El [segundo integrador BDF2](BIESTABLE_BDF2_CARGA.md) verifica coeficientes, dos memorias aceptadas y conservación en C10/junturas. Su [barrido A3/B3](BIESTABLE_BARRIDO_BDF2.md) completa 0..3 ms con 3236 intervalos; el máximo de 0,563 V todavía falla el gate de 1 mV. Próximo corte: prefijo de trigger/C2, diferencias de interpolación y refinamiento adicional, conservando los fallos de Euler.

Los [tiempos observados](BIESTABLE_TIEMPOS_DE_TRANSICION.md) separan la subida ATTACK_OUT de la caída final de Q25. Siguiente gate: error acumulado antes de ambas regiones con refinamiento adicional y otra integración, sin retimar las trazas para aprobar el contraste original.

El [corte de incrementos compensados](BIESTABLE_INCREMENTOS_COMPENSADOS.md) ya cierra el intervalo rechazado con ambos Jacobianos y conserva sus 21 memorias durante 32 pasos posteriores. El [barrido A2/B2](BIESTABLE_BARRIDO_COMPENSADO.md) completa 0..3 ms y verifica 4152 medios intervalos; falla el gate temporal de 1 mV con 5,147 V máximos. Próximo bloque: medir por separado ATTACK_OUT/Q25, sensibilidad acumulada y otra integración. Se conserva el barrido v1 fallido.

El trabajo de conmutación actual tiene un [inventario de doce sesgos y primitivas de carga verificadas](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md), un [BJT intrínseco conservativo contrastado contra ngspice](BJT_INTRINSECO_CARGA_CONSERVATIVA.md), [transitorios cargados con historial y refinamiento](BJT_CARGADO_TRANSITORIOS.md) y una [sonda Q25/Q15 no lineal de 94 nodos](BIESTABLE_CARGA_NO_LINEAL.md). La sonda conserva 25 memorias escalares y reproduce tres soluciones a 1 ms. El [primer barrido adaptativo desde DC](BIESTABLE_TRAYECTORIA_ADAPTATIVA.md) publica 2982 intervalos; la política estricta se detiene y ambas trazas difieren hasta 5,006 V. El [diagnóstico del rechazo](BIESTABLE_RECHAZO_Y_ORIGEN_CARGA.md) reproduce un límite representable en C2 y demuestra sensibilidad del estimador al cero convencional de Q. El [corte de incrementos compensados](BIESTABLE_INCREMENTOS_COMPENSADOS.md) ya verifica esa corrección; el siguiente gate es repetir el refinamiento completo con la métrica v2. La carga condicionada no identifica una pieza vintage ni admite una transición Note On/Off. Las [lecciones para RACE](LECCIONES_RACE_CONMUTACION.md) mantienen ese orden de gates.

Empezar por **VCO 1 aislado → mezclador → filtro abierto → VCA/salida**, con un grafo de circuito y un solver simple que admita barridos de notas y niveles. Luego filtro autooscilante y contornos. Cada etapa debe poder avanzar sin una captura privada.

**Corte 0 en curso:** [VCO 1 CA3046](VCO1_CA3046.md) ya tiene subgrafo funcional, resistencias de IC1 cotejadas con tabla 7-5, pinout de IC2, tramo de netlist de C1/bases/IC3 con alimentaciones, R11/R37, [inventario de conexiones de la referencia −4 V](REFERENCIA_MENOS4V.md), ramal resistivo de Schmitt/Q10, [topología parcial de Q7/Q8/Q9/Q4/Q3](VCO1_AMPLIFICADOR_FET.md), [Q2/Q1 y 21B](VCO1_TRIANGULO.md), [Q11/Q12 y 20B](VCO1_PULSO.md) y [cargas internas corregidas de la sierra 9B](VCO1_SALIDA_SIERRA.md). Hay referencias incrementales de voltaje, [razón exponencial ideal de corriente](VCO1_CONVERTIDOR_IDEAL.md), [explorador de carga DC ideal](VCO1_CARGA_DC_IDEAL.md), [polarización condicional de Q5](../tools/vco1_schmitt_bias_reference.py), [puerta FET condicionada](../tools/vco1_fet_gate_reference.py), [pesos pasivos del pulso](../tools/vco1_pulse_passive_reference.py), [selector SW6, puente 9B–21B y dos puertos R6/R45](VCO1_CABLEADO_PANEL.md) y referencia de eventos para C1. La relación de frecuencia es **normalizada y condicional**; la etiqueta −4 V y el divisor sin carga dan corrientes de Qb distintas y ninguno fija la corriente real. La [KCL del bus de mezcla](MEZCLADOR_PANEL.md) ya incorpora las cinco rutas ON con cargas de potenciómetro condicionadas. El siguiente corte es encontrar parámetros primarios para Qc y cerrar corrientes de carga de −4 V, además de resolver el conflicto 10/100 pF de C4, el comportamiento de los FET/BJT, R78 dinámica, la solución acoplada de 9B/21B/20B/22B, la entrada real del bus de mezcla y el mapa de posiciones del panel. Sólo entonces se podrá producir la sierra cargada para el mixer.
