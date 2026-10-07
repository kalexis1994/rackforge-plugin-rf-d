# VCO1 nativo: contrato previo de implementación

2026-10-07. Próximo bloque del motor portable. Este protocolo no registra
mediciones nuevas ni declara un oscilador nativo ya terminado.

## Circuito que se conservará

Revisión CA3046 de SVC-9 Fig. 9-3, PDF p. 5; panel Fig. 9-17, p. 19;
función SVC-204D §2.16, pp. 14–15. La conectividad vigente está en
[el grafo](../evidence/vco1_ramp_graph.json), con los retornos corregidos
en [la auditoría](VCO1_AUDITORIA_RETORNOS.md). Componentes de control y
selector: [CV/trims](../evidence/vco1_ca3046_parts.json) y
[panel](../evidence/vco1_panel_pulse_width.json).

Conservar simultáneamente convertidor exponencial Qa/Qb/Qc e IC1/IC3,
R42/R78, integración C1/C2, amplificador FET, Schmitt/reset Q5/Q6/Q10,
formadores de sierra/triángulo/pulso y referencia compartida −4 V con
R166/R174/C14. La frecuencia, los umbrales y los resets serán resultados
del circuito. Los CV, rieles y carga de las secciones ausentes de −4 V
continúan como fronteras explícitas.

Los valores, unidades e hipótesis de dispositivo se conservan de
[las tarjetas](../evidence/vco1_laboratory_devices.json) y
[su derivación](VCO1_ORACULO_CIRCUITO.md). Son hipótesis de laboratorio;
Q5/Q6 siguen con identidad física pendiente. C4=10 pF y 100 pF serán
escenarios distintos. IS/betas/tiempos/capacidades de BJT y parámetros
JFET tendrán cargas y derivadas coherentes, además de corriente DC.

IC1/IC3 requieren una implementación auditada de dinámica, alimentación,
límites y cargas del macromodelo privado identificado por hash. Un cambio
de modelo operativo abrirá otro protocolo y otro contraste. Las memorias
de sus ramas reactivas internas también forman parte del estado; un polo
interno del macromodelo no se atribuye a una bobina física del Moog.

## Frontera con mezclador y salida

El [puerto cargado](MEZCLADOR_PUERTO_CARGADO_RESULTADOS.md) devuelve cinco
corrientes, Jacobiano 5×5 y candidato de la cadena ON/C27→filtro/VCA→J7.
El VCO debe resolver su voltaje y la corriente entrante del puerto juntos.
Usar la convención de corriente entrante a la cadena; el mismo valor sale
del nodo del generador. Evitar duplicar las ramas R6/R45 del panel que ya
están dentro del puerto: los formadores terminan en el nodo de fuente
seleccionado, y el panel carga ese nodo desde el puerto.

Primer acoplamiento: OSC1 presente, otras fuentes ausentes y nivel
eléctrico α=0.5. Los potenciómetros siguen como fracciones de resistencia,
sin atribuirles taper o posición física. R61=200 Ω y 200 kΩ se conservan
separados; no se los ajusta para lograr convergencia.

Hay una restricción concreta que cerrar antes de este acoplamiento:
`mixer_chain66` admite actualmente pasos de **0.5 µs a 1 ms**, mientras que
el oráculo VCO usa refinamientos de **500/250/125 ns**. Primero construir y
verificar un stamp directo del puerto C27 en la fila de base, o demostrar
con referencias independientes una extensión explícita del dominio. Un
rechazo de dominio no se resolverá reduciendo el paso sólo del oscilador:
las cargas conjuntas necesitan un reloj común o una política multirate
con error propio medido. La política actual permanece vigente hasta eso.

La ruta directa se puede limitar a la fila BASE_Q29 (índice 6):
`r6=(x6−x4)/470 Ω + IB_Q29(x6,x8,x5) + I_BASE_puerto`.
Su Jacobiano conserva los términos de R54 y Q29 y añade la tangente
BASE→BASE del puerto. Para Q29, con las leyes condicionadas del núcleo,
`gf=IS·exp((x6−x5)/VT)/VT` y `gr=IS·exp((x6−x8)/VT)/VT`; columnas
4/5/6/8: `−1/470`, `−gf/BF`, `1/470+gf/BF+gr/BR+Y_BASE_BASE`,
`−gr/BR`, en siemens. Las otras filas quedan como en el núcleo de 66 nodos.
Esto es una derivación prospectiva de SVC-9 Fig. 9-11, p. 13, cotejada con
`circuit66.rs` y `filter_ladder_ebers_moll_dc_reference.py`: R54, Q29 y C27
son las únicas ramas de esa fila. La primera anotación de designador R24
en `c5cf3c1` era incorrecta; se conserva en esa revisión y se corrige aquí
sin modificar ecuaciones o circuito. Requiere
oráculo sin reducción, Jacobiano y estados completos a 500/250/125 ns;
todavía no extiende el dominio admitido del adaptador.

