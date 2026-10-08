# Puerto 741 cargado: contrato y condensación exacta previa

2026-10-08. Base `ce2eda7f58bc61ff9cda2fe2aac5e5b6a6952200`. CA3046 nominal, 25 °C, C4=10 pF; dos tarjetas TI LM741 completas, sin cambios físicos. Fuentes y unidades: [tarjeta original y stamp](VCO_741_NATIVO_PROTOCOLO.md), [puerto impuesto anterior](VCO_741_PUERTO_PROTOCOLO.md), inventario SVC-9 p.5/p.19 en `tools/vco1_native_inventory.py`. La tarjeta TI es un macromodelo nominal, no una identificación de cada transistor del integrado vintage.

## Contrato

Orden de terminales: entrada positiva, negativa, riel positivo, negativo, salida. I positiva entra al integrado. Conservar corrientes de los cinco terminales, incluida alimentación; corriente de gmin al suelo separada. IC1 tiene su riel positivo conectado a suelo: su corriente sigue existiendo y vuelve al suelo global, no desaparece por omitir esa incógnita.

Memoria independiente: tensiones C4(5−6), C3(98−9), C5(98−15), corrientes L2(98→17) y L3(22→28), unidades V/V/V/A/A. Conservar cargas C·V y flujos L·I; no reiniciar memorias al reducir variables. Cada trial mantiene idéntica historia. La candidata sólo se publica tras aceptar el solve exterior y su error temporal. Mantener todos los nodos y corrientes para reconstrucción y para gates heredados; la API reducida no autoriza comprobar sólo la salida.

Para una linealización Newton en candidato arbitrario e historia fija: partición terminal p/interior i, residual f y Jacobiano J. Resolver Jii·W=Jip y Jii·u=fi. Residual afín del puerto f*=fp−Jpi·u; tangente Y=Jpp−Jpi·W. Reconstruir δi=−u−W·δp. Es eliminación exacta del sistema lineal, no supresión de dinámica o solve no lineal. Para historia h, B=∂fp/∂h−Jpi·Jii⁻¹·∂fi/∂h. Conservar B y respuesta interior; no usarla como licencia para cambiar historia durante Newton.

Ensamblar tarjeta/placa por incidencias, sin duplicar componentes. Los 64 interiores de los dos 741 se condensan, quedan 70 incógnitas exteriores. Reponer las 134 correcciones antes de aceptar. Reconstruir suelo g*=g+∂g/∂xi·(−u), dg*/dp y dg*/dh. Exigir suma de cinco corrientes y suelo, tanto afín como derivadas; luego comprobar KCL global de 98 nodos más suelo. No identificar una matriz 5×5 local con una función de transferencia sin memoria.

## Banco congelado antes de medir

Tres historias hi/lo del descriptor02: primer rechazo Q6, final Euler fino y final SDIRK01. Cuatro linealizaciones por historia: DC y Euler a 125 ns, 30,517578125 ps y 7,62939453125 ps. Son 12 sistemas locales; no nuevas trayectorias ni una extensión del dominio Rust. Usar cargas/incidencias Decimal100 originales; LU escalado propio con múltiples RHS para condensación, pivotes absolutos heredados para solve completo independiente. Comparar todas las 134 correcciones, residual completo reconstruido, corriente/retorno de los puertos, 5 columnas de tensión y 5 de historia frente a 37 filas con puertos impuestos. Gate algebraico absoluto 1e−60, usando V para nodos, A para ramas/residuos nodales, V para restricciones, y unidades de cada derivada. Este gate verifica identidades Decimal100, no precisión de binary64 ni sustituye los gates eléctricos heredados.

Contrastar la subred lineal de modo común con derivación propia: u=(p+ +p−)/2−(V+ +V−)/2, iL2=−G4·u, v7=p+ +EOS+R13·G4·u−L2·(iL2−hL2)/dt. DC omite el término inductivo; Euler retiene su historia. Verificar valor afín, cinco columnas de tensión y cinco de memoria contra la tarjeta. Constantes leídas de la tarjeta original por nombre, sin fit. L2·G4 tiene unidades de tiempo; el aporte proporcional a du/dt impide reemplazar esta subred por una ganancia estática. Esto no demuestra la causa completa del rechazo LTE.

Conservar fuentes/hash antes/después, datos completos por caso, primer fallo y repetición sin cambios antes de corregir. Si una partición es singular, registrar rechazo; no introducir gmin o cambiar tolerancias. Cero SPICE/audio nuevos; no reducir L3/C5, no promover producción, no afirmar refinamiento, períodos completos, física, heap o RT. Siguiente puerta: resolver raíces no lineales cargadas con esta partición y luego definir error de cualquier cambio dinámico frente a la tarjeta completa.
