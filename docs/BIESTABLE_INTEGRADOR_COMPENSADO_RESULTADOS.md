# Continuaciones con residual original y J66 compensado

El [protocolo previo](BIESTABLE_INTEGRADOR_COMPENSADO_PROTOCOLO.md) y la
variante se fijaron en `e21c69a`; se ejecutaron tras archivar los
[64 mapas estáticos](BIESTABLE_VENTANAS_ESTATICAS_RESULTADOS.md).
`increment-pair/compensated-static-J66/v1` hereda Newton, búsqueda lineal,
BDF2 variable, historial y publicación originales. Sólo sustituye J66;
las ecuaciones de corriente originales permanecen en uso. Es laboratorio.

## Preflight y continuación

Los **320 pares de residuales** coinciden bit a bit: candidato guardado y
cuatro desplazamientos ±1 µV en nodos 27/66 por cada uno de 64 intervalos.
Los **64 Jacobianos** coinciden bit a bit con la ruta compensada auditada.
Las cuatro rutas FD explícitas también coinciden. Es cobertura finita de
esta implementación, no prueba universal de identidad del residual.

Cada ventana restaura el mismo historial doble inicial y avanza los 16
intervalos originales con sus estados propios, sin reemplazarlos por los
de referencia. Se completan **64/64 intentos**, sin rechazo, retimado,
controlador adaptativo o reset. Todos pasan comparación de nodos/memorias
<10 nV y publicación directa desde historiales reales.

| Ventana | Máximo nodal (V) | Máximo de memoria en coordenada V | Iteraciones candidato / original |
| --- | --- | --- | --- |
| Prefix | 8,37676×10⁻¹⁶ | 3,85334×10⁻²⁵ | 32 / 32 |
| Attack | 8,12251×10⁻¹⁶ | 6,00180×10⁻²⁶ | 45 / 45 |
| Reset | 8,37036×10⁻¹⁶ | 1,37906×10⁻²⁶ | 32 / 32 |
| Tail | 2,34020×10⁻¹⁵ | 5,95323×10⁻²⁵ | 32 / 32 |

Las memorias son 21 voltajes compensados y cuatro cargas con escala
**10⁻¹² C/V exclusivamente numérica**. La diferencia nodal incluye los
componentes low; no se descartan por coincidir los voltajes altos.

Máximo KCL publicado **1,64609×10⁻¹² A** frente a 10⁻¹¹ A;
máxima corrección Newton **4,45652×10⁻⁹ V** frente a 10⁻⁸ V;
máximo error de ecuación de rama **2,11524×10⁻²⁴ V** frente a 10⁻¹⁴ V.
Restauración tipada exacta y linaje de los dos historiales pasan en todos.
Los 141 conteos de iteración por ruta no constituyen un benchmark de CPU.

## Evidencia y prueba fallida conservada

[Datos](../evidence/loudness_latch_bdf_static_precision_continuation.json.gz):
**381.316 bytes**, SHA256 comprimido
`949bc14871b3e61ff8ce04c19620a55d2ff07f67735b7244f9e26bfc61b78c86`;
SHA256 JSON canónico
`3d4b4923ba77c96856d5d79a5bff9777ea9ce6fc37de03d07920a15006bc82e8`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_continuation_summary.json):
130 entradas, HEAD contextual `260de8a`, fuentes sin cambios antes/después.

El [recibo de validación](../evidence/loudness_latch_bdf_static_precision_continuation_validation.json)
conserva dos intentos. El primero falla una aserción de presupuesto: pedía
h=1 ns en reset, fuera de la razón BDF2 ≤2, y esperaba el mensaje de otro
gate posterior. Se conserva salida y fuente fallida completa. El adaptador
se corrige usando el intervalo guardado válido; no cambia datos ni gates.

El segundo pasa **4/4 pruebas**, 4,0648 s, entradas intactas: 320 residuales,
64 matrices, cuatro FD, publicaciones, diferencias, ocho solves nuevos de
replay e identidad de los métodos heredados. No repite la suite histórica.

`python tools/validate_bdf_static_precision_continuation.py`

## Siguiente gate

La variante reproduce estas ventanas condicionadas, incluida la región de
reset de seis nanosegundos. No prueba arranque desde DC, otras fuentes,
controles, cargas, controlador E4G8 o refinamiento global. El contraste
anterior desde DC conserva **8,234 mV** frente a 1 mV. Ampliar primero el
reloj guardado a la trayectoria completa y luego repetir los contrastes
temporales con política explícita. Física, audio y deadline siguen abiertos.
