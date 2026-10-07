# Puerto pasivo nativo del mezclador: protocolo

2026-10-07. Bloque independiente del banco monolítico de 350 ms pendiente.
Fuente: [transcripción del panel](../evidence/mixer_panel_bus.json), SVC-9
Fig. 9-17, p. 19 (SVC-204D p. 75), y Fig. 9-11 p. 13 para pin 4/C27.
Continúa la [referencia pasiva](MEZCLADOR_PANEL.md). No produce audio.

## Dominio y contrato

Seis terminales, en orden OSC1, OSC2, OSC3, NOISE, EXT, BUS; masa común
eliminada. Corrientes positivas entrando a la red pasiva. Cuatro cursores
son fracciones eléctricas desde masa, no taper ni posiciones de perilla.
Las rutas incluidas están en ON. Omitir una ruta excluye su subgrafo:
no modela contactos OFF ni sus cargas. Red vacía permite un stamp cero,
pero no permite resolver un bus flotante mediante corriente impuesta.

R6/R7/R8/R10 = 25 kΩ. R45/R47/R49/R46 = 33 kΩ; R48 = 11 kΩ.
En una rama con potenciómetro, α∈[0,1], P=25 kΩ, S=resistor de serie:

```
D = S + P α (1−α)
Yss = 1/P + α²/D; Ysb = Ybs = −α/D; Ybb = 1/D
```

Sale de eliminar el cursor de los tres resistores conservando masa y
cargas de ambos terminales. D≥S>0: no usa 1/α ni 1/(1−α), ni epsilons
de contacto. Los extremos son contactos ideales exactos. EXT tiene
matriz [[1/S,−1/S], [−1/S,1/S]]. Los cinco subgrafos se suman en BUS.

Entregar matriz de admitancia 6×6, seis corrientes, disipación y, como
control condicionado, Vbus ante cinco voltajes y corriente de placa
impuesta. Esa corriente es positiva saliendo de BUS hacia placa 4.
Entregar derivadas de Vbus y corrientes de fuentes respecto de las cinco
tensiones y de esa corriente. No incluir memorias, fuentes inventadas,
ganancia de audio, impedancias de generadores ni ley dinámica de C27.

Rechazar entradas no finitas, α fuera de dominio y overflow aritmético.
Conservar amplitud/signo; no saturar ni reemplazar un fallo por cero.
Constructor y evaluación usan arrays fijos, sin I/O o heap.

## Contraste antes de integrar a la voz

Construir un oráculo nodal independiente de resistores: cursores interiores
como incógnitas y extremos mediante unión exacta a fuente/masa. Eliminar
sus nodos con 80 dígitos y conservar ecuaciones/corrientes, no reutilizar
la fórmula reducida de Rust para generar el resultado esperado.

Cubrir los 31 subconjuntos no vacíos y nueve perfiles de α: ambos extremos,
vecindades 10⁻⁹, centros y cursores diferentes. Voltajes y carga de placa
son fronteras de laboratorio. Gates fijados:

- admitancias y tangentes de corriente: 10⁻¹⁵ S;
- voltajes y tangentes de Vbus: 10⁻¹⁰ V o V/V, 10⁻⁹ Ω para dV/dI;
- corrientes, KCL y sensibilidad dI/dI: 10⁻¹⁴ A o 10⁻¹² A/A;
- potencia: 10⁻¹³ W; simetría: 10⁻¹⁵ S;
- cero asignaciones durante 10000 evaluaciones.

Contrastar matriz completa, corrientes en ambos lados y disipación, solución
de bus y todas las tangentes con el oráculo nodal. Comparar Vbus, coeficientes
y corrientes del bus con la referencia Python anterior; registrar también
su matriz de dos puertos como diagnóstico de aritmética, sin utilizarla
como raíz de referencia del nuevo stamp. Probar explícitamente la carga al bajar
un cursor, peso triple de ruido con todos arriba, extremos representables,
bus flotante y rechazos. Registrar stdout/stderr, toolchain y hashes antes/
después; preservar todo fallo. Esta admisión sólo cubre la red estática ON
nominal. C27/ladder, fuentes cargadas, OFF, nativo VCO y RT siguen pendientes.
