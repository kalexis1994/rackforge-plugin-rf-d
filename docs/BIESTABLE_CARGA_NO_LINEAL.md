# Biestable: carga no lineal y ambigüedad temporal

## Circuito, hipótesis y memorias

Continúa el [BJT conservativo](BJT_INTRINSECO_CARGA_CONSERVATIVA.md), sus [transitorios cargados](BJT_CARGADO_TRANSITORIOS.md) y el [inventario de junturas](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md). Usa las conexiones de Q25/Q15 del grafo SVC-9 Fig. 9-7, página PDF 9, y las cargas reales de la cadena de [94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md). No cambia la revisión documental ni los componentes pasivos.

| Dispositivo | Base | Colector | Emisor |
| --- | --- | --- | --- |
| Q25 | SET_BASE | RESET_COLLECTOR | GROUND |
| Q15 | RESET_BASE | ATTACK_GATE_LOWER | GROUND |

Ambos son NPN en el grafo, marcados 2N3392. **Sus leyes de carga siguen siendo sintéticas**, sin identificación vintage: Is=10⁻¹⁴ A, βF=100, βR=5, T=298,15 K; depleción BE de 7 pF/0,75 V/m=0,5, BC de 5 pF/0,7 V/m=0,33, FC=0,4; perfiles TF/TR=0/0 y 1/3 ns. La implementación exige que la hipótesis de corriente estática coincida con la existente; no suma dos veces la corriente DC.

Por dispositivo se guardan dos cargas orientadas en C, con parámetros ligados al historial. Para cada ensayo del mismo intervalo:

```text
QB = QBE + QBC; QC = −QBC; QE = −QBE
Iextra = (Qterminal(nuevo) − Qterminal(anterior)) / dt
Jextra = (dQterminal/dVterminal)(nuevo) / dt
```

La estampación conserva la matriz terminal completa, incluidos los términos cruzados BC. El emisor a masa conserva su reacción a la fuente; no añade una incógnita artificial. No se aproxima el incremento con C(nuevo)·ΔV.

El estado conjunto conserva **21 historiales de capacitores existentes y cuatro cargas de juntura nuevas**. Los candidatos de todas las memorias se publican después de aceptar KCL y corrección; los ensayos Newton/FD usan el mismo historial entrante. C10 mantiene su resistencia serie de 25,5 kΩ y un nodo interno explícito en el descriptor.

Fuentes ejecutables: `tools/loudness_latch_charge_reference.py` y `tools/loudness_latch_charge_probes.py`. [Informe](../evidence/loudness_latch_charge_probes.json) con hashes, Python/NumPy, parámetros y estado entrante completo. No hay incorporación al motor Rust ni al paquete RF-D.

## Contraste de la matriz de carga

Se estudian **12 escenarios**: R61=200 Ω/200 kΩ × tres raíces anteriores × dos perfiles de tránsito. Se conserva el voltaje de cada raíz anterior para el análisis local; no se lo presenta como equilibrio DC ni como punto de una trayectoria física.

La derivada dQ/dV se contrasta por diferencias centrales de 1 µV sobre todos los nodos. Además, se ensamblan las matrices terminales independientes `Im(Y)/(2πf)` de ngspice a 1 kHz y 1 MHz, provenientes del [contraste ejecutable del BJT](../evidence/bjt_charge_ngspice_probes.json). Cada export corresponde al mismo sesgo BE/BC; su desplazamiento de modo común se verifica explícitamente.

La comparación se aplica al **incremento de masa de las junturas**, evitando que C2=10 µF o las cargas de audio oculten errores en pF. El descriptor incluye las 21 ramas anteriores y las cuatro nuevas: **95 incógnitas, rango dinámico 25 y 70 coordenadas algebraicas**. Se comparan polos usando G con Jacobiano híbrido frente a G completamente FD y cargas exportadas independientes.

