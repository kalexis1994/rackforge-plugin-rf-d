# BJT intrínseco con carga conservativa: alcance condicionado

## Contrato eléctrico

Se cierra una primera hipótesis dinámica de tres terminales **B/C/E** en `tools/bjt_charge_reference.py`. No tiene parámetros físicos por defecto. La referencia SVC-9 y la revisión CA3046 objetivo no cambian; la identificación de Q25/Q15 permanece abierta.

Se deriva el subconjunto intrínseco de NG46: `qb=1`, tiempos TF/TR constantes, `XTF=PTF=0`, `XCJC=1`, sin resistencias internas, Early, alta inyección, fugas adicionales o sustrato. El transporte y la depleción se mantienen explícitos; el subconjunto permite ambas junturas en conducción directa, sin afirmar que representa toda la carga real en saturación.

Con `p=+1` NPN / `−1` PNP, `vBE=p·(VB−VE)`, `vBC=p·(VB−VC)`, corrientes orientadas `F=Is·expm1(vBE/sBE)` y `R=Is·expm1(vBC/sBC)`:

```text
IB = p·(F/βF + R/βR)
IC = p·[F − R·(1+1/βR)]
IE = −IB−IC
QBE = QdepBE(vBE) + TF·F
QBC = QdepBC(vBC) + TR·R
QB = p·(QBE+QBC), QC = −p·QBC, QE = −p·QBE
```

Las [primitivas de depleción](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) conservan continuidad y Q(0)=0. Corrientes en A, cargas en C, TF/TR en s, β adimensional y escalas de emisión en V. Cada escala `s=n·VT` es argumento obligatorio. La guardia exponencial 45 es numérica; parámetros y voltajes deben ser finitos.

La matriz terminal de carga, con `cBE=dQBE/dvBE` y `cBC=dQBC/dvBC`, es:

```text
C = [ cBE+cBC  −cBC  −cBE ]
    [ −cBC      cBC    0  ]
    [ −cBE       0    cBE ]
```

Sus filas y columnas suman cero, es simétrica y semidefinida positiva en este alcance. La corriente DC puede suministrar ganancia; la pasividad de esta matriz no implica pasividad del transistor completo. El modo común no altera cargas ni corrientes.

## Memoria temporal

El historial inmutable guarda QBE/QBC orientadas y el conjunto completo de parámetros. Euler hacia atrás añade `ΔQterminal/dt` a la corriente DC y `C/dt` a su Jacobiano. La evaluación entrega un candidato; el caller publica sólo después de aceptar el circuito completo.

Cambiar parámetros, polaridad o ley mientras se mantiene el historial se rechaza. Preparar carga desde voltajes declarados es posible; seleccionar esos voltajes como estado inicial físico requiere resolver el circuito. Un paso rechazado no modifica memorias. No hay política de rama por tiempos, contador ADSR o número de iteraciones.

## Contraste ejecutable independiente

Se adquiere el ngspice 46 portátil de la distribución oficial, fuera de Git. El tag oficial se verifica con `git ls-remote`: `ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6`. Los hashes de fuentes, archivo 7z y ejecutable están en [FUENTES](FUENTES.md).

El [informe](../evidence/bjt_charge_ngspice_probes.json) cubre **72 casos**: doce sesgos Q25/Q15 más seis escenarios elementales, NPN/PNP y dos perfiles de tránsito. Cada caso mide corrientes DC, cargas de junturas, capacitancias y la **matriz AC completa 3×3** a 1 kHz y 1 MHz mediante tres excitaciones terminales independientes. Son **360 comparaciones** con gates declarados antes de ejecutar.

Parámetros exclusivamente sintéticos: Is=10⁻¹⁴ A, βF=100, βR=5, Cj0BE=7 pF/VjBE=0,75 V/mBE=0,5, Cj0BC=5 pF/VjBC=0,7 V/mBC=0,33, FC=0,4; TF/TR=0/0 o 1/3 ns. No son una identificación 2N3392. TEMP y TNOM se fijan en 25 °C.

ngspice conserva constantes térmicas anteriores a las SI exactas utilizadas aquí. Se declara la correspondencia `NF/NR=1,0000003394239112` en el netlist para comparar **la misma escala de emisión**; no se modifica la temperatura ni la constante SI de RF-D. ngspice continúa la corriente inversa con una cola cúbica por debajo de −3·nVT; RF-D conserva Shockley. Esa diferencia se registra y queda dentro de los gates absolutos de este experimento.

| Cantidad | Gate absoluto + relativo | Máximo absoluto observado |
| --- | --- | ---: |
| Corriente | 2×10⁻¹⁴ A + 10⁻⁷·abs(I) | 2,48×10⁻¹⁷ A |
| Carga | 10⁻²⁰ C + 10⁻⁷·abs(Q) | 2,37×10⁻²⁶ C |
| Capacitancia | 10⁻¹⁹ F + 10⁻⁷·abs(C) | 4,01×10⁻²⁵ F |
| Admisión AC compleja | 10⁻¹² S + 10⁻⁷·abs(Y) | 4,10×10⁻¹⁶ S |

Todos pasan; máximo cociente error/gate **0,001218**. Esto verifica implementación bajo la hipótesis declarada, no identidad sonora.

Cinco regresiones regeneran todas las comparaciones desde los exports guardados, verifican las nueve derivadas DC/carga/temporal por FD, KCL terminal, invariancia de modo común, rango/pasividad restringida y memoria intacta ante rechazo/reparametrización.

Para regenerar con el binario adquirido:

```powershell
python tools/bjt_charge_ngspice_probes.py --ngspice references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe
python -m unittest discover -s tests -p test_bjt_charge.py -v
```

El harness verifica versión y SHA del ejecutable, usa procesos sin ventana, conserva logs/decks/tablas ignorados y borra únicamente sus exports anteriores antes de cada corrida para impedir resultados viejos. La ruta de exportación `wrdata` de este harness requiere ausencia de espacios/caracteres de control. No altera instalaciones globales ni añade dependencias al plugin.

## Pendiente

El contraste temporal de un circuito cargado con memoria propia se completa en [BJT cargado: transitorios](BJT_CARGADO_TRANSITORIOS.md). Sigue pendiente estudiar conmutación del contorno bajo hipótesis explícitas, incluyendo qué efectos omitidos son necesarios. Parámetros físicos, partición más completa, alta inyección, recuperación física, resistencia de base y dispersión siguen abiertos. Ninguna carga nueva incorporada a la voz nativa, ningún deadline ni audio admitido.
