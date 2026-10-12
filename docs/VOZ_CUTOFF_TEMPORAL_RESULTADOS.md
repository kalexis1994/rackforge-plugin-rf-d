# Cambio temporal del cutoff con carga real de VCO

2026-10-12. Model D CA3046 nominal, R61=200 Ω, RANGE=0,1, VCAs=2 V.
OSC1 ON por panel SW6, alpha=0,5; otras entradas OFF.
[Contrato previo](VOZ_CUTOFF_TEMPORAL_PROTOCOLO.md),
[inputs](../evidence/voice_cutoff_temporal_inputs01.json),
[nativo](../evidence/voice_cutoff_temporal_native01.json),
[oráculo](../evidence/voice_cutoff_temporal_reference01.json),
[QA](../evidence/voice_cutoff_temporal_tests01.json).

La apertura cutoff0,5→1 se aplica a la raíz de memoria del candidato a=1,
por bytes, en t=0. No se prepara un nuevo DC ni se cambian cargas, trims
o componentes. Cambia el equivalente eléctrico del panel documentado,
incluida su impedancia según la posición. Cada paso resuelve VCO/BUS,
filtro y salida juntos. El estado entrante no se presenta como DC de la
nueva fuente. La receta de parámetros acompaña al codec de estado.

Cuatro perfiles hasta250 µs, con pasos propios y checkpoints a2/16/64/125/250 µs.
Los nominales coinciden por bits en400 coordenadas a2 µs con el banco anterior.
A250 µs coinciden bajo gates, con diferencias≈1e−14 V/A de representación;
no se afirma identidad por bits de ese final. Dos restores por perfil,
en0/64 µs, verifican estados/incrementos por bits y ratios/relojes/h/intentos.

## Efecto medido

| Cutoff | Máximo h ns | C18 final V | Cola final µA | J7 final V | J7 min→max muestreado V |
|---|---:|---:|---:|---:|---:|
| 0.5 | 125 | 0.000122528823873 | 6.82489850903 | 3.3837725939e-05 | 5.20248666373e-05 |
| 0.5 | 62.5 | 0.000122528823873 | 6.82489850903 | 3.3837725939e-05 | 5.20247325367e-05 |
| 1.0 | 125 | 0.090267732454 | 144.421881342 | 0.00272926811477 | 0.00273133548874 |
| 1.0 | 62.5 | 0.090267732454 | 144.421881342 | 0.00272926811493 | 0.00273133548891 |

C18 cambia≈90,145 mV y la cola alcanza≈21,161 veces el nominal.
J7 final cambia≈2,695 mV. El rango muestreado de J7 aumenta≈52,5 veces
en esta ventana, coherente como hipótesis con el diagnóstico AC anterior.
No comparar ese rango transitorio con amplitud de un ciclo ni inferir54×
para una nota. Se admite el efecto eléctrico por el criterio previo:
ΔC18≥1 mV y aumento de cola≥1 %, en ambas resoluciones.

## Conservación y auditor independiente

72 candidatos/28800 ecuaciones, 48 observaciones de corrientes VCO y24 LTE.
Se hereda el código del auditor VCO Decimal100 y se crean funciones con
globals propios para la KCL de la cadena bajo cada cutoff. Los módulos
anteriores no se mutan. La cadena mantiene sus FD centrales1 µV, masa,
fuentes, R14 y gates. No hay nueva búsqueda independiente de raíces.

C18=100 pF: se integra la KCL estática de cada etapa con pesos Radau3/4,1/4;
ΔQ+∫I_DC pasa≤1e−12 A·duración en los cinco relojes. Estas integrales son
nativas, no una nueva cuadratura independiente de todas las etapas.
Los checkpoints verifican C18 y cola por estados completos. C1/BUS/C18
KCL≤1e−12 A, balance C1≤0,002; carga C27 y medias de panel conservan gates.
Estados al mismo reloj:2 µV/2 nA, sin cambios del criterio por efecto de control.

Nativo 190.595793 s, auditor 18.948925 s,
salidas 7466637 bytes. Cuatro procesos seriales,
stack32 MiB, reserva1 GiB, estimación32 MiB. Todos completos, sin fallos ni
replays de rechazo. Biblioteca/compilador congelados y248 tests heredados
por identidad; sin nueva biblioteca, audio, SPICE, fidelidad física o RT.

La ventana no contiene resets ni un ciclo completo. El siguiente bloque
extiende sólo los perfiles abiertos desde sus checkpoints finales exactos,
con todos los balances y contraste temporal, antes de preparar escucha.
