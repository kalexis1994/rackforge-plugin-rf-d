# Forcing firmado de C7 y séptimo intervalo certificado

## Fuente y congelación

Modelo documental CA3046 nominal, parámetros sintéticos intactos.
Fuente: último certificado real del [prefijo dirigido](BIESTABLE_PREFIJO_DIRIGIDO_RESULTADOS.md),
seis intervalos hasta ≈6,25 µs, 22 memorias, P y pico conocidos.
Se intenta sólo su séptimo soporte, índice 6, hasta ≈12,5 µs.
No se reinicia DC ni se toma memoria de una rama rechazada.

[Protocolo](BIESTABLE_FORCING_C7_PROTOCOLO.md),
[helper](../tools/loudness_latch_signed_memory_shift.py) y
[productor](../tools/loudness_latch_bdf_static_precision_signed_memory.py)
se congelan en `33c11a3`. Datos, ocho tests y validator se fijan en
`c063e31`. Se reutilizan por certificado/SHA 16 inversas, 16 tasas y
128 acciones; cero solves, precondicionadores, recintos, métricas o
consultas de tasa nuevos. Hay 128 compensaciones nuevas de subcelda.

## Por qué se conserva el signo temporal

La fuerza nominal de C7 empieza cerca de +0,300 V/s y termina cerca de
−0,300 V/s en el soporte. Su integral firmada termina en ≈4,416 pV,
pero la magnitud integrada contribuía a un presupuesto nodal de
≈1,2904 µV. La dirección temporal proviene del polinomio completo del RHS;
no se deduce de que dos corrientes parezcan opuestas.

El descriptor da e'=B(t)e+f(t), con B=-Hbar^-1_memory,memory y
f=-Hbar^-1*R. Se integra exactamente p'=−X_binary*R_poly sólo en C7,
partiendo de cero y conservando continuidad entre las ocho celdas.
Para z=e-p, la fuerza pasa a (f-p')+B(t)p. **p es una candidata auxiliar,
no la solución verdadera**: se paga todo el defecto y los restos de f-p',
y todos los acoplamientos de B(t)p mediante la inversa intervalar completa.

El término directo nodal añade |Hbar^-1_potential,C7*p|. Las tasas,
ganancias, P y normas permanecen iguales. Tras propagar z se restituye
p en todos los picos y endpoints de memoria correspondientes a C7.
Se identifican campos de z y kernels que actúan sobre z; las cotas de e
publicadas sirven para transporte posterior. Ninguna carga, ley o
reconstrucción física cambia. Los restos independientes no se cancelan.

## Banco y cierre estricto

| Radio | absolute | signed_c7_shift |
| --- | --- | --- |
| 0,1 µV | Pico entrante no cabe | Pico entrante no cabe |
| 1 µV | ≈1,290396602 µV; rechazo | ≈0,792816841 µV; aceptado y seleccionado [1,1] |
| 10 µV | Presupuesto enorme; rechazo | Presupuesto enorme; rechazo |

El modo absoluto de 10 µV se identifica por la [repetición de enteros](BIESTABLE_CIERRES_ENTEROS_RESULTADOS.md).
Todas las fracciones exactas permanecen archivadas, con política decimal
sin límite de longitud y dominio de kernel <=4096 sin cambios.

El prefijo contiene **siete intervalos contiguos hasta aproximadamente
12,5 µs**, con **error nodal exterior ≤0,793 µV**. Su tiempo exacto es
7378697629483821/590295810358705651712 s. No queda hueco en este soporte;
no se certifica el octavo por extrapolación.

El pico nuevo está en la celda 4, nodo índice 81: anclaje
≈323,9759706 nV y forcing/restauración particular ≈468,8408705 nV.
La particular alcanza una cota de ≈468,7054857 nV. En C7, el presupuesto
integrado de f-p' es ≈3,2881e-17 V y el de Bp ≈0,199029 nV; ambos están
incluidos. Las demás coordenadas pagan sus propios Bp y forcing anterior.
Una particular de pequeño endpoint no implica pequeño pico interior.

La memoria final real de C7 queda en ≈324,0785403 nV. Antes de restituir
p eran ≈324,0741245 nV; se añade ≈4,4157843 pV. La diferencia pequeña
sigue pagada. Las 22 memorias finales conservan sus normas originales.

## Verificación y alcance

**Ocho regresiones pasan al primer intento en 66,8599714 s**, con fuentes
idénticas antes/después. Incluyen forcing afín con solución exacta y
cambio de signo, control sin cancelación, matriz variable con solución
racional conocida, resto independiente, contraejemplo al omitir Bp,
conversiones ponderadas/cuadráticas, primitivas en tiempo físico,
continuidad, restauración y reproducción completa de los 16 certificados.
[Recibo](../evidence/loudness_latch_bdf_static_precision_signed_memory_validation.json).
El [corpus](BIESTABLE_FORCING_C7_ENTRADAS.md) recupera 564 entradas de
97 informes, 134 hashes propios y quince fuentes históricas fallidas.
Sus dos pruebas pasan al primero en 97,8725673 s; diez pruebas nuevas
aceptadas en total, con fuentes y datos intactos.

[Datos](../evidence/loudness_latch_bdf_static_precision_signed_memory.json.gz):
29482093 bytes, SHA comprimido
`e1970f5987559c8d5045b13c13d6d69ded6993f48db3050a8722cc128154e0c6`,
canónico `8df39a6a4d6433656b6ddde6eea8cae7892b3882a1eb9936d8604786dc124a89`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_signed_memory_summary.json).

La prueba admite error del circuito nominal en estos siete soportes.
El [siguiente plan](BIESTABLE_REFERENCIA_CURVA_PLAN.md) estudia una referencia
curva con endpoints reales conservados. Trayectoria completa, 1 mV global,
identificación física, audio, motor nativo y deadline siguen abiertos.
