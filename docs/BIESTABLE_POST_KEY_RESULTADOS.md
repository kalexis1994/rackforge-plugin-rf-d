# Estado consistente y recinto local post-KEY

## Identidad del experimento

Se resuelve el límite derecho KEY 0→10 V en t=0: 94 potenciales y 25 tasas,
con las 25 cargas publicadas previas conservadas. El modelo CA3046 documental
nominal y sus parámetros sintéticos permanecen idénticos. El primer
[protocolo](BIESTABLE_POST_KEY_PROTOCOLO.md), helper y productor se congelan
en `85b7bcd`. El primer lanzamiento falla al importar por un paréntesis sin
cerrar: **cero candidatos evaluados y cero datos escritos**. Recibo y versión
se conservan en `5d1594f`, antes de medir con la sintaxis reparada.

No se usa un paso con dt diminuto. KCL y restricciones de carga se resuelven
simultáneamente; C10 conserva R*C*ydot con R=25,5 kΩ. El evento algebraico
permite saltos de potencial manteniendo cargas. El candidato se publica con
identidad propia, clock cero, fuente previa/posterior y ninguna historia anterior.

## Dos semillas y publicación de laboratorio

Newton Decimal80 converge desde V77=9,5 V en **11 evaluaciones** y desde
V77=9 V en **24**. Las tasas empiezan en cero y los demás potenciales en DC.
Los 33 candidatos de line search se aceptan sin rechazos de dominio; todas
las trazas quedan guardadas. La regla previa elige la primera semilla.
No se calcula otro DC. Ambas soluciones coinciden dentro de la meta fijada.

V77_post es **9,646427209278158 V**; la tasa de coordenada máxima es
**964,642720157 V/s**. No es una corriente: cada tasa se multiplica por
su escala S antes de sellar KCL. El residual independiente Decimal100 de la
publicación racional restaurada es **5,33133e-52 A** como máximo en KCL y
**6,20165e-78 V** en restricciones de coordenada. Pasa los gates 10 pA y
10 fV; JSON conserva exactamente los valores y clock cero.

Esta es publicación racional del laboratorio. Todavía no incluye redondeo
high+low del estado tipado ni restauración dentro del integrador BDF.
El solve de la inversa H119 binary64 **rechaza el gate backward 1e-10**;
los máximos binary/Decimal80 alcanzan aproximadamente uno. Se conserva el
rechazo completo y no se admite la inversa en audio. El certificado ideal
siguiente incluye esa inversa como precondicionador aproximado.

## Primer recinto conservado y banco de escalas separado

Con peso de tasa D_rate=1e-6 s, las cajas 1e-9 y 1e-8 V prueban raíz local
para las cargas publicadas nominales. Las cajas 1e-7 y 1e-6 V rechazan
contracción. **Ninguna de las cuatro cubre la incertidumbre de cargas DC**:
el residual precondicionado robusto alcanza eta=3,72707162061e-5 V.
Todos los ocho certificados originales permanecen intactos.

El [protocolo de escalas](BIESTABLE_POST_KEY_ESCALAS_PROTOCOLO.md), fijado
separadamente en `19f3914`, reutiliza exactamente el centro y precondicionador,
sin nuevas soluciones ni inversas. Fija tres pesos y cuatro radios por peso.
La caja normalizada limita voltajes por r y tasas por r/D_rate; masa y
columnas de tasa permanecen completas. Las no linealidades dependen de
potenciales, cuya escala se conserva en uno.

