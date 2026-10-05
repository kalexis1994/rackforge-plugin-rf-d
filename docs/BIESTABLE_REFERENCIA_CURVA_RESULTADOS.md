# Octavo soporte: referencia curva con extremos conservados

Modelo documental CA3046 nominal con parámetros sintéticos, sin unidad
física. El [protocolo](BIESTABLE_REFERENCIA_CURVA_PROTOCOLO.md) y las fuentes
se congelan en `04e5519`, antes de medir. Un lanzamiento interrumpido sin
salida ni publicación se conserva en `6a40b44`; la ejecución posterior
mantiene exactamente las mismas fuentes. No se atribuye una causa externa
que no se haya podido verificar.

## Resultado del banco completo

Fuente: [séptimo cierre de C7](BIESTABLE_FORCING_C7_RESULTADOS.md), sus 22
memorias reales restituidas y P fija. Único soporte intentado: índice 7,
≈12,5→25 µs, con historias publicadas adyacentes. Variantes exteriores
affine/c7_bubble y radios interiores 0,1/1/10 µV, fijados antes de medir.

| Referencia | Radio | Resultado |
| --- | --- | --- |
| Afín | 0,1 µV | Pico entrante fuera del radio; sin recintos nuevos |
| Afín | 1 µV | Rechaza: cota local ≈4,185274 µV |
| Afín | 10 µV | No soportado: norma escalada del kernel >4096 |
| C7 cuadrática | 0,1 µV | Pico entrante fuera del radio; sin recintos nuevos |
| C7 cuadrática | 1 µV | Acepta: cota local ≈0,326723 µV |
| C7 cuadrática | 10 µV | No soportado: norma escalada del kernel >4096 |

Selección primaria **[1,1]**. Se certifican **ocho intervalos contiguos
hasta ≈25 µs**, extremo exacto
`7378697629483821/295147905179352825856` s. El máximo de todo el prefijo
permanece en **7,928168411011273e-7 V**, ≤0,793 µV, heredado del soporte
anterior. No confundir esa cota con el pico local del nuevo intervalo.

Los rechazos de 10 µV son límites del dominio declarado del kernel;
no se publica una cota matemática calculada fuera de ese dominio.

## Cambio de referencia, residual y memoria

La X candidata fija del punto medio afín define A≈0,5993781707010053 V/s
y p=A*h*u*(1-u). Su pico candidato es ≈1,873057 µV; ambos endpoints son
exactamente cero. Los potenciales usan −X_v,C7*p; C7 añade p a su memoria.
La corrección candidata supera el radio del error permitido: el radio
acota la distancia de la solución a la **nueva referencia curva**, no
la distancia entre las dos referencias. Los extremos del integrador no
cambian. El certificado nuevo paga el residual completo de esa curva.

Se reconstruyen 94 potenciales, 21 cargas lineales con sus restricciones
RC, y cuatro Q(v) por piezas. La expansión exponencial de orden seis
conserva polinomios de grado doce para voltajes cuadráticos. Restos
uniformes, derivadas físicas variables y corrientes C(v)*v' se incluyen.
P, normas y pesos permanecen fijos; recintos y tasas se renuevan.

En la última celda [7/8,1], nodo 81, la afín suma ≈323,726 nV de anclaje
y ≈3861,548 nV de forcing. La curva suma el mismo anclaje y ≈2,997 nV
de forcing: ≈326,723 nV. Su error final real de C7 es ≤326,672 nV.
La burbuja desaparece en la interfaz; las 22 cotas finales corresponden
a errores reales respecto al endpoint publicado y pueden transportarse.

Se obtienen **17 precondicionadores candidatos**, **32 recintos nuevos
de inversa**, **3168 consultas LDL de tasa** y **256 certificados de
acción de subcelda**. Cero solves no lineales o sistemas de métrica nuevos.
La comparación renueva ocho celdas por referencia en dos radios cada una.

## Evidencia y alcance

Datos y seis regresiones se congelan en `0cf6e0c` antes de validar.
[Datos](../evidence/loudness_latch_bdf_static_precision_curved_reference.json.gz):
60932689 bytes, SHA comprimido
`43c35d2ce7965e5338bf26afdff3d3b805f7070a849fe5343d448e68e5b313cb`,
canónico `4c40ee2952633164c1d23ecb4b4ddab44d75b7bd16f29c64265a834d750f5879`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_curved_reference_summary.json),
[validación y corpus](BIESTABLE_REFERENCIA_CURVA_ENTRADAS.md).

El resultado certifica una reconstrucción nominal por tramos con una
referencia explícita nueva. No modifica circuito, parámetros, integrador
o trayectoria publicada, ni identifica la trayectoria vintage. Cobertura
completa, gate global 1 mV, hardware, voz, audio nativo y deadline siguen
abiertos. Siguiente: [continuación curva](BIESTABLE_PREFIJO_CURVO_PLAN.md).
