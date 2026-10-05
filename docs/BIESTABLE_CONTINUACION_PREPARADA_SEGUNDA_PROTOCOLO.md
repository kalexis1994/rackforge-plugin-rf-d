# Segundo banco con acciones preparadas: protocolo congelado

Fecha: 2026-10-05. Fuente: banco 24–31 completo, variante 0, ancho 8,
ensayo 1, 32 soportes y reloj real 5995191823955603/18446744073709551616 s.
P y sus 22 memorias se transportan exactamente desde el último cierre.

## Banco y decisión

Historias 32–39 del startup congelado, ocho referencias C7 curvas nuevas.
Anchos 8, 4, 2, 1, radios heredados 0,1 y 1 µV. Primera rama completa;
si ninguna completa, prefijo más largo y primera rama en empate. Se corta
cada rama al primer hueco. Todas las plantillas son condicionadas y se
archivan, incluso las no alcanzadas. Reloj intentado y admitido se distinguen.
No se resuelven nuevas trayectorias ni se construye otra métrica.

## Diagnóstico conservado

El pico local del soporte 31 está en nodo de índice 66, [1/2,5/8]:
0,10995732988344857 µV de anclaje y 0,4131863153986408 µV de forcing.
El productor conserva las ocho celdas, las contribuciones exactas de nodo66,
polinomio precondicionado, restos independientes, primera corrección y cola
por subcelda, con identidades completas de RHS y acción. El desglose es una
cota numérica, sin atribuir causalidad física. La validación examina las
mismas magnitudes del banco nuevo. No se cancela ningún resto independiente.

## Certificados y archivo

Cada bloque renueva ledger Bernstein de polinomios completos, dominio,
candidato binario, inversa validada y tres tasas con probes LDL. Preparación
explícita una vez por bloque/radio; cada budget verifica contexto y estado.
Se reproducen todos los bytes de acciones con el helper original y preparado.
No se extrapola el ahorro de tiempo medido en el benchmark anterior.

Artefactos tipados separados para plantilla, bloque y soporte; bytes gzip y
JSON canónico identificados. Guardas de duración física h/8 antes de aplicar
forcing. Fuente, launch, stdout/stderr y snapshots se preservan. Productor y
protocolo se congelan antes de medir, datos/tests/validator antes de validar.
El corpus recupera todas las entradas y las versiones fallidas históricas.

Gates sin cambios: KCL 10 pA, corrección 10 nV, rama lineal 10 fV,
backward 1e-10, objetivo global 1 mV; dominio exponencial 45, norma kernel
4096. Laboratorio nominal offline; cobertura completa, 1 mV global,
identificación física, voz, audio nativo y deadline siguen abiertos.
