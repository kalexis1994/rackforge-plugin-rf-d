# Lecciones RF-D para RACE: conmutación y memoria de carga

El [barrido de doble paso desde DC](BIESTABLE_BARRIDO_DOBLE_PASO.md) completa 9446 intervalos y 866 consultas, pero conserva 7,81 mV de máximo. Cambiar el estimador requiere repetir cobertura, publicación y máximo con políticas declaradas. El mínimo pertenece a cada intervalo real de las rutas provisionales. La heurística de crecimiento también necesita hipótesis explícitas: un cúbico con memoria realmente publicada pasa de razón 0,2 a 1,725 al duplicar h. Preservar el intento fallido del adaptador tupla/lista y contrastar JSON canónico permite corregir la validación sin cambiar datos o gates.

El [doble paso BDF2](BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md) propone derivar el estimador sobre el historial realmente compartido. Un cúbico exacto da `Efine/(Efull−Efine)=13/19` con h/k=1, no 1/3; ese valor tampoco calibra el DAE no lineal. Declarar qué candidato se publica y cómo limita el siguiente crecimiento evita aceptar un macro cuya comparación provisional esté fuera del dominio del integrador.

La [auditoría de máximos por nodo](BIESTABLE_MAXIMOS_CON_HISTORIAL_COMUN.md) propone conservar una rejilla fija y ampliar la consulta a todos los máximos, en vez de concluir desde el máximo interpolado global. Ese punto baja a 2,12 mV, pero otro nodo/instante sigue en 26,79 mV. Ambos son diagnósticos finitos; ninguno localiza por sí solo el máximo continuo.

El [historial común](BIESTABLE_HISTORIAL_COMUN.md) propone separar un contraste desde DC de otro condicionado a la misma memoria doble, intervalo previo y primera propuesta. Heredar un tramo verificado requiere volver a comprobar linaje/carga y distinguirlo de integración nueva. Los máximos de esas diferencias no se suman linealmente y la condición común no valida retroactivamente el prefijo ni el circuito físico.

El [observador dentro del dominio](BIESTABLE_DOMINIO_DE_OBSERVACION.md) propone conservar el destino temporal cuando el resto respecto del último estado es impropio: usar un anclaje anterior y guardar los dos intervalos provisionales, con KCL y memoria intermedia verificadas. Completa 772 consultas sin mover el reloj y pasa sólo el gate del prefijo muestreado; el máximo global permanece fallido. Corregir la observación no demuestra convergencia de la trayectoria.

La [rejilla de consultas](BIESTABLE_OBSERVACION_ENTRE_MUESTRAS.md) propone aplicar el dominio temporal también a la observación: dos tiempos casi coincidentes en binario pueden pedir un paso mucho menor que el permitido al integrador. Conservar cada fallo y la memoria entrante; no reemplazarlo por interpolación ni redondear el reloj sin cuantificarlo. El siguiente observador debe usar otro anclaje y conservar sus estados provisionales.

La [tercera malla BDF2](BIESTABLE_TERCERA_MALLA_BDF2.md) propone conservar una secuencia de políticas declaradas y el gate original: 4364 intervalos nuevos reducen la discrepancia máxima a 0,126 V, pero no pasan 1 mV. Un cociente entre dos discrepancias no demuestra orden global ni error absoluto. Los hashes de fuente también requieren fijar la convención de bytes del checkout; Python LF debe sobrevivir a `core.autocrlf=true` sin alterar fuentes históricas identificadas con otra convención.

La [consulta temporal conservativa](BIESTABLE_PREFIJO_Y_CONSULTA_TEMPORAL.md) propone auditar la interpolación usada para comparar mallas: una separación de 3,75 mV se reduce a 39,4 µV al resolver el mismo instante, mientras un pico distinto permanece en 0,563 V. Conservar los historiales entrantes, marcar las consultas como provisionales y repetir FD permite diagnosticar el error de observación sin reescribir la evidencia fallida. Un punto consultado no valida el resto de la trayectoria.

El [barrido BDF2](BIESTABLE_BARRIDO_BDF2.md) propone distinguir error final y máximo de trayectoria: 0,141 mV al final no compensa 0,563 V durante la transición. Una mejor coincidencia entre políticas del segundo integrador tampoco identifica cuál se acerca a la solución exacta; mantener el contraste entre métodos y el alcance del solver compartido.

El [corte BDF2](BIESTABLE_BDF2_CARGA.md) propone validar un integrador multistep sobre carga antes de repetir la voz completa: derivar coeficientes con interpolación, conservar ambos estados ante rechazo, distinguir memoria virtual de carga física y verificar publicación directamente desde los historiales reales. Compartir un solver espacial con otro integrador no crea un oráculo espacial independiente.

Los [tiempos observados](BIESTABLE_TIEMPOS_DE_TRANSICION.md) proponen separar desfase y forma sin reemplazar el gate temporal original. Registrar todos los cruces, sus intervalos muestreados y la dirección evita seleccionar por conveniencia un evento. Las alineaciones diagnósticas conservan su propio alcance y nunca retiman la evidencia publicada para aprobarla.

El [barrido compensado](BIESTABLE_BARRIDO_COMPENSADO.md) completa ambas trazas y conserva 4152 intervalos, pero aún difiere 5,147 V. Resolver un límite de representación no demuestra convergencia de la dinámica. Registrar por separado cobertura, conservación publicada y discrepancia temporal evita promover un solve local como garantía de la transición completa.

