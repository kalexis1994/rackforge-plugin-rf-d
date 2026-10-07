# JFET nominal E402: canal y cargas nativos

2026-10-07. Pasó el [protocolo previo](VCO_JFET_NOMINAL_PROTOCOLO.md).
Una mitad NJF, B=1, TEMP=TNOM=25 °C, terminales [D,G,S].
Valores de [la tarjeta condicionada](../evidence/vco1_laboratory_devices.json),
sin identificar población física, mismatch o otras temperaturas.

## Núcleo

Canal con corte, zona lineal y saturación; inversión de drenador/fuente y
derivadas físicas completas. Junturas GS/GD con continuación inversa del
oráculo y GMIN operativo. Cargas de depleción con incrementos estables,
historia fija, candidato sin publicación. Ninguna difusión JFET añadida.

La inversión orienta el canal al extremo de menor voltaje. Las cargas
siguen en GS/GD: 3.3 pF y 5.4990908339470075 pF nominales. La simetría DC
se verifica por permutación D/S; la asimetría transitoria queda preservada.
BJT y primitiva de depleción anteriores permanecen sin cambios.

## Contrastes

[Decimal100](../evidence/voice_vco_jfet_vectors01.json): 2028 vectores,
13×13 biases, dos gates comunes, tres historias y dt125/500 ns. Veinte
vecinos adicionales, con gate relativo sin piso para ΔQ no nula.
La referencia usa ramas/incidencias y un polinomio de canal independiente.

| Valor | Diferencia máxima contra Decimal100 |
|---|---:|
| Corriente DC/Euler | 1,2434497876×10⁻¹⁴ A |
| Carga terminal | 1,2924697071×10⁻²⁶ C |
| Jacobiano DC/Euler | 4,5474735089×10⁻¹³ S |
| Derivada de carga | 1,6155871339×10⁻²⁷ F |
| ΔQ de juntura | 3,2311742678×10⁻²⁷ C |

Gates absolutos más relativos aplicados por valor. Pasaron las nueve
entradas de los Jacobianos por FD, gauge, conservación de tres terminales,
historia fija/igual, inversión, capacitancias físicas y rechazos de dominio.
[Producción](../evidence/voice_vco_jfet_native01.json): tres tests eléctricos
y uno aislado de heap, 10.000 stamps completos con cero asignaciones.
Fuentes, compiler, comandos y tres binarios conservados. No acredita RT.

[Ngspice46 independiente](../evidence/voice_vco_jfet_spice01.json): doce
escenas con DC, cargas finales de bias constante y AC1kHz por tres
excitaciones. Todas admitidas, sin fallos/replays; diferencia máxima
nativo/AC **1,0842021725×10⁻¹⁹ S**. En cada escena, el transitorio de
250 ns llega a su final y conserva voltajes impuestos; no es un VCO.

En MODEINITSMSIG, @j[qgs]/[qgd] retorna la capacitancia almacenada en ese
slot, a pesar de su etiqueta de carga. El export de Q se hizo después del
transitorio y antes de AC; el export de C después de AC. La QA vuelve a
leer los archivos y logs privados para verificar cantidades, unidades,
cobertura y contrastes. Doce procesos SPICE, sin audio nuevo.

## Admisión y siguiente cierre

La [QA de publicación](../evidence/voice_vco_jfet_tests01.json) reconstruye
el banco Decimal, coteja los exports SPICE y conserva todos los algoritmos,
gates y datos anteriores. **205 controles: cuatro ejecutados y 201
heredados por identidad.** El [snapshot](../evidence/voice_vco_jfet_documentation01.json)
guarda las tres portadas previas por bytes exactos.

Quedan los estados y leyes internos del 741 y el stamp nodal completo del
VCO. Las dos mitades E402 deberán compartir su fuente en ese circuito,
sin atribuir matching físico a la tarjeta común. VCO autónomo y acoplamiento
cargado requieren su propia referencia. No amplía fidelidad física, voz
instalable, deadline o la campaña larga rechazada.