| Peso de tasa (s) | Radio normalizado (V) | q superior | Caja DC completa | Cota normalizada posterior (V) |
| --- | --- | --- | --- | --- |
| 1e-09 | 1e-09 | 6.25043311534e-05 | rechazado | — |
| 1e-09 | 1e-08 | 0.000625043312009 | rechazado | — |
| 1e-09 | 1e-07 | 0.00625043320161 | aceptado | 3.75051395757e-08 |
| 1e-09 | 1e-06 | 0.0625043402219 | aceptado | 3.97556146712e-08 |
| 1e-12 | 1e-09 | 0.000107130949948 | rechazado | — |
| 1e-12 | 1e-08 | 0.000445049230959 | rechazado | — |
| 1e-12 | 1e-07 | 0.0041275839397 | aceptado | 2.9236987986e-08 |
| 1e-12 | 1e-06 | 0.0409532924332 | aceptado | 3.03596369543e-08 |
| 1e-15 | 1e-09 | 0.0806308189459 | rechazado | — |
| 1e-15 | 1e-08 | 0.0808695589181 | rechazado | — |
| 1e-15 | 1e-07 | 0.0832569643659 | aceptado | 3.17606010978e-08 |
| 1e-15 | 1e-06 | 0.107131591405 | aceptado | 3.26098555887e-08 |

La selección previa toma el **primer par aceptado**, D_rate=1e-9 s y
r=1e-7 V; no elige la menor cota después de medir. q=0,00625043320161,
eta=3,72707162061e-8 V e imagen estrictamente interior. Para **cada vector
de cargas de la caja DC** existe una raíz local única en esa caja. Su error
respecto al centro publicado es <=eta/(1-q):

- **Potenciales: 3,75051395757e-8 V (~37,51 nV)** en cada nodo.
- **Tasas de coordenada: 37,5051395757 V/s** en cada memoria.

Estas cotas incorporan la incertidumbre del DC y su publicación de carga.
No certifican unicidad fuera del recinto, dispersión de parámetros vintage
ni continuidad global de ramas. La norma de la prueba tiene unidades V;
la cota de tasa se divide por el peso en segundos. No se identifica con las
normas de ventanas temporales anteriores ni con crecimiento físico.

## Datos y validación

[Proyección](../evidence/loudness_latch_bdf_static_precision_key_projection.json.gz): **3107865 bytes**, SHA comprimido
`6eef4a30c16e906e951f637488e4d59115d3b549cf18325a6efde32fe01639b4`, canónico
`9203fc52deb93b4609fddef77729f08a0cb98c2e612763284f7dade1d00787cd`.

[Escalas](../evidence/loudness_latch_bdf_static_precision_key_scaled.json.gz): **4446868 bytes**, SHA comprimido
`50a13dc29bbcaf4dfd4be15c06c8d4a6ec35f63c1befc7deeca06a9aecef6d7a`, canónico
`b0a77ceac3c20edede2ae3c88ec64a13e233fd623d77de05d5a46369d9c5d77b`.

Datos, ocho regresiones y validador se fijan en `f4e0933`. Primer intento:
**23,9821359 s**, siete pruebas pasan y una fixture falla porque exige
igualdad exacta con 1/25 en una cota redondeada hacia fuera. Se conserva
fuente íntegra y recibo en `57c0b0b`. La corrección `7ba069e` exige inclusión
>=1/25 y exceso <=2^-200 en esa fixture, sin alterar datos, helper, radios,
modelo o gates. Segundo intento: **24,2123045 s**, ocho pruebas pasan.

Se verifican eliminación con pivot, Jacobiano por diferencias independientes,
masa y resistencia serie, ambas trazas, los veinte certificados completos,
Jacobiano intervalar construido desde corrientes salientes, productos
Decimal80/100, caja de las 25 cargas, unidades, publicación, bytes y fuentes.
Ambos intentos tienen entradas idénticas antes/después. El intento de import
previo se verifica contra sus blobs Git, separado de versiones de tests.
El [corpus ampliado](BIESTABLE_POST_KEY_ENTRADAS.md) conserva ambas mediciones,
rechazos y las diez versiones fallidas históricas de pruebas.

## Alcance y próximo corte

El anclaje local **del evento racional de laboratorio** queda probado.
`binary_integrator_initial_error_known` sigue falso. No se avanza tiempo,
se sustituye una trayectoria ni se reutiliza indebidamente el soporte del
arranque histórico. **1 mV global sigue abierto**, igual que resto no lineal,
cobertura, identificación física, voz audible y deadline.

El [siguiente plan](BIESTABLE_POST_KEY_PUBLICACION_PLAN.md) aborda estado
high+low tipado, arranque de orden declarado sin historial fabricado y
primer tramo contiguo con procedencia propia.
