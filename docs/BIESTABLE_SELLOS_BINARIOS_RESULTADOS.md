# Sellos analíticos binary64: resultados

El [protocolo previo](BIESTABLE_SELLOS_BINARIOS_PROTOCOLO.md) y ambos
productores se fijaron en `c32d7a4`. Se completan los ocho contrastes
estáticos y solves J94/B. Todas las corrientes pasan 10 pA, con diferencia
máxima de 1,42357×10⁻¹⁷ A frente a Decimal80; las ocho derivadas pasan
10⁻³⁰ S + 10⁻⁸|JDecimal|. Todos los solves racionales y sus mapas redondeados
pasan ambos gates algebraicos de 10⁻¹⁰ (máximo 1,67525×10⁻¹⁶).

## Mapas y redondeo de recíprocos

El gate de mapa es 10⁻⁸; la referencia es el mapa analítico Decimal80:

| Ventana | Recíproco ordinario | Recíproco compensado |
| --- | --- | --- |
| Prefijo | 4,34890×10⁻¹⁵ | 4,49148×10⁻¹⁵ |
| Ataque | 2,25694×10⁻¹⁴ | 2,25694×10⁻¹⁴ |
| Reset | **6,74262×10⁻⁷ — falla** | **2,23922×10⁻¹⁴ — pasa** |
| Cola | 1,42512×10⁻¹⁴ | 1,42512×10⁻¹⁴ |

Pasan 3/4 mapas ordinarios y **4/4 compensados**. Las dos rutas evalúan
las mismas corrientes y dispositivos; cambia únicamente la preparación y
acumulación de los recíprocos en el Jacobiano. Se guardan todos los fallos.

La preparación compensada levanta la resistencia binary64 a fracción
exacta, guarda high y el resto low redondeado, y registra el resto que
high+low todavía omite. La evaluación posterior usa sólo binary64,
`math.exp`, `math.expm1` y sumas `fsum`. No se ejecuta Decimal ni eliminación
racional de resistencias durante esa evaluación. El solve racional JX=B
sigue siendo el auditor fuera de tiempo real.

En reset, una inspección posterior observa una diferencia de **un ULP**
en componente estática (27,27): 0,0010000000001604051 S ordinario frente
a 0,001000000000160405 S compensado. En las otras tres ventanas esa
componente coincide. Existen otras diferencias de componentes entre rutas;
no se afirma que esa entrada aislada explique todo el mapa sin una sonda
causal adicional. La sensibilidad obliga a comprobar los mapas, incluso
cuando ambos Jacobianos pasan su gate componente a componente.

La ruta compensada aún difiere de Decimal80 en 160, 165, 156 y 156 de los
4356 componentes estáticos. No se exige identidad binaria universal:
los cuatro contrastes de mapa pasan el gate fijado pese a esas diferencias.
No se cambia el gate para admitir el ordinario fallido.

## Datos reutilizados y regresiones

Los **48 contrastes de predicción** pasan el gate de 10 nV + 10⁻³|pred|,
con máximo normalizado 0,000148462. Son los mismos 24 contrastes centrales
de 48 solves hipotéticos del corte Decimal, evaluados con dos mapas;
**cero solves no lineales nuevos**. Su gate más amplio no detecta el
fallo del mapa ordinario de reset y conserva su alcance distinto.

- [Datos completos](../evidence/loudness_latch_bdf_static_precision_binary.json.gz):
  337.674 bytes, SHA256 comprimido
  `93d19161519b4bf94f7116b24d7609335eab20d9de8c219f5e6dbf3a34c364ab`.
- [Resumen](../evidence/loudness_latch_bdf_static_precision_binary_summary.json).
- [Recibo](../evidence/loudness_latch_bdf_static_precision_binary_validation.json):
  **4/4 regresiones**, un intento exitoso, 124 entradas identificadas y
  fuentes sin cambios. Verifica preparación sin alterar el grafo, restos
  recíprocos con fracciones, replay de los ocho solves racionales, los
  contrastes reutilizados y el fallo ordinario de reset.

`python tools/validate_bdf_static_precision_binary.py`

El campo heredado `mixed_value` en las métricas indica aquí la referencia
analítica Decimal80 y `candidate_value` el candidato de la ruta indicada.
El HEAD contextual del productor y validación es `c32d7a4`; el commit de
archivo es posterior y fija las identidades de los resultados.

## Gate siguiente

La ruta compensada pasa sólo estos **cuatro mapas de un intervalo**.
El siguiente corte debe contrastar sus Jacobianos durante ventanas más
largas, luego integrarla en una variante de laboratorio que conserve el
residuo original, sus memorias, clocks y gates de publicación. Registrar
cambios de raíces/voltajes e iteraciones; no sustituir una referencia por
conveniencia. Después repetir el refinamiento temporal desde DC.

El solver original permanece intacto. No se admite una trayectoria nueva,
error acumulado, conmutación física, audio ni deadline; el fallo del mapa
FD original y el gate global de 1 mV permanecen archivados y abiertos.

La [auditoría de entradas](BIESTABLE_PRECISION_ESTATICA_ENTRADAS.md)
reconstruye los 124 SHA del corpus ampliado desde Git y tres archivos
históricos exactos, sin modificar estos resultados numéricos.
