# Conformidad nominal con referencias existentes

Fijado antes de medir el nuevo banco nativo. Sólo C4=10 pF nominal,
R8=0,5, R11=500 ohm, CV todos−2,1 V, mixer/rail load=0, nivel=0,5,
contactos 3/10, 30 ms y asentamiento15 ms. Comparar ambos perfiles
Radau250/125 contra las escenas Gear2/Trap2 a125 ns del banco SPICE
ya validado. No ejecutar nuevos procesos SPICE ni recalibrar trims.

Conservar identidad del banco comprimido y su recibo de validación
posterior (el gate HIGH/LOW inicial falló por el adaptador, no por estas
escenas). Confirmar las fronteras nominales/escenas, procesos completos
y hashes antes/después de sus fuentes originales. Reusar mediciones
archivadas de la validación anterior; no contar esa herencia como nuevo
solve. Frecuencia<=1 cent, extremos saw/tri/rect<=5 mV, idénticos al
criterio previo. Comparación de fase sólo diagnóstica; no equivale a
error al mismo reloj. RAMP, referencia−4 V, medios de corrientes y
duty se informan sin imponer nuevos umbrales a posteriori.

Pasar sólo admite conformidad numérica de estas observaciones nominales
entre métodos. CV/trims reservados, C4=100 pF, carga activa y física
vintage siguen abiertos. Los nuevos contrastes de raíces son Decimal100
locales; este contraste de ciclos usa otra trayectoria y otro método.
