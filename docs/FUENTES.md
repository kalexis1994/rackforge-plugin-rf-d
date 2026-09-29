# Registro de fuentes de RF-D

Investigación iniciada el 28-09-2026. Los originales descargados quedan en `references-local/` (ignorado por Git). Este repositorio guarda enlaces, hashes y conclusiones propias; no redistribuye los documentos. **Página PDF** significa índice desde 1 del archivo indicado; cuando existe, también se anota la página impresa.

## Corpus local verificado

| ID | Documento original y procedencia | Archivo local (fuera de Git) | SHA-256 | Alcance comprobado |
| --- | --- | --- | --- | --- |
| SVC-204D | [Moog/Norlin, *Service Manual for Minimoog Model 204D*, 993-043232-002](https://manuals.fdiskc.com/tree/Moog/Moog%20Minimoog%20Service%20Manual.pdf) | `pdf/service_204d_full_fdiskc.pdf` | `d1f96fa26d9e25dda9d1cb0bbe9a5e0b017f7e463ec5b268c380b58d44f5b6fe` | 82 páginas; especificaciones, descripción, servicio, modificaciones, inventario de piezas y esquemas. Escaneo sin texto extraíble. |
| SVC-9 | [Moog/Norlin, sección 9 del mismo manual: esquemas y placas](https://synthfool.com/docs/Moog/minimoog/Minimoog_Service_Manual.pdf) | `pdf/service_204d_synthfool.pdf` | `0edd35f3f9ab1eba346693545f0dcbe374bdcf6f37f9b1a34ecbdeb8ae682b4a` | 46 páginas; copias alternativas de esquemas y listas. **No es el manual completo**. |
| SVC-RJF | [R. J. Folkman, *The Minimoog Model D Technical Service Manual*, 7/1973](https://www.vintagesynthparts.com/wp-content/uploads/2016/08/MINIMOOG-D_SERVICE_MANUAL.pdf) | `pdf/service_model_d_folkman.pdf` | `914e3e7007ee8a5e80d1145ebabc53c2500f91f3a7b5df212a3543518391ee9d` | 24 páginas, texto extraíble; placas 93-113/114/115/116 y calibración temprana. Esta copia declara ausentes sus esquemas (PDF pp. 19–20). |
| OP-EARLY | [Moog, *A Guide to the Operation of the Mini Moog Model D*](https://funkwerkes.com/web/wp-content/techdocs/MixedProAudio/Minimoog-Manual.pdf) | `pdf/operation_model_d_funkwerkes.pdf` | `9a598c654920c87609c600ba9fc84096c7d6ddf032bd256469d173d1aed2835b` | 43 páginas: manual de operación temprano en PDF pp. 1–19, seguido por el manual Folkman en pp. 20–43. No adjudicarlo al manual de Tom Rhea de 1974 sin otra evidencia. |
| B-804C-1 | [Norlin, Factory Service Bulletin 804C, 9/1981, hoja 1](https://synthfool.com/docs/Moog/minimoog/factory_service_bulleting_804C1.jpg) | `factory-bulletins/804C_p1.jpg` | `eb0678df1751dbaa1f75977994435da581ce255c7ee7e831ba0c2961da7f6b1b` | Corrige instrucciones y valores de manual; en §8.2 cambia **10175 por 5000** para el kit de estabilidad de placa antigua. |
| B-804C-2 | [Norlin, Bulletin 804C, hoja 2](https://synthfool.com/docs/Moog/minimoog/factory_service_bulleting_804C2.jpg) | `factory-bulletins/804C_p2.jpg` | `d049166176480ae8a21bd1ff20e7133e72f2c5f99a2963a3af035c3857642a18` | Más correcciones, incluidas notas de selección de pares de transistores de la placa de filtro. |
| B-832 | [Moog, Factory Service Bulletin 832, 3/1983](https://synthfool.com/docs/Moog/minimoog/factory_service_bulleting_832.jpg) | `factory-bulletins/832.jpg` | `74c31b3c6f7dc8b12432372aed20c62b8df832e4eee3ad1e45209829806cbcb5` | Modificación de potenciómetro/cableado para reducir modulación residual al mínimo; aplicable a todos los números de serie según boletín. |
| B-TUNE | [Moog, procedimiento actualizado de afinación para osciladores antiguos](https://synthfool.com/docs/Moog/minimoog/updated_tuning_early_vcos.jpg) | `factory-bulletins/updated_tuning_early_vcos.jpg` | `54f9d170c3927ee4ba867ecf4cf40f5e79ebb255c88b6d0bd5122c04c46571fa` | Hoja que reemplaza pp. impresas 5-5 y 5-6 para seriales bajo 10175; cambia el orden/objetivos de ajuste. |
| PAT-LADDER | [R. A. Moog, US3475623, *Electronic high-pass and low-pass filters employing the base to emitter diode resistance of bipolar transistors*](https://patents.google.com/patent/US3475623A/en) | `pdf/patent_us3475623_moog_ladder.pdf` | `464ba3222f40e8430281388b06085177702331b2d87c9ec9361c929f48480905` | 9 páginas; principio de ladder y realimentación. **No prueba** el BOM ni la calibración del Model D. |
| DS-726 | [Fairchild, μA726, *Temperature-Controlled Differential Pair*](https://radio-hobby.org/uploads/datasheet/7/ua72/ua726.pdf) | `datasheets/fairchild_ua726.pdf` | `c1d463512dcae704c61ad7549ac4158718ca377b8e6b3f0a047e940b49301b26` | 3 páginas; componente de la placa estabilizada documentado por SVC-204D p. PDF 8. Hoja de componente, no medición del equipo. |
| DS-3046 | [Rochester Electronics, reproducción de hoja CA3046, *General Purpose NPN Transistor Array*](https://atta.szlcsc.com/upload/public/pdf/source/20240129/4203E06A77725CA3AAC3A43A913440E8.pdf) | `datasheets/rochester_ca3046.pdf` | `27c7742de9b37256c3653c1286b7c473f729e7fb9c1e3247c60b27f29bb0de4d` | 2 páginas; array indicado en Fig. 9-3 para la placa antigua. Edición posterior de fabricante; sus parámetros no se transfieren sin examinar población, alimentación y rango de trabajo. |
| DS-458 | [Microsemi/Microchip, *1N457A thru 1N459A*, T4-LDS-0023 rev. 1](https://ww1.microchip.com/downloads/aemDocuments/documents/HRDS/ProductDocuments/DataSheets/1N457A-1N459A.pdf) | `datasheets/microsemi_1n457a_1n459a.pdf` | `f042566295364dd26f32c77bffde48bbbbbd0f55185d3d16f10e403e9d472582` | PDF pp. 1 y 3; límites de 1N458A a 25 °C. Producción posterior, sin curva I–V vintage ni parámetros dinámicos. Véase [modelo condicionado](DIODOS_SALIDA_1N458A.md). |
| MOOG-2022 | [Moog, *Minimoog Model D User's Manual* (reedición)](https://cdn.inmusicbrands.com/Moog/Model%20D/Minimoog_Model_D_Manual.pdf) | `pdf/user_model_d_2022_moog.pdf` | `c7e6f1abd54999cad7aa232d782df397f974ff210db1e6a429a863af6e850b1f` | 84 páginas; comparación de interfaz, no especificación del clásico. |

El manual Folkman está duplicado dentro de OP-EARLY. El PDF SVC-9 solapa la sección 9 de SVC-204D, pero puede ofrecer otro contraste visual de los esquemas. Se comprobó que cada descarga listada abre como PDF o JPEG real; respuestas HTML bloqueadas no se registran como fuentes.

## Copias complementarias y pistas de modificación

| Archivo local | Procedencia y hash SHA-256 | Uso |
| --- | --- | --- |
| `factory-bulletins/mini_modifications1.jpg` | [Sección 8, hoja 1](https://synthfool.com/docs/Moog/minimoog/mini_modifications1.jpg), `46dfe957c9c13ec6fbeaf73b78d456ef1c0ca2789572dc7b7c0c54f9af96fcfe3` | Escaneo alternativo de SVC-204D §8.1–8.6, útil para leer valores y seriales. |
| `factory-bulletins/mini_modifications2.jpg` | [Sección 8, hoja 2](https://synthfool.com/docs/Moog/minimoog/mini_modifications2.jpg), `d0a0e8c72b8dcc8c7aa887ecd826b77242ee868645e860ffd3d65f58e268b6d3` | Escaneo alternativo de §8.6–8.8: fugas en placa 2, VCO 2 en torno al serial 4185 y reemplazo de placa osciladora. |
| `factory-bulletins/mini_modifications3.jpg` | [Sección 8, hoja 3](https://synthfool.com/docs/Moog/minimoog/mini_modifications3.jpg), `30ce8107c46598d42ee1f05a7d49013df5df2a65d3b0070d96124b2f78681d27` | Escaneo alternativo de ajustes de VCO y modificación de conexión de fuente. |
| `factory-bulletins/mini_psu_mod.jpg` | [Extracto de modificación de fuente](https://synthfool.com/docs/Moog/minimoog/mini_psu_mod.jpg), `6fb2449a71d26d6043a9b233f2313e4803f38bc8e24b76a1c9b3a5c3cbb26fa2` | Duplicado ampliado del procedimiento de conexión de alimentación. |
| `secondary/more_mini_mods.jpg` | [Colección manuscrita de modificaciones](https://synthfool.com/docs/Moog/minimoog/more_mini_mods.jpg), `7ff308c45d3c23db8945b7d114db5b3ca71dade0d60926e1d7262cae65587232` | **Pista secundaria**, sin atribución de fábrica; sync, rueda, trigger y bleed. No define el circuito nominal. |
| `secondary/lessdrift.jpg` | [Consejo de menor deriva](https://synthfool.com/docs/Moog/minimoog/lessdrift.jpg), `2be4fbd153559f9de0d5a3cdafc37e483d32ebbe9f954aafa9a3b417aa0893ec` | **Pista secundaria**, modificación posterior de amplificadores del VCO. No presumirla en una unidad clásica. |

[Un índice de correcciones aportadas por técnicos](https://www.synthfool.com/docs/Moog/minimoog/errors/) señala posibles errores de cableado, numeración de pin y dibujos de placas. Sus afirmaciones permanecen **sin verificar** contra los esquemas y una unidad real, por lo que no se usan como evidencia primaria.

[Una comparación de primera mano de placas CA3046 y μA726](https://forum.moogmusic.com/t/minimoog-model-d-differences/14878) documenta que el autor midió ambos VCO antes del potenciómetro de mixer, en la misma nota, y describe diferencias de forma y pulso. Las imágenes originales alojadas en Tinypic no están accesibles; la publicación aporta una **observación cualitativa**, sin voltajes, audio crudo ni panel reproducible. [Otra nota histórica](https://forum.moogmusic.com/t/ra-minimoog/22482/7) menciona el dibujo original #1441 de la primera placa discreta. Queda como pista para localizar el documento, no como esquema verificado.

## Investigación de métodos numéricos

Estos artículos originales ayudan a diseñar y contrastar el solver. **Ninguno sustituye** los valores de las placas del Model D documentados por SVC-204D.

| ID | Publicación y archivo local | SHA-256 | Uso y límite |
| --- | --- | --- | --- |
| DSP-HUV-2004 | [A. Huovilainen, *Non-Linear Digital Implementation of the Moog Ladder Filter*, DAFx 2004](https://www.dafx.de/paper-archive/2004/P_061.PDF), `research/huovilainen_dafx2004_ladder.pdf` | `d8bee4101c859f3eb8f0ccc0d08d6a3af09745ccce4c6549e46dd27138a30d67` | 4 pp.; ecuación diferencial del ladder idealizado y discretización Euler con corrección de sintonía. Sus supuestos de transistores apareados, beta infinita y carga despreciable deben examinarse frente a la placa 4 completa. |
| DSP-DV-2013 | [S. D'Angelo y V. Välimäki, *An Improved Virtual Analog Model of the Moog Ladder Filter*, ICASSP 2013](https://dangelo.audio/icassp13-ladder), [PDF del artículo](https://raw.githubusercontent.com/ddiakopoulos/MoogLadders/master/research/DAngeloValimaki.pdf), `research/dangelo_valimaki_icassp2013_ladder.pdf` | `5d1490cf578d7e0f41de89344b905f1a3989fe19875d31ecb19f1aed35c204c1` | 5 pp.; modelo no lineal y comparación con SPICE. Referencia de método y banco de contraste; su esquema de núcleo no incluye por sí solo mixer, recuperación, dos VCA y salida del RF-D. |
| DSP-PEK-2011 | [J. Pekonen et al., *Discrete-Time Modelling of the Moog Sawtooth Oscillator Waveform*, EURASIP 2011](https://mural.maynoothuniversity.ie/id/eprint/4185/), [PDF](https://mural.maynoothuniversity.ie/id/eprint/4185/1/VL_Discrete-time.pdf), `research/pekonen2011_voyager_sawtooth.pdf` | `dadfe0f7744ef2660d5c26551f583d013474732e170b60943ef47779a91baee8` | 15 pp.; antialias y ajuste de forma de onda. **La grabación objetivo es de un Minimoog Voyager**, indicado en el propio artículo pp. 1–2, y no mide un Model D clásico. No importar sus curvas ni parámetros como evidencia RF-D. |
| BJT-TI-2023 | [Texas Instruments, *DC Parameters: Input Offset Voltage (VOS)*, SLOA059B, rev. 3/2023](https://www.ti.com/lit/an/sloa059b/sloa059b.pdf), `research/ti_sloa059b.pdf` | `3d7015d7c8b3c6944099b841f263173419dd3a6100f84759582618b83b99d6dc` | 20 pp.; PDF p. 6, impresa 6, ecuaciones (3)–(4): `V_BE = (kT/q) ln(I_C/I_S)` y diferencia entre par bipolar. Se usa como ley ideal condicionada; **no** aporta corrientes ni emparejamiento medidos del CA3046 instalado. |

## Índice de páginas decisivas

| Pregunta | Fuente y ubicación |
| --- | --- |
| Especificaciones de fábrica: cinco fuentes, formas, rangos, salidas, teclado | SVC-204D PDF p. 6, impresa vi |
| Placa de osciladores estabilizada: sumadores, μA726, rampas/formas | SVC-204D PDF pp. 8–10, impresas 2-3 a 2-5; esquema PDF p. 60, Fig. 9-2 |
| Placa de osciladores antigua: convertidor, rampa, triángulo, pulso | SVC-204D PDF pp. 14–16, impresas 2-9 a 2-10A; esquema PDF p. 61, Fig. 9-3 |
| Interconexión de osciladores, SW6, ancho 22B, R30/R31, R6/R45 y SW9 | SVC-9 PDF p. 19, Fig. 9-17; SVC-204D PDF p. 75. Entrada de mixer en placa 4: SVC-9 PDF p. 13, Fig. 9-11 (SVC-204D p. 69). |
| Bus de mezcla: cinco ramas ON, resistencias R45–R49 y entrada de placa 4 | SVC-9 PDF p. 19, Fig. 9-17; placa 4 y C27 en SVC-9 PDF p. 13, Fig. 9-11. |
| Entrada de filtro: C27, R54, C24, R61, Q29/Q30 y retorno de regeneración | SVC-9 PDF p. 13, Fig. 9-11; tabla 7-8 PDF pp. 30–31. R61 difiere entre esquema (`200`) y lista (`200K Ohm`); ver [análisis](ENTRADA_FILTRO.md). |
| Recuperación activa Q5–Q8, R6/R7/R3, C1/C5/C9, R20/R24/R26/R31/R38 | SVC-9 PDF p. 13, Fig. 9-11 y tabla 7-8 PDF pp. 30–31; [DC y AC condicionados](RECUPERACION_ACTIVA_FILTRO.md). R3=1 kΩ, R23=100 Ω según la tabla. |
| Lazo de EMPHASIS en pequeña señal: tap R7/R3 → C10 → R14 de panel → R73 → Q30, retorno por R76/BOTTOM | SVC-9 PDF pp. 13 y 19, Figs. 9-11 y 9-17, tabla 7-8 pp. 30–31; [red acoplada](LAZO_EMPHASIS_PEQUENA_SENAL.md). La curva de R14 y parámetros de transistor siguen impuestos o desconocidos. |
| Transitorio no lineal acoplado del ladder, Q5–Q8 y EMPHASIS | Mismas figuras y tabla SVC-9; [Euler implícito de 24 nodos con C10 como estado](TRANSITORIO_FILTRO_ACOPLADO.md), método BJT de Nagel y Pederson citado en este registro. Valores de BJT y R61 físico pendientes. |
| Salida paralela R77/pin 22/R21 HEADPHONE VOL hasta cursor | SVC-9 Fig. 9-11 PDF p. 13 y Fig. 9-17 PDF p. 19; SVC-204D pp. 69 y 75; [red condicionada](SALIDA_AURICULARES_R21.md). La etapa activa posterior sigue abierta. |
| Entrada de auriculares de placa 3: pin 7, C19/R50/R53 y base Q16 | SVC-9 Fig. 9-8 PDF p. 10 y Fig. 9-17 PDF p. 19; SVC-204D pp. 66 y 75; [frontera pasiva](ENTRADA_AMP_AURICULARES.md). La corriente de base se supone nula y no hay modelo de ganancia. |
| Salida de auriculares de placa 3: nodo Q11/R33 y Q10/R32, C21, pin 8, R56 y J7 | SVC-9 Fig. 9-8 PDF p. 10 y Fig. 9-17 PDF p. 19; SVC-204D pp. 66 y 75; [acoplamiento pasivo](ACOPLAMIENTO_SALIDA_AURICULARES.md). Fuente ideal pre-C21 y cargas de auricular son hipótesis explícitas. |
| Etapa activa de auriculares Q16/Q11/Q10 y CR1/CR2; frontera de sesgo de Q16 | SVC-9 Fig. 9-8 PDF p. 10 (SVC-204D p. 66); [grafo y Thévenin DC](TOPOLOGIA_AMP_AURICULARES.md). El Thévenin deja libre la corriente de base; el cierre semiconductor está documentado aparte. |
| Punto DC aislado de los tres TIS y dos 1N458A de placa 3 | SVC-9 Fig. 9-8 PDF p. 10 (SVC-204D p. 66), Nagel/Pederson 1973 pp. 4–5 y hoja Microsemi 1N458A ya registrada; [once nodos condicionados](PUNTO_DC_AMP_AURICULARES.md). Parámetros BJT/diodo son supuestos, no ajustes de hardware. |
| AC incremental aislado del amplificador de auriculares hasta J7 | Mismos esquema, leyes y condiciones que el punto DC anterior; [matriz de doce nodos](AC_AMP_AURICULARES.md) añade C19/C15/C21/R56 y cargas externas impuestas. |
| AC acoplado BUS→R21→placa 3→J7 | SVC-9 Figs. 9-8 p. 10, 9-11 p. 13 y 9-17 p. 19; [reducción de un puerto y matriz explícita de 65 nodos](AURICULARES_AC_ACOPLADO.md). Sigue siendo pequeña señal condicionada. |
| SW18 MAIN OUTPUT en ON/OFF, secciones 5/2 y contactos 6/3, 4/1 | SVC-9 Fig. 9-17 PDF p. 19; SVC-204D PDF p. 75; [carga y aislamiento en OFF](SW18_OFF_SALIDA.md). Fugas, rebote y contactos de jack no identificados. |
| Sensibilidad conjunta de R20/R21, SW18 y carga del cursor | SVC-9 Fig. 9-11 p. 13, Fig. 9-17 p. 19, tabla 7-8 pp. 30–31; [54 escenarios condicionados](SENSIBILIDAD_PANEL_SALIDA.md). Las cargas y posiciones eléctricas de la malla son hipótesis. |
| Sensibilidad de EMPHASIS: R61, R73, R14 y C10 | SVC-9 Figs. 9-11 y 9-17, tabla 7-8 pp. 30–31; [malla de 162 escenarios](SENSIBILIDAD_EMPHASIS.md). Intervalo C10 `+50/−10 %`; no representa frecuencia estadística de piezas reales. |
| Jacobiano analítico del transitorio de 24 nodos | Topología y valores SVC-9 Fig. 9-11 p. 13, Fig. 9-17 p. 19, tabla 7-8 pp. 30–31; ley Ebers–Moll de Nagel y Pederson 1973 pp. 4–5; [derivación, regresión y coste local](JACOBIAN_ANALITICO_FILTRO.md). |
| Entrada del primer VCA: R2, C6, R34, C15, R36, Q16/Q15 y Q18 | SVC-204D §2.9 PDF p. 12; SVC-9 Fig. 9-11 p. 13 y tabla 7-8 pp. 30–31; [frontera pasiva](FRONTERA_ENTRADA_VCA1.md). R2=82 kΩ entre colector de recuperación y C6. |
| Carga pasiva del primer VCA sobre el colector del recuperador | Mismas fuentes; [red AC de 27 nodos](CARGA_VCA1_FILTRO.md), con C10/R14/R73 y R2/C6/R34/C15/R36. Q16/Q15 activos pendientes. |
| Transitorio del filtro y entrada pasiva del primer VCA | SVC-204D §2.9 p. 12 y SVC-9 Fig. 9-11 p. 13, tabla 7-8 pp. 30–31; [oráculo de 27 nodos](TRANSITORIO_CARGA_VCA1.md). Q16/Q15 siguen abiertos. |
| Retorno de regeneración: C10, R14 de panel, R73, R76 y Q30 | SVC-9 PDF p. 13, Fig. 9-11, p. 19, Fig. 9-17 y tabla 7-8 PDF pp. 30–31; [derivación condicionada](REGENERACION_FILTRO.md). |
| Par inferior Q29/Q30 y cola R60/Q28 | SVC-9 PDF p. 13, Fig. 9-11, tabla 7-8 pp. 30–31; B-804C-2 corrige nota 3 de Q26/Q28; [límite ideal del par](PAR_ENTRADA_FILTRO_IDEAL.md) usa BJT-TI-2023 p. 6 y constantes SI NIST/CODATA. |
| Control de corriente Q26/Q28: R39 RANGE, R46, R45 y R60 | SVC-9 PDF p. 13, Fig. 9-11, tabla 7-8 pp. 30–31 y B-804C-2; [carga DC condicionada](COLA_FILTRO_Q26_Q28.md). |
| Base de Q26: R11/R55, J2/R51, SW15/R52, SW16/R53, SW17/R54, pin 5 directo, R74 desde pin 16, R49/R70/C18 | SVC-9 PDF pp. 13 y 19, Figs. 9-11 y 9-17; [reducción pasiva y estados de panel](BASE_Q26_CONTROL_FILTRO.md), [transcripción](../evidence/filter_cutoff_base_network.json). |
| Q26/Q28 con corriente de base finita y panel acoplado | SVC-9 PDF pp. 13 y 19, Figs. 9-11 y 9-17; BJT-TI-2023 PDF p. 6, ec. (3) para ley exponencial; [punto DC condicionado](COLA_FILTRO_ACOPLADA_DC.md). β e Is siguen impuestos; TAIL puede imponerse o cerrarse condicionalmente con Q29/Q30. |
| TAIL de Q29/Q30 con R60 y corriente Q28 | SVC-9 PDF p. 13, Fig. 9-11 y tabla 7-8 pp. 30–31; BJT-TI-2023 PDF p. 6, ec. (3); [cierre DC condicionado](COLA_FILTRO_TAIL_Q29_Q30.md). Bases inferiores, β e Is siguen impuestos. |
| BOTTOM y bases Q29/Q30 en DC, dos candidatos R61, R54/R76/R73 y pin 6 abierto por C10 | SVC-9 PDF p. 13, Fig. 9-11; p. 19, Fig. 9-17; tabla 7-8 pp. 30–31; [cierre DC condicionado](BASES_FILTRO_ACOPLADAS_DC.md). Inyección desde el ladder superior y parámetros de transistor siguen impuestos. |
| Ruido, mezcla de modulación y entrada externa | SVC-204D PDF pp. 10–11 y 14; esquemas pp. 66 y 69 |
| Ladder, recuperación, dos VCA | SVC-204D PDF pp. 11–12, impresa 2-7; placa p. 68, Fig. 9-10; esquema p. 69, Fig. 9-11. |
| Contornos, gatillo y final decay | SVC-204D PDF pp. 12–13, impresas 2-7 a 2-8; esquema p. 65, Fig. 9-5 |
| Prioridad de nota, retención CV, glide | SVC-204D PDF p. 16, impresa 2-10A; esquema p. 65, Fig. 9-5 |
| Afinación y calibración | SVC-204D PDF pp. 26–38, sección 5; B-TUNE y B-804C tienen prioridad para los procedimientos que corrigen |
| Modificaciones de época | SVC-204D PDF pp. 52–57, sección 8, con correcciones B-804C |
| Revisión temprana de placas | SVC-RJF PDF pp. 4–5, impresas 4–5; ajustes pp. 11–17 |

## Fuentes por conseguir o verificar

Para el [cierre DC con saturación simple del ladder](LADDER_EBERS_MOLL_DC.md), la fuente metodológica primaria es [Nagel y Pederson, *SPICE*, 1973, PDF pp. 4–5](https://www2.eecs.berkeley.edu/Pubs/TechRpts/1973/ERL-m-382.pdf), con β directo e inverso en Ebers–Moll. El [manual de ngspice §7.3.3](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) delimita efectos adicionales del modelo Gummel–Poon. La [red de pequeña señal](LADDER_PEQUENA_SENAL.md) toma C3/C7/C11/C16 de SVC-9 Fig. 9-11 y tabla 7-8, p. 30; la [frontera de recuperación](FRONTERA_RECUPERACION_FILTRO.md) toma C1/C5 y R31/R38 de la misma figura y tabla 7-8, pp. 30–31. Ninguna fuente aporta β inverso medido de la placa 4.

La [columna resistiva DC del ladder](COLUMNA_RESISTIVA_LADDER_DC.md) transcribe R4, R16, R32, R41 y R52 de placa 4 desde SVC-9 Fig. 9-11, PDF p. 13, y tabla 7-8, pp. 30–31. Las [pilas activas](PILAS_ACTIVAS_LADDER_DC.md) trazan los dos recorridos colector/emisor y derivan las corrientes de tap condicionalmente a β e `I_S` impuestos.

- [Tom Rhea, *Minimoog Model D Operation Manual* (1974), documentado por el autor](https://www.drtomrhea.com/resources) y [ejemplar catalogado por The Henry Ford](https://www.thehenryford.org/collections/explore/artifact/429443). Falta un escaneo íntegro autenticado; no confundirlo con OP-EARLY.
- Dibujo Moog #1441 (21-12-1970) de la primera placa osciladora discreta, citado por un técnico pero no localizado como documento primario íntegro.
- Fotografías de placas originales de procedencia comprobable para contrastar población y cambios del esquema; no se asume que una foto de una unidad representa todo un lote.
- Referencias audibles de autores/propietarios de unidades vintage: [candidatas y límites](VALIDACION_SIN_HARDWARE.md). No habrá captura o medición propia del instrumento.

## Regla de admisión

Cada constante DSP requiere documento/página o nodo medido, derivación, unidades, dominio de validez, incertidumbre y prueba que pueda refutarla. La especificación de fábrica, el esquema nominal, la unidad ajustada y la preferencia musical son niveles de evidencia distintos. Un valor de datasheet o reedición no se traslada automáticamente a la voz clásica.
