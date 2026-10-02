# E4G8 con Newton compensado: decisiones, estados y sombras

El [protocolo previo](BIESTABLE_CONTROLADOR_COMPENSADO_PROTOCOLO.md) y driver
se fijaron en `6ef7a0f`, después de archivar el
[reloj completo impuesto](BIESTABLE_RELOJ_COMPLETO_COMPENSADO_RESULTADOS.md).
Esta vez el controlador decide intervalos y rechazos a partir de sus estados
propios. Sólo cambia la construcción del network de Newton a
`increment-pair/compensated-static-J66/v1`.

## Control del cambio

Los AST de los dos drivers coinciden después de normalizar **una única
sustitución** del constructor. Se archivan ambas fuentes. Las funciones
de arranque, estimador, publicación y cálculo modal, así como el objeto
Policy, son los mismos. Las pruebas verifican esos vínculos además del AST.
Policy E4 y umbral de crecimiento 0,125 permanecen iguales.

El guard modal mantiene su derivada compartida original. Los Jacobianos
de Newton y del descriptor modal tienen alcances distintos; este corte
no contrasta una nueva implementación del descriptor.

## Barrido y equivalencia

| Comprobación | Resultado |
| --- | --- |
| Cobertura propia | **0..3 ms**, completa |
| Ensayos totales | **6.534** |
| Ensayos aceptados / rechazados | **6.485 / 49** |
| Intervalos publicados | **6.486**, dos de arranque |
| Medios intervalos provisionales de ensayos aceptados | **12.968** |
| Razón de los 49 rechazos | Error de voltaje o incremento de juntura |
| DC frente a E4G8 archivado | Estado completo idéntico |
| Proyecciones de decisiones aceptadas/rechazadas | Idénticas a E4G8 |
| Reloj, fuentes y métodos publicados | Idénticos a E4G8 |
| Estados completos frente a variante de reloj fijo | **6.486/6.486 idénticos** |
| Máximo nodal frente al E4G8 anterior | **6,20949×10⁻¹² V**, pasa 10 nV |
| Máximo de memoria en coordenada V | **8,76941×10⁻¹² V**, pasa 10 nV |

Los provisionales no contaminan la memoria aceptada. Se conservan los dos
historiales propios, las 21 memorias lineales y cuatro cargas; la escala
10⁻¹² C/V de esas cargas es exclusivamente numérica. No se reinicia estado,
selecciona otra raíz ni cambia el reloj para pasar un contraste.

KCL publicado máximo **9,95576×10⁻¹² A**; provisional máximo
**9,94497×10⁻¹² A**, ambos bajo 10⁻¹¹ A. Los gates de corrección, ramas,
restauración y descriptor se mantienen. El tiempo de integración offline
932,655 s identifica esta ejecución, sin admitir CPU de audio o deadline.

## Comparador temporal: ambos fallos permanecen

Se repite el comparador lineal histórico, sin retimado ni cambio del gate
**1 mV**. Es un diagnóstico sobre intervalos aceptados; no son solves de
consulta independientes ni una cota entre muestras.

| Referencia | Puntos comparados | Máximo | Nodo / instante | Gate |
| --- | --- | --- | --- | --- |
| D4 | 9.998 | **8,23403042 mV** | 66 / 2,44247036 ms | Falla 1 mV |
| E4 | 12.370 | **1,00186139 mV** | 67 / 2,42242432 ms | Falla 1 mV |

Reproducir el controlador no demuestra que su estimador acote el error
acumulado. El Jacobiano más preciso conserva la conducta, pero no resuelve
estos fallos temporales. El siguiente bloque debe estudiar propagación de
memoria y sensibilidad acumulada con sellos auditados, y luego declarar
otro contraste temporal. No ajustar tolerancias o raíces a estos máximos.

## Evidencia y validación

[Datos completos](../evidence/loudness_latch_bdf_static_precision_adaptive.json.gz):
**81.519.430 bytes**, SHA256 comprimido
`3cdf86978603d1acb3cd9fb15d8730196c183aed4efe27687783b9112694e14b`;
SHA256 JSON canónico
`a5345be7dc28bf67938cf451c69f9341e453e8a2dee328ec85bc13f7dd639096`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_adaptive_summary.json):
136 entradas, HEAD contextual `6ef7a0f`, matrices de alcance, máximos y
conteos. Fuentes/datos permanecen iguales antes/después de la ejecución.

El [recibo](../evidence/loudness_latch_bdf_static_precision_adaptive_validation.json)
registra **5/5 pruebas**, un intento exitoso, 142,630 s: driver/globals,
publicación directa de 6.486 intervalos y 12.968 sombras, decisiones,
contrastes de nodos/memoria, estados del reloj fijo, seis replays de ensayos
aceptados y uno rechazado, almacenamiento y ambos comparadores temporales.
Las entradas permanecen intactas. No se repite la suite histórica.

`python tools/validate_bdf_static_precision_adaptive.py`

No hay oráculo espacial completo independiente, parámetros vintage
identificados, cota temporal, audio de voz completa ni deadline admitidos.