## Estado y solve

La estructura de estado contendrá voltajes nodales, cargas de todas las
junturas y capacitores, estados internos del 741 y memoria de la cadena.
Inventario, orden de incógnitas y dimensiones se fijarán por una tabla de
terminales antes de compilar el primer kernel. No habrá asignación de heap,
I/O, locks ni logs dentro del procesamiento.

Primer integrador portable: Euler implícito con historia fija durante
cada Newton y búsqueda de paso. El resultado será provisional hasta que
VCO y cadena cumplan sus ecuaciones. Cualquier fallo devuelve diagnóstico
y conserva **todo** el estado anterior, incluido el estado de la cadena.
Se evaluarán estabilidad y error temporal antes de optimizar.

La inicialización resolverá DC con las condiciones de arranque del
oráculo, incluida C1=0 V. Las cargas se inicializarán desde sus terminales;
no se copiará una trayectoria SPICE como mecanismo de arranque. Las
semillas nodales serán ayudas del solver identificadas como tales.

## Verificaciones y gates antes de medir

1. **Dispositivos:** currents y cargas de BJT/JFET, conservación terminal y
   Jacobianos contra ecuaciones independientes y diferencias finitas,
   incluyendo saturación, inversión de terminales y regiones de juntura.
   Congelar dominios y gates de cada tarjeta antes de ese banco.
2. **Stamp completo:** contrastar cada fila contra la netlist expandida,
   incluidos nodos/estados internos del 741, contactos exactos, retornos y
   cargas. Validar todas las columnas del Jacobiano, con historia fija.
3. **Cierre de un paso:** referencia nodal independiente sin eliminación
   del panel/bus. Como en la cadena: KCL <1e−11 A, restricciones ideales
   <1e−11 V y corrección completa <1e−8 V. Preservar intentos rechazados.
4. **Trayectoria autónoma:** 30 ms con observación tras 15 ms; arranque,
   resets, frecuencia, extremos/offset de C1 y las tres ondas, referencia
   −4 V, corrientes Qa/Q10 y corriente de fuente al panel.
5. **Refinamiento:** usar los bancos existentes de Gear2/Trap2 como
   referencia externa al kernel y añadir un oráculo Euler con la misma
   discretización para localizar discrepancias. Frecuencia ≤1 cent y
   extremos ≤5 mV entre las dos resoluciones más finas; dispersión relativa
   de periodo ≤1e−5 y balance C1 ≤0.002, con la definición histórica. El
   diagnóstico por fase no reemplaza diferencias al mismo reloj.
6. **Reservados:** R11=521.31266 Ω/R8=0.26134047, CV −3.1/−2.1/−1.1/−0.1 V.
   Reutilizar los resultados de [calibración](VCO1_RESULTADOS_CIRCUITO.md)
   sin ajustar el kernel por nota. Extremos ≤0.1 cent e intermedios ≤5 cents
   siguen siendo objetivos condicionados de laboratorio.
7. **Integración:** volver a contrastar frecuencia, formas, carga y J7 con
   un oráculo acoplado independiente. La referencia antigua de mixer fijo
   sirve al VCO aislado; el puerto activo cambia la frontera y necesita
   su propia referencia. Su corriente/tangente debe corresponder al mismo
   estado aceptado, sin confirmar pasos intermedios.

Cada banco tendrá fuentes/modelos/protocolo antes y después, comando,
logs, datos completos y recibo exclusivo. La cobertura parcial no contará
como escena completa. Un gate incumplido produce rechazo; su causa se
investiga antes de modificar física, tolerancias o presupuesto.

## Promoción y escucha

El resultado inicial será VCO1 condicionado con cadena y controles
impuestos. Contorno autónomo, otros VCO, ruido y modulación siguen abiertos.
La escucha futura declarará duración realmente simulada, nodo/carga,
escala V→audio y resampling/antialias. El presupuesto RT se medirá después
de cerrar el error numérico. Ninguno de estos pasos acredita identificación
física de una unidad vintage sin mediciones de ese instrumento.
