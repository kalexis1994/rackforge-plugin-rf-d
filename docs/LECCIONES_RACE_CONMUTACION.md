# Lecciones RF-D para RACE: conmutación y memoria de carga

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
