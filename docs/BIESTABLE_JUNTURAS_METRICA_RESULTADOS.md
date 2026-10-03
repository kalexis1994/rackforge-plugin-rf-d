# Métrica cuadrática fija de junturas: prueba y comparación completa

## Candidato y certificado fijados

El [protocolo](BIESTABLE_JUNTURAS_METRICA_PROTOCOLO.md), helper y productor
se congelaron en `0716b5c` antes de medir. Se evalúan los ocho casos,
sin escoger otra métrica tras observar resultados. Los parámetros de
circuito, pesos W, seis grupos físicos y celdas anteriores no cambian.

Cada intervalo produce un único candidato desde el centro del hull de
sus ocho recintos B_JJ, con escala temporal positiva y redondeo diádico
nearest-even de 40 bits. Se resuelve CᵀP+PC=-I racionalmente, se exige
positividad estricta, se normaliza traza a cuatro y se redondea P.
La prueba y conversiones usan el P final, cuya LDLᵀ se verifica otra vez.
Las **ocho resoluciones candidatas** son de métrica numérica; no son
nuevas inversas o solves no lineales del circuito.

Se aceptan seis candidatos; **reset N2/N4 se rechazan** por P no positiva
definida. Se archivan solución y pivote rechazado. No se regulariza,
no se busca otro candidato y no se produce una propagación nueva de reset.
La [base de Lyapunov de Stanford EE363, Lecture 13](https://ee363.stanford.edu/archive/lectures/lq-lyap.pdf)
explica la ecuación y la condición cuadrática en las páginas 13–2 a 13–4.
El centro sólo diseña el candidato; no certifica la familia temporal.

Para cada celda aceptada se forma el recinto firmado
S=(PB/rho+(B/rho)ᵀP)/2. Su centro C_S y radio dan
S<=C_S+delta*I, delta=max_i sum_j Rij. Las 32 bisecciones y LDLᵀ racional
prueban alpha*P-C_S-delta*I positiva definida. Entonces
mu_P(B)<=rho*alpha para toda la celda, con incertidumbre incluida.
Se archivan **48 certificados y 1.584 consultas LDLᵀ** de tasa.
El extremo inferior del bracket pertenece al problema auxiliar con delta*I;
**no es un inferior de la medida logarítmica real**.

## Contracción interna y conversiones

P es constante en las ocho celdas de cada intervalo: no existe P'(t)
dentro de ese intervalo. Las **32 celdas de prefijo y cola** certifican
contracción del bloque interno variable en esta métrica, con entradas
externas separadas. Las 16 de ataque no obtienen una tasa negativa.
Que su superior sea positivo no prueba crecimiento real en la nueva norma.
La métrica no es común a los ocho intervalos no contiguos; una unión
futura debe convertir sus anclajes y normas en los límites correspondientes.

u_J=sqrt((W_J e_J)ᵀP(W_J e_J))/(2a), con a exterior calculado del máximo
racional de los **16 vértices** de signos. Así u_J<=||W_J e_J||infinito
para el anclaje común. La norma dual usa P^-1 exacta, y todas las raíces
son exteriores de 256 bits. Se recomputan acoplamientos en ambas direcciones,
forzamiento L1 por columnas y las 94 ganancias nodales. Los otros cinco
bloques y términos directos permanecen idénticos. Las inversas Neumann
se reconstruyen y sus certificados coinciden exactamente con los anteriores.

Los seis grupos se propagan con núcleos de extremo y pico exteriores,
anclaje inicial de unos y forzamiento tardío. No se mezclan medidas de
normas distintas ni se intersectan variantes retrospectivamente.

## Comparación completa

Las cotas forzadas usan anclaje cero **hipotético**. El coeficiente del
anclaje común se conserva; estas cifras no son errores observados del DAE.

| Ventana | N | Mayor tasa superior nueva (1/s) | Forzado espectral anterior (V) | Forzado cuadrático nuevo (V) | Coeficiente de anclaje nuevo |
| --- | --- | --- | --- | --- | --- |
| prefix | 2 | -1,98006911325e7 | 2,97828174890e-6 | 6,41872359122e-6 | 1758,21341958 |
| prefix | 4 | -1,98138588773e7 | 5,78532725532e-6 | 5,78532726688e-6 | 589,543782934 |
| attack | 2 | 5,06846640812e10 | 1,02221975734e114 | 8,27052383020e609 | 5,24543155662e618 |
| attack | 4 | 1,25081030396e10 | 1,26757413857e52 | 3,67801677017e70 | 3,41488430531e80 |
| reset | 2 | candidato rechazado | 3,67506765972e-6 | sin propagación nueva | sin coeficiente nuevo |
| reset | 4 | candidato rechazado | 4,86537697199e-7 | sin propagación nueva | sin coeficiente nuevo |
| tail | 2 | -5,25766470257e6 | 5,33904987470e-6 | 5,33902713709e-6 | 589,543782955 |
| tail | 4 | -5,26895981963e6 | 9,92152195776e-6 | 9,92152208337e-6 | 341,381585581 |

Sólo cola N2 baja, ~22,74 pV. Cola N4 sube ~0,126 pV; prefijo N4
sube ~0,012 pV, y prefijo N2 y ataque empeoran claramente. No se promueve
esta variante por la contracción interna aislada ni se ocultan conversiones.
La tabla anterior conserva también reset sin reutilizarlo como resultado nuevo.

El condicionamiento infinito ||P||infinito*||P^-1||infinito de ataque ronda
**2,315e4**. La incertidumbre isotrópica delta*I se amplifica en el problema
generalizado. En la primera celda de ataque el bracket auxiliar es
estrictamente positivo y su ancho físico tras 32 bisecciones es ~33,31/s
(N2) y ~15,10/s (N4), frente a tasas superiores de 5,06e10/s y 1,25e10/s.
Una bisección más precisa de este mismo problema auxiliar no basta para
hacerlo negativo. Esto orienta un certificado con perturbaciones dirigidas;
no demuestra inexistencia de otra métrica o una tasa positiva real del circuito.

## Evidencia y validación

[Datos](../evidence/loudness_latch_bdf_static_precision_junction_metric.json.gz):
**6962547 bytes**, SHA comprimido
`ffd54f507b96f443755f13ea664c8181f42b98c95840b8ddc404d6e3057ffd9a`,
SHA canónico `4e40205153c6e978d1a05967a52969c5db2aff229d272216adbfabdf79638a4c`.
[Resumen](../evidence/loudness_latch_bdf_static_precision_junction_metric_summary.json).
Incluye candidatos aceptados/rechazados, métricas e inversas, vértices,
normalización de anclaje, tasas, conversiones, kernels y comparación previa.

La [suite](../tests/test_loudness_latch_junction_metric.py) pasa **7/7 al primer intento**,
105.6921072 s. Comprueba ecuación
Lyapunov exacta, redondeo, P^-1, familias intervalares y vértices, norma y dual,
conversiones de entrada/salida/forzamiento, un bloque no normal contractivo
en la métrica y una familia Hurwitz con candidato común rechazado.
Reconstruye todos los candidatos, 48 tasas, inversas, conversiones y
propagaciones; preserva las componentes ajenas al bloque de junturas.
El [recibo](../evidence/loudness_latch_bdf_static_precision_junction_metric_validation.json)
conserva el intento y SHA antes/después idénticos.
El [corpus ampliado](BIESTABLE_JUNTURAS_METRICA_ENTRADAS.md) reconstruye fuentes.

**1 mV global sigue abierto:** anclaje, restos no lineales y recorrido
completo siguen pendientes. No se certifica contracción del sistema acoplado,
fidelidad física, sonido o deadline. Próximo corte: perturbación dirigida y
congruencia racional del certificado de tasa, con la misma P y conversiones.

```powershell
python tools/loudness_latch_bdf_static_precision_junction_metric.py
python tools/validate_bdf_static_precision_junction_metric.py
```
