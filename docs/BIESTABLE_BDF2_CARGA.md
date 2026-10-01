# BDF2 variable sobre carga conservativa

## Alcance y procedencia

Segundo integrador temporal para el laboratorio de 94 nodos; comparte el
grafo, leyes estáticas, parámetros sintéticos y solver espacial anteriores.
No es un segundo oráculo espacial ni identifica un transistor vintage.
Conserva el objetivo documental SVC-9, Fig.9-7/p.9 y pasivos de
Figs.9-11/p.13, 9-8/p.10 y 9-17/p.19. Sigue limitado a Q25/Q15 dinámicos,
BUS=0 V y controles fijos del laboratorio; ocho BJTs del contorno y los
semiconductores de audio conservan sus modelos instantáneos.

Código: `tools/loudness_latch_bdf_reference.py`. Euler y sus informes
permanecen intactos. Todo el trabajo nuevo es Python offline.

## Derivación y representación

Interpolar Q con un polinomio cuadrático en `t`, `t−h`, `t−h−k` y derivarlo
en t da, con `r=h/k`:

`a0=(1+2r)/(1+r)`, `a1=−(1+r)`, `a2=r²/(1+r)`.

La corriente es:

`dQ/dt ≈ [a0·(Qnew−Qold) − a2·(Qold−Qolder)] / h`.

Q se mide en C, h/k en s, los coeficientes son adimensionales y la corriente
en A. La forma de diferencias evita depender del cero convencional de Q.
Una regresión deriva los coeficientes resolviendo las condiciones de momentos
del polinomio y verifica la invariancia de origen con racionales exactos
sobre los valores binarios.

Para reutilizar el stamp implícito existente, se forma una memoria virtual:

`Qstar = Qold + γ·(Qold−Qolder)`, `γ=a2/a0`, `hstar=h/a0`.

Así `dQ/dt=(Qnew−Qstar)/hstar`. Los capacitores lineales forman Vstar en
pares compensados; las cargas BE/BC usan su historial ligado a parámetros.
Los nodos de partida son los del estado aceptado actual. Qstar es una
combinación numérica provisional, nunca un estado físico publicado.

C10 conserva su resistencia serie de 25,5 kΩ:

`I10=(VLnew−VRnew−Vcstar)/(R+hstar/C)`.

Se publica `Vcnew=Vcstar+hstar·I10/C`. Decimal80 verifica después la
derivada directamente con **los dos historiales reales**, sin usar Qstar,
y comprueba `VLnew−VRnew−Vcnew−R·I10=0`.

## Contrato de memoria y rechazo

El formato `rf-d/bdf-two-state/v1` contiene ambos estados compensados,
el intervalo previo, sus fuentes y el tiempo actual. Sólo el DC inicial
declarado puede carecer de un estado anterior. La primera llamada usa BE;
las siguientes usan BDF2. Un rechazo no inicia de nuevo ni sustituye BDF2
por Euler. Se conserva cada historial entrante.

Se exige `0<r≤2`: no se duplican más que una vez los intervalos aceptados.
Para coeficientes congelados con corriente cero, la raíz parasitaria es
`a2/a0=r²/(1+2r)`, como máximo 0,8 en ese rango. Es una observación de la
recurrencia congelada, no una prueba de estabilidad de la trayectoria DAE.
Las reducciones de paso siguen utilizando ambos estados.

Los gates siguen siendo KCL <10 pA y corrección <10 nV, con 80 iteraciones
y 24 fracciones de búsqueda. Ninguna combinación virtual modifica la
topología, limita un voltaje ni selecciona otra raíz del biestable.

## Primer contraste

Informe: `evidence/loudness_latch_bdf_probes.json`.
Siete intervalos: 25/25/50/25/12,5 µs y 1/2 ns, desde DC con KEY=10 V.

| Comprobación | Resultado | Gate previo |
| --- | ---: | ---: |
| KCL directa de cargas publicadas | 7,67e−15 A | 1e−11 A |
| Ecuaciones de ramas lineales/C10 | 2,73e−26 V | 1e−14 V |
| Diferencia de nodos híbrido/FD | 1,78e−15 V | 1e−8 V |
| Diferencia Jacobiano `abs(ΔJ)/(1+abs(J))` | 2,26e−10 | 1e−8 |

Un RC sintético de R=10 kΩ, C=10 nF, τ=100 µs e inicial 1 V se contrasta
con `exp(−t/τ)` hasta 500 µs. No es una constante audible ni un ajuste del
Model D. Con h=10/5/2,5/1,25 µs, los errores finales son
67,145/16,092/3,940/0,975 µV: cocientes entre 3,8 y 4,3, gate establecido
para ese caso. El arranque BE queda explícito en el cálculo.

Seis pruebas verifican esos resultados, coeficientes, origen de carga,
ambos historiales ante rechazo, formato serializado y fuentes fijadas.
Este corte no cubre aún toda la transición de 3 ms ni admite su refinamiento.

## Próximo barrido

Comparar BDF2 con un predictor BE desde el mismo estado actual, conservando
el estado anterior para BDF2. El control local usará voltajes de nodos y
junturas, sin escala absoluta de Q. El arranque comparará el BE completo
con BE a medio paso seguido por BDF2 a medio paso; sólo se publicará la
ruta fina completa si pasa todos los gates. Las diferencias son estimadores
propios, no cotas del error acumulado.

Políticas A3/B3 antes de ejecutar: Vabs nodos/junturas=100/25 µV,
Vrel=1e−4/2,5e−5, Δjuntura por intervalo=50/25 mV,
`hreal·λ+≤0,1/0,05`, h máximo=100 µs, mínimo=1 ps y 3000 intentos.
El crecimiento se limita a ×2 del intervalo real previo. Comparación al
mismo tiempo: máximo 1 mV en los 94 nodos, sin alinear eventos para admitirla.

`python tools/loudness_latch_bdf_probes.py`

`python -m unittest discover -s tests -p test_loudness_latch_bdf.py -v`
