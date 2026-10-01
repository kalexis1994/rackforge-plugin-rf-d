# Defecto local y memoria compartida: contraejemplos exactos

La [derivación de doble paso](BIESTABLE_ESTIMADOR_BDF2_DOBLE_PASO.md)
partía de dos estados exactos. En una trayectoria, ambos son estados
numéricos. Este corte deriva cómo contaminan el contraste completo/medios
y refuta usarlo como una cota absoluta del error global.

## Problema y unidades

Se usa exclusivamente el escalar normalizado `y=t³`, `y′=3t²`, h/k=r∈(0,2].
La fuerza es independiente de y. Tiempo y estado son normalizados;
ninguna cifra se traslada a voltios, segundos o parámetros BJT de RF-D.
Todo se calcula con fracciones racionales exactas, sin Newton ni float.

Para BDF2 completo, las ganancias de los estados precedentes son:

`A=(1+r)²/(1+2r)`, `B=−r²/(1+2r)`, `A+B=1`.

El primer medio usa razón r/2; el segundo, razón 1, tiene ganancias
4/3 y −1/3. Si los errores entrantes son e₀ y e₋₁, el contraste satisface:

`D = Dexact + K(r)·(e₀−e₋₁)`

`K(r)=r²(r+2)/[3(r+1)(2r+1)]`.

Es una identidad sobre estos historiales reales. No describe las ganancias
variacionales de un DAE no lineal ni corrige su estimador automáticamente.

## Dos formas de quedar oculto

1. **Error común:** sumar el mismo desplazamiento a ambos estados precedentes
   desplaza completo y fino por ese valor. Su diferencia permanece idéntica.
   El contraste local no ve ese error acumulado común.
2. **Cancelación exacta:** con h=k=1, errores entrantes e₀=0 y e₋₁=19/4,
   ambas rutas producen **3/4** frente a destino exacto **1**. El contraste
   es exactamente cero aunque cada candidato tenga error −1/4.

No se afirma que ese segundo historial sea una trayectoria RF-D admisible.
Refuta una garantía que no imponga hipótesis sobre el error entrante.

## Acumulación en una trayectoria publicada

Desde estados exactos en −h y 0, se publican N pasos completos uniformes.
La recurrencia de errores es `eₙ=(4/3)eₙ₋₁−(1/3)eₙ₋₂+(4/3)h³`, con
e₋₁=e₀=0. Sus soluciones exactas son:

`eₙ=h³·(2n−1+3⁻ⁿ)`

`Dₙ=h³·(9/8−3⁻ⁿ)`.

La diferencia local permanece menor que (9/8)h³, mientras el error global
crece con n a h fijo. Tras 256 pasos, el cociente eₙ/Dₙ supera 450.
A tiempo final fijo T y h=T/N, el error global sí converge como h²:
este contraejemplo trata la inferencia desde D, no niega el orden de BDF2.

## Evidencia y siguiente gate

Productor: `tools/loudness_latch_bdf_memory_defect.py`.
Datos: `evidence/loudness_latch_bdf_memory_defect.json`.
Regresiones: `tests/test_loudness_latch_bdf_memory_defect.py`.

Se verifican razones 1/4, 1/2, 1 y 2, perturbaciones de ambos estados,
cancelación, trayectorias de hasta 256 pasos y escalado h=1/1000. Un
contraste independiente usa directamente la derivada del interpolante de
Lagrange de tres puntos, sin llamar al helper de coeficientes BDF2.

**5/5 regresiones pasan** en 0,064 s, el 2026-10-01. La evidencia guardada
se reproduce exactamente y conserva el SHA de su productor.

Para RF-D, [E4G8 desde DC](BIESTABLE_CRECIMIENTO_DESDE_DC.md) conserva el
contraste de trayectorias y la observación al mismo reloj. El próximo gate
necesita cuantificar dependencia del historial o refinamiento adicional;
reducir rechazos, un estimador pequeño o un FD coincidente no acota por sí
solo el error acumulado. No hay identificación física, audio o cota DAE.
