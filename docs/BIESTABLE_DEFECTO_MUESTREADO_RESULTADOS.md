# Diagnóstico de diferenciación sobre cargas publicadas

El [protocolo](BIESTABLE_DEFECTO_MUESTREADO_PROTOCOLO.md) y
[productor](../tools/loudness_latch_bdf_static_precision_charge_proxy.py)
quedaron congelados en **`d4b3230`**, antes de medir, el 2 de octubre de 2026.
Usan las referencias propias de 2/4 subpasos ya archivadas; **cero solves
no lineales nuevos**, ningún cambio al integrador o controlador.

## Cobertura y resultados

Se conservan **496 puntos**: índices gruesos 2..63 de ambas referencias
en las cuatro ventanas. Los índices 0/1 quedan excluidos expresamente
porque los dos predecesores gruesos deben ser muestras de la misma
continuación fina. Se usan las cargas guardadas: 21 C*vc compensados y
cuatro QBE/QBC. El voltaje de C10 es su memoria interna, no el de terminales.

Todos los puntos pasan preparación/evaluación Decimal80/100,
descomposición de los tres operadores y conservación incluyendo los
terminales fijos. El interpolante cúbico de las últimas cuatro muestras
finas aproxima Q'; el cuadrático de tres ofrece un contraste adicional.
Estas derivadas reciben estados numéricos, no una solución exacta del DAE.

| Ventana | Máximo defecto aproximado, 2 subpasos (A) | 4 subpasos (A) | Máxima diferencia 4 menos 2 (A) |
| --- | --- | --- | --- |
| Prefijo | 2,41710e-10 | 2,42705e-10 | 3,76096e-12 |
| Ataque | 1,43043e-7 | 1,40958e-7 | 3,50590e-9 |
| Reset | 9,88970e-11 | 9,89249e-11 | 6,23164e-13 |
| Cola | 8,98189e-10 | 8,98577e-10 | 5,20661e-12 |

Se separan `Dclock Q - Q'_cubico`, `(Dcommand-Dclock)Q` y
`(Dbinary-Dcommand)Q`. Máximo término de reloj **2,09840e-13 A**;
máximo término de coeficientes **9,39194e-20 A**. Son máximos de esta
selección y coordenadas, sin atribuirles el error temporal global.
Dos registros de ataque (el mismo reloj grueso bajo ambas referencias)
tienen razón de timestamps apenas >2. El interpolante matemático sigue
definido; no se lo presenta como un solve que admite esa razón. Los
intervalos comandados conservan el dominio <=2.

La mayor componente de esta selección es la carga de **C2**, índice
grueso 21 con dos subpasos, en **0,002422375488281306 s**. Identificar
ese máximo no atribuye a C2 por sí sola la brecha global de trayectoria.

El mapeo de la aproximación a KCL usa incidencias y beta; la publicación
RC serie añade z=R*beta*tau. Su máximo aquí es **5,54896e-21 V**.
No se compara con el forzamiento relativo del bloque anterior como si
fuese la misma magnitud. beta deriva del h/a0 racional levantado;
se conserva la diferencia frente al dt_eff redondeado del kernel.

En ataque, la máxima diferencia cúbico menos cuadrático de Q' es
**4,40456e-8 A** con dos subpasos y **9,21149e-9 A** con cuatro.
Las diferencias entre reconstrucciones y mallas no certifican el error
absoluto de Q'. La precisión aritmética del cálculo no hace exacto este
defecto aproximado ni justifica usarlo todavía para controlar el paso.

## Reproducción y alcance

[Datos](../evidence/loudness_latch_bdf_static_precision_charge_proxy.json.gz):
2.102.282 bytes; SHA comprimido
`939384e463f3103098f80c138b8326ce2395adf20e2cdd82a90c362199c8879b`;
SHA canónico
`d94d8680025dfdb3c294ce71d7981fb2ccc9cf47c8f64d13a804ee1ba9dc6b70`.
El [resumen](../evidence/loudness_latch_bdf_static_precision_charge_proxy_summary.json)
conserva **163 entradas**, máximos de cada término, cobertura y gates.
El [recibo](../evidence/loudness_latch_bdf_static_precision_charge_proxy_validation.json)
registra **4/4 pruebas**, primer intento, **15,3063527 s**, SHA antes/después
idénticos. La [suite](../tests/test_loudness_latch_bdf_static_precision_charge_proxy.py)
verifica momentos cardinales, tiempos, origen, toda la reproducción
Decimal80/100 y **24 replays racionales independientes** de cargas,
operadores e incidencias RC. Conserva todas las diferencias 4 menos 2.

```powershell
python tools/loudness_latch_bdf_static_precision_charge_proxy.py
python tools/validate_bdf_static_precision_charge_proxy.py
```

No hay estimador independiente ni cota de Q''' durante conmutación,
arranque, error entre muestras o trayectoria completa desde DC. El gate
global de **1 mV**, identificación física, audio y deadline permanecen
abiertos. Siguiente contraste: reconstrucción de la tasa de carga frente
a ecuaciones continuas, manteniendo aparte el error de los estados finos.
