# Raíz local de DC y condición necesaria del salto KEY

## Experimento y fuente congelados

El [protocolo](BIESTABLE_DC_EVENTO_PROTOCOLO.md), helper y productor se fijaron
en `2c5c577` antes de medir. Se reutiliza el DC KEY=0 del reloj completo,
con sus 94 potenciales, pares de memoria y parámetros nominales sintéticos.
No se resuelve otro DC ni se ajusta un parámetro. El grafo estático
independiente usa las leyes resistivas, Ebers–Moll y Shockley existentes,
levantando exactamente sus coeficientes binarios.

Un Jacobiano Decimal100 en el punto proporciona **un precondicionador
binary64 candidato**. La prueba racional posterior incluye sus errores:
no se trata como inversa exacta del Jacobiano ideal ni se admite en audio.
El precondicionamiento por sellos rank-one conserva cancelaciones antes
de encerrar exponenciales. No se cambian los gates históricos.

## Inclusión contractiva del DC

Para T(v)=v-X*F(v), el recinto de I-X*J en una caja infinita de radio r
da q_i=sum_j abs(D_ij) y q=max q_i. El punto aporta eta_i=abs((X*F(x))_i).
Si q<1 y eta_i+r*q_i<r en todas las filas, T transforma la caja en sí
misma y es contractiva: hay una raíz local única. La misma prueba implica
X no singular, de modo que un punto fijo es una raíz de F. El error
posterior es <=max eta_i/(1-q), sin ejecutar otra iteración de Newton.

Los cuatro radios fijados antes de medir pasan:

| Radio de caja (V) | q superior | Error nodal posterior (V) | Existencia / unicidad local |
| --- | --- | --- | --- |
| 1e-9 | 2,83162227339e-5 | 7,39762166411e-11 | certificadas |
| 1e-8 | 2,83162249636e-4 | 7,39950745258e-11 | certificadas |
| 1e-7 | 2,83162500155e-3 | 7,41841837033e-11 | certificadas |
| 1e-6 | 2,83165005167e-2 | 7,61298529340e-11 | certificadas |

El caso primario es el primero aceptado, según la regla previa: radio 1 nV.
Su error posterior de **~73,98 pV** acota todos los nodos respecto a esa
raíz local ideal. Se conservan los cuatro recintos completos, exponentes,
filas, imagen de caja y certificados. No se demuestra que esa raíz sea la
única rama global ni que el equipo vintage tenga estos parámetros sintéticos.

## Error de publicación de las 25 memorias

El recinto nodal posterior se convierte a **21 cargas lineales y cuatro
junturas monótonas**, comparadas con las memorias publicadas exactas:
C*(high+low) en ramas lineales y QBE/QBC binarias en junturas. Se incluyen
tanto el error nodal de DC como el desajuste de publicación de carga.
Las escalas siguen siendo C y el S binario existente de 1e-12 C/V.

La norma inicial fija Wlineal=1 y Wjunction=dyadic_floor(S/Cupper(x)).
Los cuatro pesos son **1/8, 1/4, 1/256 y 1/512**. El error inicial de memoria
en esa norma infinita ponderada queda acotado por **1,47952708453e-10 V
(~147,95 pV)**; la fila limitante es la memoria lineal 14, base cero.
Los datos guardan todos los recintos de carga y errores por coordenada.

Esta es una **norma inicial nueva**, con regla fijada por el DC, no una
modificación de las normas de ventanas anteriores. Para usarla en otro
tramo hay que convertir pesos/métrica y conservar el mismo vector de error.
El resultado acota el DC KEY=0; no demuestra el anclaje consistente a t=0+
después de conmutar, ni propaga la región entre DC y ataque.

## CR10 y el evento KEY 0→10 V

