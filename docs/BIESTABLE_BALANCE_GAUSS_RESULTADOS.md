# Balance integrado: resultados de la variante Gauss

Protocolo/productor fijados en `bfef51b`, el 2 de octubre de 2026.
Gauss-Legendre 4/8/16 conserva el problema, leyes condicionales,
dominios, cargas, puente y gates del [informe Simpson](BIESTABLE_BALANCE_CARGA_RESULTADOS.md).
No se ejecuta un nuevo paso del circuito ni se cambia su controlador.

Los **496 intervalos** y el soporte mixto pasan el contraste final **8/16**,
el cierre de cargas por piezas, precisión Decimal80/100 e identidades.
También pasan 4 frente a 16 en los 496 intervalos. Las 28 raíces escalares
de Legendre se conservan con nodos, pesos, presupuesto e iteraciones;
sus **112 momentos** pasan a las dos precisiones. Estas raíces pertenecen
a la cuadratura; hay **cero solves nuevos del circuito**.

Simpson64 frente a Gauss16 pasa en **225/496** casos y conserva **271 fallos**.
Los 371 fallos de Simpson32/64 permanecen en su informe original.
La variante resuelve el contraste de cuadratura sin relajar componentes
pequeñas ni modificar los datos que revelaron el límite del primer método.
La concordancia Gauss tampoco es una cota certificada del resto.

## Balance medio condicionado

El residual constitutivo medio queda bajo 10 pA en **105/496** intervalos;
se conservan **391 incumplimientos**, igual cobertura que el diagnóstico
Simpson64. Los máximos medios Gauss16 son:

| Ventana | Dos subpasos (A) | Cuatro subpasos (A) | Intervalos bajo 10 pA, 2/4 |
| --- | ---: | ---: | ---: |
| Prefijo | 6,11115649195e-11 | 1,55268841204e-11 | 0/43 |
| Ataque | 3,52891693342e-8 | 8,81308470189e-9 | 0/0 |
| Reset | 2,56358966427e-11 | 6,41600024044e-12 | 0/62 |
| Cola | 2,24806590035e-10 | 5,62944669488e-11 | 0/0 |

Cada nivel tiene 62 intervalos. Usar Q(v) coherente no elimina este
residual del circuito reconstruido. Un balance firmado puede ocultar
cancelaciones; tampoco mide error de voltaje ni cubre el recorrido desde DC.

El soporte mixto conserva dos piezas y un puente. Su comparación
Simpson64/Gauss16 pasa (0,00309912 normalizado). No se elige una raíz
aproximada para dividir la carga dentro del bracket ni se modifica el knee.

## Pruebas, archivo y alcance

**Cuatro pruebas**, primer intento, **14,2683057 s**; hashes antes/después
idénticos. Cubren reglas/momentos, los 496 balances y soporte mixto,
24 verificaciones mediante Gauss4 de fórmula cerrada independientes del
Newton de Legendre, replays seleccionados a ambas precisiones y conservación
del informe y primera fuente de prueba fallida de Simpson.

[Datos](../evidence/loudness_latch_bdf_static_precision_charge_gauss.json.gz):
12.790.268 bytes; SHA comprimido
`8fa71e4a97e4913e4c1144ae5ed416b28d961daba1961957c46d21ed4363b93a`;
SHA canónico
`c8c35c3c25f93a76056384172802c044fe0a93b8cc4281cf6088997aec935db6`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_charge_gauss_summary.json)
y [recibo](../evidence/loudness_latch_bdf_static_precision_charge_gauss_validation.json)
conservan las fuentes y observaciones completas.

Siguiente corte: cota del resto de cuadratura y magnitud/propagación del
residual, antes de convertir un balance firmado en error global. Este
contraste no admite física, audio, deadline ni el criterio global de 1 mV.
