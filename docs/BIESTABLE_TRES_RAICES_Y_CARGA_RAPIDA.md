# Tres raíces y dinámica rápida omitida del biestable

## Búsqueda ampliada

El [cierre cargado de 94 nodos](CONTORNO_CADENA_94_Y_ESTABILIDAD.md) conserva las dos raíces observadas con las primeras semillas. Se amplía la búsqueda sin modificar el historial: **17 interpolaciones** entre sus voltajes y desplazamientos `−1/0/+1 mV` en bases de Q25/Q15, 51 semillas por R61.

Los [102 ensayos](../evidence/loudness_chain94_root_survey.json) convergen y encuentran **tres raíces**, con colector Q25:

| Raíz observada | Colector Q25 |
| --- | ---: |
| Inferior | 0,021881 V |
| Intermedia | 0,997567 V |
| Superior | 3,836036 V |

Cada raíz se reproduce con **94 columnas FD desde la misma semilla inicial**, no sólo refinando una raíz ya convergida. Diferencia máxima híbrido↔FD: **1,78 fV**. Todas cierran la misma KCL, dt=1 ms y las mismas 21 cargas entrantes. El campo `selected` sigue siendo null. Se registra explícitamente que el muestreo no prueba exhaustividad.

Este resultado limita la sonda anterior: afirmar «sólo hay dos raíces» a partir de sus cinco semillas habría sido incorrecto. La convergencia de Newton revela la cuenca numérica de una semilla; no identifica por sí sola la trayectoria del circuito.

## Qué aportan las hojas 2N3392

Se descargan y verifican como PDF real dos hojas de fabricante:

- **DS-3392-C:** Central Semiconductor, revisión R0 de 29-01-2014, PDF p. 1. El archivo actual tiene cinco páginas; las restantes incluyen encapsulado y anexos posteriores. Especifica `Cob=2..10 pF` a `VCB=10 V`, `f=1 MHz`, `TA=25 °C`; `hFE=150..300` a `VCE=4,5 V`, `IC=2 mA`.
- **DS-3392-F:** Fairchild, revisión B ©1997, copia de siete páginas, PDF p. 2. Confirma esas condiciones y rangos. Su p. 1 identifica producción Process 10 y remite a PN100A para características; no identifica el proceso de una pieza Moog antigua.

En ambas tablas, **2 pF es mínimo y 10 pF máximo**, no valor típico. No se sustituye el βF=100 hipotético del laboratorio por un número de esas tablas ni se usa Cob constante como una ley vintage. Falta identificar `CBE(VBE)`, `CBC(VBC)`, tiempos de tránsito/almacenamiento, saturación y dispersión de las piezas pobladas. Las condiciones de medida de Cob no cubren la juntura base-colector en conducción directa durante una conmutación. Fuentes y hashes completos están en [FUENTES](FUENTES.md); sólo se versionan metadatos/derivaciones, nunca los PDF.

La descarga directa de la copia Mouser devolvió HTML, aunque terminaba en `.pdf`: se rechazó. La copia Fairchild verificada procede del archivo DigiKey. La pista GE/RCA 1987 respondió HTTP 403 y no se registra como fuente local adquirida.

## Auditoría de perturbación singular

Se añaden **cuatro capacitores de diagnóstico**, con topología BE/BC sobre Q25 y Q15. Permanecen fuera del motor y no se integran en una trayectoria de audio:

```text
C_BE: base ↔ emisor, 1/10/100 pF
C_BC: base ↔ colector, 2/5/10 pF
```

Los tres CBE son escalas numéricas de sensibilidad sin especificación física. Los CBC usan escalas sugeridas por la hoja como experimento, **no un rango validado para estos puntos de operación**. Se omiten leyes no lineales de depleción/difusión, carga almacenada y el resto de las junturas del circuito. Las cargas constantes sólo exploran qué modos desaparecen al hacer instantáneos los terminales del biestable.

La [auditoría](../evidence/loudness_fast_charge_audit.json) cubre **54 escenarios**: tres raíces × dos R61 × nueve pares de cargas. El descriptor pasa de rango dinámico 21 a 25, conservando nodos algebraicos y el nodo serie C10. Se repite con Jacobiano completo FD; error relativo máximo de emparejamiento de polos **5,69×10⁻⁷** y residuo del pencil **3,47×10⁻¹¹**.

## Inestabilidad que el modelo sin carga ocultaba

Las tres raíces no presentan modos crecientes con los 21 capacitores documentados. Al incluir estas cuatro cargas de diagnóstico:

| Raíz | Escenarios | Modos locales crecientes |
| --- | ---: | ---: |
| Inferior | 18 | 0 |
| Intermedia | 18 | **1 en cada escenario** |
| Superior | 18 | 0 |

En la raíz intermedia, el crecimiento observado va de **3,49×10⁶ a 1,85×10⁷ s⁻¹** en el barrido. Para CBE=10 pF/CBC=5 pF resulta aproximadamente `λ=+7,33×10⁶ s⁻¹`. Es un resultado de la familia de cargas hipotéticas; no se adjudica ese tiempo a una pieza vintage.

El límite algebraico había eliminado ese modo rápido. Esto no admite automáticamente la raíz inferior o superior: **ambas conservan modos congelados decrecientes**, y una trayectoria causal con cargas iniciales y leyes físicas sigue pendiente.

## Estabilidad numérica no es estabilidad del circuito

Para el modo escalar `dδv/dt=λδv`, Euler implícito produce:

```text
δv_next / δv_old = 1/(1 − dt·λ)
```

Si `λ>0` y `dt·λ>2`, su magnitud es menor que uno: el paso discreto puede amortiguar un modo continuo creciente. En los 18 escenarios intermedios con dt=1 ms, la magnitud cae entre **5,40×10⁻⁵ y 2,87×10⁻⁴**. Un residuo Newton pequeño o una simulación que no explota no bastan para declarar estable la conmutación.

Se agrega una regresión independiente de un modo conocido `λ=+1000 s⁻¹`, dt=10 ms, que detecta crecimiento continuo aunque Euler tenga amplificación menor que uno. No se usa este fenómeno como mecanismo sonoro ni se oculta la raíz intermedia bajo un gate de convergencia.

## Decisión RACE y siguiente trabajo

Se conserva toda la búsqueda, las tres raíces, los rechazos temporales y `selected=null`. El laboratorio demuestra que el análisis de las cargas macro no alcanza para decidir el biestable y que la dinámica omitida puede cambiar la clasificación. **No están admitidos parámetros de carga, conmutación física ni contorno audible.**

El siguiente corte deberá identificar o acotar leyes de carga dependientes de tensión y conducción, revisar su dominio en los tres puntos y resolver el evento con un historial de cargas coherente. Una selección de raíz por amplitud deseada, etiqueta ADSR o convergencia de una semilla no satisface ese gate.
