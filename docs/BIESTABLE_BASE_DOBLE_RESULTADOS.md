# Sensibilidad lineal de las 50 coordenadas de historia doble

[Protocolo](BIESTABLE_BASE_DOBLE_PROTOCOLO.md) y
[productor](../tools/loudness_latch_bdf_static_precision_memory_basis.py)
fijados antes de medir en `09d8bd6`, el 2 de octubre de 2026.
Se reutilizan 256 mapas sobre las cuatro ventanas de 64 pasos;
**cero solves no lineales nuevos y cero solves espaciales nuevos**.

## Productos y precisión

Se propagaron las 50 coordenadas de la base actual/previa completas.
Los **256/256 contrastes de productos** pasan 1e-8 normalizado.
Las matrices nodales 94x50 y de memoria 25x50 redondeadas de Decimal80
y Decimal100 coinciden en todos los intervalos.

| Ventana | Máx. diferencia normalizada de producto nodal | De memoria | Norma 2 nodal máxima | Norma 2 de memoria máxima | Norma 2 de historia doble máxima |
| --- | --- | --- | --- | --- | --- |
| prefix | 5,22958e-15 | 4,52979e-15 | 180,305 | 20,4340 | 28,7589 |
| attack | 1,58334e-14 | 3,23796e-15 | 2.885,333 | 782,180 | 1.105,389 |
| reset | 3,11684e-15 | 2,75335e-15 | 180,919 | 98,7595 | 138,494 |
| tail | 4,45081e-15 | 2,87207e-15 | 180,731 | 232,982 | 329,192 |

El contraste levanta **los mismos mapas binary64** y coeficientes ya
redondeados, incluyendo (1+gamma), a 80/100 dígitos. Verifica redondeo
acumulado de productos; no sustituye la auditoría de precisión espacial
de J/X/T. Sus SHA Decimal permiten reproducir cada suma/producto completo.
No se recortan términos pequeños ni se añaden parámetros de circuito.

## Direcciones y límites

Los máximos de norma son de matrices lineales homogéneas, con escala
Q/(1 pF), reloj y trayectoria fijados. La entrada usa norma euclídea
en las 50 coordenadas de ambos historiales; la salida nodal usa los
94 nodos. **No equivalen a ganancias de señal musical**, errores de
voltaje por sí solos ni umbrales físicos universales.

El máximo nodal de ataque está en índice 9, tiempo
**2,422232056 ms**. Su dirección derecha tiene componentes mayores en
coordenadas 20 y 45 (C7 actual y previa), aproximadamente +0,963491
y -0,267355. Esta memoria no estaba inyectada por separado en el corte
anterior. Los máximos nodales de prefix/reset/tail tienen contribuciones
principales de memorias de audio 6,3,7 y sus previas. Se guardan todos los
vectores, singular values y tiempos; no se atribuye el máximo a una
única componente ni causa física.

La base completa descubre direcciones de sensibilidad que las ocho
continuaciones no lineales anteriores no validaron. Próximo contraste:
declarar inyecciones pequeñas de C7 y de las direcciones de mayor norma,
con ambas memorias, amplitudes y ventanas fijadas; verificar la respuesta
no lineal antes de usarlas para estudiar el error entrante.

La recurrencia no contiene forzamiento de truncamiento ni defecto afín.
Una norma grande no explica por sí sola el fallo temporal, ni convierte
la diferencia cruda full/half en defecto exacto. El gate de **1 mV desde
DC sigue abierto**; tampoco se admite fidelidad vintage, audio o deadline.

## Datos y validación

[Datos](../evidence/loudness_latch_bdf_static_precision_memory_basis.json.gz):
30.537.138 bytes, SHA comprimido
`ce244d1dc892fb4cb3114c4548adc793c7e489d140723d6892938d7f41415de6`;
SHA canónico
`66387e0b0e2fb88671b52357665873f4c1b349c518db7c4cc843b1613185f008`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_memory_basis_summary.json):
139 entradas, máximos seleccionados bajo regla previa, direcciones y alcance.

El [recibo](../evidence/loudness_latch_bdf_static_precision_memory_basis_validation.json)
conserva cada intento y fuente fallida. La primera prueba comparaba singular
values de SVD sin vectores contra la ruta fijada con vectores: dos valores
pequeños diferían hasta 1,67075e-12, fallando la tolerancia del adaptador.
El dato original y ese fallo se conservan. La prueba corregida reproduce
la ruta SVD completa, exige igualdad de valores y mantiene el testigo
independiente ||A v|| / sigma_max = 1 con v normalizado.
No se cambian datos, mapas, protocolo ni gate de productos. Las normas SVD
son diagnósticos numéricos de esa ruta, sin certificación de todos sus
singular values pequeños.

Pasan **4/4 pruebas** en el segundo intento, 82,177 s; entradas idénticas
antes/después de ambos intentos. Las cuatro pruebas cubren base completa, recurrencia, direcciones/normas,
reproducción Decimal80/100 de los 256 intervalos y sus SHA, proyecciones
sobre las 8.192 predicciones anteriores, almacenamiento, entradas y alcance.
No se repite la suite histórica.

```
python tools/loudness_latch_bdf_static_precision_memory_basis.py
python tools/validate_bdf_static_precision_memory_basis.py
```
