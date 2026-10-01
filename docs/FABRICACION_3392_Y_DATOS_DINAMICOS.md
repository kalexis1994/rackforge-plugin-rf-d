# Fabricación 2N3392 y datos dinámicos

## Nuevas fuentes adquiridas

Se descarga el catálogo **GE/RCA 1987** desde `www.bitsavers.org` y **Fairchild PN100A rev. C1, octubre de 2008**, desde la ruta pública `onsemi.com/pub/Collateral`. Ambas copias son PDF reales, con hashes registrados en [FUENTES](FUENTES.md). Las rutas inicialmente consultadas sin `www` y `download/data-sheet` respondieron 403; las alternativas públicas entregaron los documentos. Originales y renders permanecen ignorados.

El [registro de fuentes de carga](../evidence/latch_charge_source_ledger.json) conserva fabricante, revisión, columna de límites, sesgo, página PDF/impresa y cuestiones pendientes. No asigna parámetros al motor.

## Columnas y población

| Fuente | Cob a 10 V inversos, 1 MHz, 25 °C |
| --- | --- |
| GE/RCA 1987, PDF p. 16 / impresa 15 | **2 pF típico**, 10 pF máximo; mínimo vacío |
| Central 2014, PDF p. 1 | **2 pF mínimo**, 10 pF máximo; típico vacío |
| Fairchild 1997, PDF p. 2 | **2 pF mínimo**, 10 pF máximo; típico vacío |

La diferencia no es una tolerancia estadística común: se mantienen tres poblaciones documentales. GE declara TO-98; Fairchild TO-92. Debe preservarse la conexión B/C/E por nombre y verificar el encapsulado antes de usar un orden físico de pines.

GE aporta curvas para 2N3392, pero su Fig. 8 imprime `VBE=5 V` en el encabezado mientras representa VBE. Los rótulos de terminales de Fig. 12 también requieren contraste antes de digitalizar. Se registra la ambigüedad y no se corrige por intuición. Curvas típicas no identifican un lote Moog.

## Pista Process 10

Fairchild 1997 p. 1 remite expresamente a PN100A. La hoja PN100A de 2008 confirma Process 10 y aporta:

- PDF p. 3 / impresa 2: **fT mínimo 250 MHz**, IC=20 mA y VCE=20 V; Cobo máximo 4,5 pF a VCB=5 V, 1 MHz.
- PDF p. 4 / impresa 3: curvas típicas de capacitancia inversa.
- PDF p. 5 / impresa 4, Fig. 7: tiempos de conmutación para IC=10..300 mA, VCC=10 V y magnitudes IB1=IB2=IC/10.

Los doce puntos del [inventario Q25/Q15](CARGAS_JUNTURA_Y_DOMINIO_BIESTABLE.md) tienen IC entre casi cero y 2,59 mA: todos quedan por debajo del intervalo de esa curva de conmutación. Tampoco reproducen IC/VCE del ensayo fT. La [comparación reproducible](../evidence/latch_dynamic_source_coverage.json) registra cero coincidencias de sesgo fT, cero puntos dentro del dominio IC de conmutación y cero coincidencias exactas VCB de Cobo PN100A. Las precisiones de comparación 1 nA/1 nV no constituyen tolerancias físicas. Es una referencia de familia posterior, útil para una hipótesis condicionada; la identidad de fabricación histórica sigue desconocida.

`ts` de una conmutación bajo ese drive no se introduce como `TF`/`TR`. Un único fT tampoco separa tiempo de tránsito, depleción y resistencia de base. La nueva hoja no reemplaza los tiempos explícitamente desconocidos ni autoriza ajustar la envolvente por oído.

## Gate documental

Antes de ajustar cargas: aclarar rótulos y dominio de las curvas, conservar separado típico/mínimo/máximo y cada fabricante, derivar la relación entre medición y parámetro, y comprobar identificabilidad. Un parámetro condicionado debe mantener su etiqueta de hipótesis y pasar contraste independiente de terminales/transportes. El registro permanece con `selected_parameter_set=null` y sin audio admitido.
