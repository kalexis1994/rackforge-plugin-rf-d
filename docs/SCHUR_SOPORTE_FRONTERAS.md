# Soporte exacto para fronteras y sustituciones, antes de medir

2026-10-13. Las directivas de constructores no pasan utilidad:
mediana0.853485×, con las cinco rondas por debajo de1. Preservar variante,
fuentes y resultado; no elegirla para la trayectoria.

El perfil también registra8752 RHS64 y416 RHS330 (tiempos anidados
22.187/29.455 ms). La preparación contiene validación de fronteras y
movimientos cuyo costo no está aislado. Ensayar dos recorridos que
aprovechan ceros exactos, sin atribuirles previamente esa diferencia:

1. Validar acoplamientos interiores recorriendo el soporte completo de J
   ya construido. Para cada entrada (i,k), verificar dueño interior de i
   y de k contra sus terminales documentados. Equivale a comprobar ambas
   direcciones de cada fila interior; evita consultar J[k,i] por columnas.
   Mantener rechazo de todos los coeficientes extraños, sin umbral.
2. En las sustituciones L/U, omitir el producto por coeficiente cero sólo
   cuando el acumulador es finito y distinto de cero y el valor multiplicado
   es finito. Restar cualquier cero con signo conserva entonces el mismo
   acumulador binary64. Si el acumulador es ±0 o hay un no finito, ejecutar
   la operación original. Conservar orden de todos los demás productos.

Partir del solver anterior sin las directivas de inline del intento fallido.
No cambiar factores, pivotes, capacidad4096, tres refinamientos, errores,
gate1e-11, estados, puertos o cargas. Exigir identidad completa de raíces
y de396 J/b/correcciones, y las doce regresiones. Añadir controles de
ceros con signo y no finitos de la sustitución. Benchmark y confirmación
siguen el contrato de costo original (confirmar una sola vez si1<mediana≤1.10).