La [corrección por incrementos](BIESTABLE_INCREMENTOS_COMPENSADOS.md) propone un gate de publicación: cuando el solve exige variaciones menores que un ULP, verificar que sobreviven en las memorias serializadas y satisfacen las ecuaciones de rama en el paso siguiente. Un residuo provisional pequeño no basta. La aritmética de mayor precisión debe contrastar la carga guardada, incluyendo ramas con resistencia en serie.

Registro transferible al estándar, basado en el contorno cargado de 94 nodos. No convierte las hipótesis RF-D en parámetros reutilizables de otros sintetizadores.

| Regla propuesta | Evidencia concreta RF-D | Gate para el próximo circuito |
| --- | --- | --- |
| Cerrar la carga del bloque vecino antes de validar un control | C2/reset dejan de ser fuentes en el [cierre de 94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) | KCL conjunta, mismos historiales y Jacobiano independiente de la frontera |
| Declarar el alcance de una enumeración de raíces | Cinco semillas vieron dos raíces; [102 interpolaciones](BIESTABLE_TRES_RAICES_Y_CARGA_RAPIDA.md) encontraron una tercera | Conservar semillas, raíces y rechazos; marcar búsqueda no exhaustiva |
| Newton no decide la rama física | Tres soluciones satisfacen el mismo paso y sus mismas cargas entrantes | Selección derivada de dinámica con memoria; nunca por número de iteraciones |
| Auditar modos que una eliminación algebraica omite | Cuatro cargas hipotéticas revelan un modo creciente intermedio ausente en el descriptor de 21 cargas | Comparar rango dinámico y modos de G+λC; declarar las cargas no identificadas |
| Separar estabilidad continua y amortiguamiento del integrador | Euler a 1 ms amortigua el modo local creciente de la familia diagnóstica | Registrar λ y amplificación discreta; refinar dt respecto de los modos pertinentes |
| Usar el dominio completo de una medida | Cob=2..10 pF a 10 V inversos/1 MHz no cubre ninguna de las doce junturas auditadas | Fuente, sesgo, frecuencia, temperatura, proceso y lote; evitar convertir un rango de tabla en C(V) |
| El historial de una carga no lineal pertenece a Q | [Contraejemplo ΔQ frente a C(V)·ΔV](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) | Cuadratura de C, dQ/dv, KCL terminal, Jacobiano FD e historial intacto ante rechazo |
| Un modelo elemental no completa un dispositivo multipuerto | Primitivas de depleción/difusión sin partición BJT ni alta inyección | Derivar cargas terminales, suma de corrientes, transporte y régimen de saturación |
| Publicar alcance, condiciones y desconocidos junto al resultado | Informes con fuentes/hash, ambiente, dt, selected=null y audio_admitted=false | Evidencia reproducible antes de promover a nativo o anunciar fidelidad |

Estas reglas son candidatas documentadas para el repositorio RACE. Su implementación matemática se verifica en RF-D; los parámetros físicos pendientes y el rendimiento del motor siguen teniendo gates propios.

La [comparación de fabricantes 2N3392](FABRICACION_3392_Y_DATOS_DINAMICOS.md) añade una regla documental: conservar la columna típico/mínimo/máximo, el encapsulado, la revisión y las ambigüedades impresas. GE87 y Central/Fairchild sitúan 2 pF en columnas distintas. Una remisión a una familia de proceso posterior no identifica el lote de un sintetizador histórico.

El [BJT cargado](BJT_CARGADO_TRANSITORIOS.md) añade dos gates operativos: comprobar que un oráculo cubre todo el intervalo solicitado aunque devuelva exit code cero, y validar el significado de sus columnas iniciales antes de convertirlas en memoria física. Las cargas t=0 no calculadas por un export permanecen marcadas; no se sustituyen silenciosamente. Se refinan ambos integradores conservando los límites de error originales.

La [sonda no lineal Q25/Q15](BIESTABLE_CARGA_NO_LINEAL.md) mantiene las tres raíces aun después de añadir cargas conservativas. La masa se contrasta en pF antes de sumarla a capacitores de µF, y la reproducción FD parte de otra semilla con el mismo historial. Una ley de carga verificada necesita seguimiento temporal que resuelva sus modos; no basta una raíz implícita a paso grueso. Preparar cargas nuevas desde un prefijo anterior es una condición inicial declarada, no una validación retroactiva de ese prefijo.

El [barrido adaptativo desde DC](BIESTABLE_TRAYECTORIA_ADAPTATIVA.md) separa aceptación local, cobertura final y refinamiento: 2982 intervalos pasan sus solves, pero la política estricta se detiene y el intervalo común difiere 5,006 V. Registrar el estado previo de cada rechazo y comprobar los pasos guardados permite conservar ese fallo. Un estimador propio por duplicación de paso y un descriptor congelado no son un oráculo independiente ni una prueba de estabilidad de toda la trayectoria.

El [diagnóstico de C2 y del origen de Q](BIESTABLE_RECHAZO_Y_ORIGEN_CARGA.md) añade dos verificaciones: contrastar el residuo con los vecinos representables cuando C/dt crece, y probar que el control de error conserva su significado al cambiar referencias convencionales del estado. Una corrección menor que un ULP no equivale a cerrar KCL. Una métrica nueva debe declarar por qué reemplaza la anterior; la traza rechazada permanece como evidencia y no se convierte retroactivamente en un éxito.