El grafo identifica CR10-contour entre KEYBOARD_TRIGGER y la fila nodal 77.
Conservando voltajes del DC tras pasar KEY a 10 V, su exponente queda en
**[259,4782964396; 259,4782964434]**, completamente fuera del dominio <=45.
La hipótesis de continuidad de **todos** los potenciales queda refutada
para el modelo congelado. No se evalúa esa exponencial ni se recorta su
valor para continuar; tampoco se relaja el dominio.

Dentro del dominio existente, es necesario que:

`V77_post >= 10 - 45*(ideality_CR10*vt) = 8,26575090933 V`.

Comparado con todo el recinto previo, el salto ascendente necesario es
**al menos 8,26575090154 V**. Es una condición necesaria de dominio,
no el valor de una solución post-evento calculada.

La fila 77 no tiene puertos de ninguna de las **25 memorias modeladas**:
su fila de masa es cero. Por ello puede ser una incógnita algebraica del
evento; no hay fundamento para imponerle continuidad por almacenar otras
cargas del circuito. Esto no identifica todas las capacitancias parasíticas
del hardware físico, que siguen fuera del alcance del modelo.

Para un evento con corrientes acotadas, las cargas almacenadas deben
conservarse y las incógnitas algebraicas resolverse con KEY=10. Falta probar
esa consistencia y su sensibilidad al recinto de cargas iniciales. El
[plan del siguiente corte](BIESTABLE_ESTADO_POST_KEY_PLAN.md) fija las
ecuaciones que deben resolverse sin avanzar el reloj ni fabricar historiales.
Interpolar desde los voltajes KEY=0 como si fueran el límite derecho no
queda autorizado por el certificado de DC.

**1 mV global sigue abierto.** Quedan estado post-KEY, anclaje a la derecha,
arranque del interpolante, resto no lineal temporal y cobertura continua.
El DC certificado es un resultado numérico del modelo nominal; física,
voz audible y deadline mantienen sus gates propios.

## Evidencia y validación preservada

[Datos](../evidence/loudness_latch_bdf_static_precision_dc_anchor.json.gz):
**710576 bytes**, SHA comprimido
`e1c4155a17231f2786d2fe93124e448374d5fdf0df692a3d940a21d9cb39a970`,
SHA canónico `a2355ae246ca4d6043edd3c328fec659a844ae3bf272c75e78a72f29ee2bd636`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_dc_anchor_summary.json).

Datos, primera suite y validador se congelaron en `c1dd9a0`. El primer
intento de validación falla por dos errores de test: una fixture Fraction
no serializable y una comparación que trata Decimal redondeado como valor
exacto frente a un recinto racional degenerado. Fuente y recibo fallido
se preservaron en `7bfc33c`. La corrección de tests se fijó en `744238f`
antes del segundo intento. **No cambian helper, datos, radios o gates.**

La [suite](../tests/test_loudness_latch_dc_anchor.py) pasa **6/6 en el segundo
intento**, 6.2415193 s; el primero dura 5.6000784 s. Verifica inclusiones
lineales y no lineales con raíz conocida, rechazos q>=1 y caja insuficiente,
cancelación exacta y conservación de corriente. Reproduce los cuatro radios;
contrasta residual/productos Decimal80/100 y productos de un Jacobiano
puntual intervalar independiente. Dos recintos válidos deben intersectarse:
un resultado Decimal no se convierte artificialmente en testigo exacto.

Comprueba 25 memorias, compensación, escalas, monotonía de junturas y pesos,
evento, fila de masa cero, dominio y ausencia de estado post-KEY. El
[recibo](../evidence/loudness_latch_bdf_static_precision_dc_anchor_validation.json)
preserva ambos intentos con SHA antes/después idénticos en cada uno.
El [corpus](BIESTABLE_DC_EVENTO_ENTRADAS.md) recupera también la fuente
fallida por su SHA, sin sustituirla por el archivo vigente.

```powershell
python tools/loudness_latch_bdf_static_precision_dc_anchor.py
python tools/validate_bdf_static_precision_dc_anchor.py
```
