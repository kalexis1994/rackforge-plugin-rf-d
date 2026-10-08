# 741 cargado: puerto exacto y término dinámico limitante

2026-10-08, base ce2eda7. [Contrato previo](VCO1_741_CONDENSACION_PROTOCOLO.md) y [banco de raíces](VCO1_741_RAICES_PROTOCOLO.md). CA3046 nominal, C4=10 pF, 25 °C; dos tarjetas TI completas, producción intacta. No hay nuevo SPICE o WAV. Este bloque añade herramientas Decimal100 de laboratorio, no una reducción física o admisión temporal del oscilador.

## Partición implementada

Condensación de 32 interiores por 741 mediante LU escalado y múltiples RHS: residual afín, matriz cargada 5×5, cinco columnas de historia y reconstrucción interior. Conserva todas las corrientes de alimentación/salida/entrada, tres memorias de capacitor y dos de inductor por tarjeta; gmin y el pin de IC1 ligado a suelo tienen retornos explícitos. Reensambla un sistema exterior de 70 incógnitas y reconstruye las 134 correcciones antes de comprobar gates. No suprime polos ni resuelve una tarjeta con salida sin carga.

El [recibo03](../evidence/voice_vco1_741_condensation03.json) pasa **12 sistemas locales**: tres historias de reset × DC/125 ns/30,5176 ps/7,62939 ps. Frente a eliminación completa con pivotes absolutos, diferencia máxima 4,5607e−92 V /4,60522e−94 A; residual reconstruido ≤4,51491e−94 y KCL global más suelo ≤4,705e−97 A. Las 24 tarjetas locales contrastan también diez RHS cada una contra 37 filas con terminales impuestos: cinco tensiones y cinco memorias. Gates algebraicos 1e−60, propios de Decimal100; no indican exactitud binary64 o tiempo real. Las correcciones DC son linealizaciones, no nuevas raíces DC libres. Valores y matrices completos retenidos.

Los intentos01/02 fallan por un retorno global incompleto del adaptador, aunque las correcciones ya coinciden. Se conservan original, replay y diagnóstico; la [auditoría](VCO1_741_CONDENSACION_AUDITORIA.md) identifica el retorno omitido de la placa y su reparación por incidencias explícitas. No se infiere el retorno como negativo de la suma global, ni se relaja un gate.

## Raíces no lineales cargadas

El [banco03](../evidence/voice_vco1_741_roots03.json) pasa **nueve pares condicionales** desde las mismas tres historias a 7,62939/15,2588/30,5176 ps, con historia fija durante Newton y candidatos reconstruidos. Cada raíz condensada se compara con el solve completo Decimal100 desde su propia historia, sin importar la raíz completa como semilla. Diferencias ≤4,39e−97 V /1e−101 A, 3–4 iteraciones en ambos métodos. Residual/corrección y KCL conservan gates previos; repetición idéntica y rechazo por presupuesto1 sin mutar historia. No se ensayan DC libre, 125 ns no lineal, C4=100 pF o una trayectoria. No se trasladan estos pasos al dominio de producción.

Los primeros intentos de este banco pasan los mismos nueve pares y luego fallan en metadatos del adaptador de descomposición. [Auditoría y replay](VCO1_741_RAICES_AUDITORIA.md) conservan ambos; el banco03 repite todos los pares tras reparar sólo el acceso a paso/coeficiente. Hay nueve casos únicos, 27 comparaciones de pares incluyendo los dos intentos anteriores; no nuevos tests Rust.

## Modo común de la tarjeta y error temporal

La subred lineal impone iL2=−G4·u, con u=(p+ +p−)/2−(V+ +V−)/2. La base Q2 (nodo7 de la tarjeta) cumple v7=p+ +EOS−R13·iL2−L2·diL2/dt. La forma continua es v7=p+ +EOS+R13·G4·u+L2·G4·du/dt; esta identidad del macromodelo no convierte L2 en una bobina física del Moog. L2·G4≈16,7760015 ns, parámetros originales sin fit. Euler conserva explícitamente la historia de iL2; sus derivadas cargadas verifican esta identidad. El factor de u llega a 2198,8641 a 7,62939 ps. Una matriz estática o un seguidor de salida omitirían el aporte de variación de entrada/rieles.

Se reconstruyen las dos etapas de cada full/mid/end de los diagnósticos SDIRK anteriores, manteniendo coeficientes y tiempos efectivos binary64 originales. El término dinámico de etapa2 incluye tanto memoria entrante como forcing de etapa1. Identidades de base con error ≤1,09321e−95 V, dentro de 1e−11 V declarado. No se vuelve a ejecutar la continuación.

| Intervalo previamente rechazado | Diferencia estática full−end | Diferencia dinámica L2 full−end | Total XIC3.7 | Fracción dinámica con signo |
|---|---:|---:|---:|---:|
| SDIRK01, half15,2588 ps | −0,000247276 µV | −1,999790734 µV | −2,000038010 µV | 99,987636 % |
| SDIRK4, half7,62939 ps | −0,000086634 µV | −2,003965121 µV | −2,004051754 µV | 99,995677 % |

Esto explica algebraicamente la fila que limita ambos intervalos. No demuestra causalidad de toda la trayectoria, exactitud del modelo físico o que retirar L3 arregle el reset. La condensación conserva exactamente las ecuaciones discretas, por lo que **no cambia los rechazos temporales previos**. Los modos rápidos locales y la alimentación dinámica de esta base son evidencias distintas.

## Siguiente puerta

Con el contrato cargado y la reconstrucción establecidos, estudiar el puerto dinámico conservando el término derivativo de modo común y sus historias. Formular por separado cualquier eliminación de subredes rápidas, transformación del descriptor o integración distinta; contrastar corrientes, cargas, retornos, memorias, reconstrucción y error temporal exterior contra la tarjeta completa. No ampliar otra grilla ni aceptar únicamente tensiones de salida por estos nueve pares locales. Ciclos completos, refinamiento/frecuencia, calibración, carga activa de mixer, física y RT siguen abiertos.

La [QA de publicación](../evidence/voice_vco1_741_condensation_tests01.json) hereda 235 tests por identidad, cero nuevos o reejecutados; distingue los 12 sistemas lineales únicos, nueve pares no lineales únicos y sus repeticiones. Conserva todas las evidencias privadas anteriores y la escucha de salida con fuente impuesta.