| Gate numérico fijado | Resultado máximo |
| --- | ---: |
| Masa frente a ngspice: 10⁻¹⁹ F + 10⁻⁶·abs(C) | error/gate 3,97×10⁻⁸ |
| Masa frente a FD: 10⁻¹⁸ F + 10⁻⁵·abs(C) | error/gate 0,000113 |
| Emparejamiento relativo de polos <0,005 | 2,96×10⁻⁸ |
| Residuo descriptor relativo <10⁻⁹ | 2,89×10⁻¹¹ en la ruta principal |
| Transformación de coordenadas <10⁻¹² | Pasa en ambas rutas |

Este contraste independiente verifica las cargas de dispositivo y su ensamblaje local. **No es una simulación ngspice independiente del circuito completo de 94 nodos.**

## Modo creciente y paso grueso

La raíz intermedia conserva un modo creciente en los cuatro escenarios correspondientes; las otras ocho no muestran polos crecientes en el análisis congelado. Con TF/TR=0/0, λ≈6,96051×10⁶ s⁻¹; con TF/TR=1/3 ns, λ≈6,34757×10⁶ s⁻¹. La escala local 1/λ es **143,668/157,541 ns**. Son resultados de las hipótesis del laboratorio, no tiempos de conmutación identificados para el Model D.

Euler hacia atrás tiene amplificación `1/(1−dt·λ)`. Para dt=1 ms amortigua ese modo creciente. Que una solución implícita gruesa converja no permite interpretar su rama como evolución estable. Los polos negativos de las otras raíces tampoco prueban estabilidad de una trayectoria: se trata de una linealización congelada en puntos temporales.

## Repetición simultánea del paso ambiguo

Se parte del último estado previamente aceptado del prefijo de 94 nodos. Las cargas nuevas se preparan desde sus voltajes declarados; los 21 historiales anteriores se conservan exactamente. Este inicio condicionado no demuestra que el prefijo previo se reproduzca al añadir las cargas.

Para KEY=10 V y dt=1 ms se repite el circuito completo con los nuevos términos de carga y semillas cercanas a cada raíz anterior. **Siguen existiendo tres soluciones diferentes por combinación de R61/perfil**, con todos los historiales entrantes comunes. No se selecciona ninguna ni se afirma enumeración exhaustiva.

Las doce repeticiones pasan KCL<10⁻¹¹ A y corrección<10⁻⁸ V. Cada solución se reproduce con Jacobiano completamente FD desde una semilla desplazada +0,1 mV en todos los nodos, conservando el historial: diferencia máxima **2,21×10⁻¹¹ V**, dentro del gate de 1 µV. La variación máxima respecto de las raíces sin estas cargas es **5,974 mV**; no se oculta restando voltajes o reseteando memorias.

## Regresiones y cierre pendiente

Seis pruebas reconstruyen el contraste AC y los descriptores; derivan la corriente temporal con historial fijo; verifican KCL, Jacobiano y publicación conjunta de las 25 memorias escalares; reproducen las doce soluciones por FD desde otra semilla; y prueban rechazos de presupuesto, malla, layout, polaridad y cambio de parámetros sin modificar el estado aceptado.

```powershell
python tools/loudness_latch_charge_probes.py
python -m unittest discover -s tests -p test_loudness_latch_charge.py -v
```

Faltan cargas dinámicas de **Q16/Q17/Q18/Q19/Q3/Q2/Q12/Q20**, de los diodos y de todos los semiconductores de audio. Deben declararse y contrastarse antes de atribuir causalidad física al resultado. También faltan alta inyección, resistencia de base, transporte dependiente del sesgo y parámetros identificados.

Próximo bloque: preparar el circuito con estas memorias desde el arranque, seguir su continuidad con pasos que resuelvan los modos rápidos y verificar refinamiento temporal. Las raíces múltiples, los rechazos y la preparación condicionada deben permanecer visibles. No hay transición Note On/Off, fidelidad sonora ni deadline admitidos por este informe.
