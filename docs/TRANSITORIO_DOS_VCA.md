# Transitorio no lineal hasta el segundo VCA

La [referencia offline de cuarenta nodos](../tools/filter_vca_cascaded_transient_reference.py) une el filtro, recuperación, EMPHASIS, entrada R2/C6/C15 y los **dos VCA activos**. Recalcula veinte transistores por paso: catorce del filtro/recuperador y Q16/Q15/Q18/Q14/Q13/Q21. Los valores y conexiones están trazados a **SVC-9 Fig. 9-11, PDF p. 13, tabla 7-8, pp. 30–31** y **SVC-204D §2.9, PDF p. 12**. Las leyes Ebers–Moll y los parámetros impuestos se describen en el [DC acoplado](VCA_CASCADA_DC.md). La referencia no inventa parámetros de un TIS97 medido.

El estado inicial combina los DC del ladder, recuperador y [quince nodos de ambos VCA](VCA_CASCADA_DC.md). C6_LEFT toma el voltaje DC del colector de recuperación por R2, mientras Q16_BASE/Q15_BASE conservan su sesgo por C6 abierto. Euler implícito conserva las cargas de los capacitores ya presentes en el [transitorio anterior](TRANSITORIO_VCA1_ACTIVO.md), más el estado de C10. Las corrientes de base Q14/Q13 cargan los colectores Q16/Q15 en cada iteración. R13 y R11 distribuyen la corriente de los dos cursores. Se resuelve con Newton amortiguado y diferencias finitas de 40 columnas, deliberadamente **sólo para estudio offline**.

El modelo fija la frontera de voltaje previa a R11 y los controles que excitan Q18 y Q21; Q12/Q17 y la etapa final siguen abiertos **en esta referencia**. Se reportan `V_Q14c−V_Q13c`, las corrientes de base entre VCA y el residuo de KCL/carga. La diferencia de colectores es una señal **intermedia**. La [extensión de 48 nodos](TRANSITORIO_HASTA_SALIDA.md) alcanza los pines de salida con cargas declaradas.

Las [regresiones](../tests/test_filter_vca_cascaded_transient_reference.py) comprueban el punto fijo DC, `I_R2=I_C6`, suma de carga, dos polaridades de BUS, una traza no nula y el límite de pequeña señal contra la [matriz AC de cuarenta nodos](CARGA_AC_DOS_VCA.md) discretizada por Euler. Exigen `<10⁻¹⁰ A` de residuo en los escenarios probados. No prueban estabilidad para todos los parámetros, tiempo real ni semejanza sonora con un Model D. La frecuencia `48 kHz` y los niveles de BUS son estímulos de regresión, no medidas del instrumento.

El siguiente cierre eléctrico es Q12/Q17, Q1, R10 y la carga de salida; después deben trazarse los contornos y el jack EXTERNAL LOUDNESS. Una solución DSP necesitará trabajo separado para tiempo acotado, sin asignaciones ni acceso a archivos durante audio, y comparación con este oráculo.

```powershell
python -m unittest discover -s tests -q
```
