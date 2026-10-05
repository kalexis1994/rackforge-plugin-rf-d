# Próximo bloque: preparar acciones sin cambiar sus certificados

La continuación compartida renueva una prueba uniforme por bloque, pero
cada macrocelda conserva ocho acciones completas. El helper de referencia
vuelve a restaurar X, escalas y E en cada subcelda. Estudiar preparación
única de esos datos para disminuir trabajo repetido del laboratorio.

1. Congelar antes de medir banco, orden, entradas y controles. Fuente: los
   artefactos completos de la continuación, con sus SHA verificados. Medir
   tiempos de la referencia y la variante en el mismo entorno; no inferir
   una mejora de tiempo a partir de conteos.
2. Mantener intacto el helper original como control. La variante debe
   preparar X, D, E, q y cotas por fila una sola vez por identidad completa
   del certificado. No reutilizar la preparación si cambia recinto, radio,
   escala o precondicionador.
3. Conservar orden de operaciones racionales, redondeos dirigidos, signo de
   polinomios, restos independientes, primera corrección, cola e intersección.
   Comparar todos los certificados y presupuestos con bytes canónicos
   idénticos, además de dimensiones, dominios y gates. No usar sólo picos.
4. Probar rechazo de identidades o dimensiones distintas y RHS/duraciones
   alterados. Una cache por dirección de objeto no identifica matemáticamente
   el certificado. No modificar fuentes o evidencia congeladas.
5. Reproducir el banco completo, registrar cualquier fallo antes de corregir,
   ampliar corpus y documentar alcance. Preparar el siguiente banco temporal
   sólo después de comprobar esta equivalencia.

Esto sería una optimización del laboratorio offline. No admite asignaciones,
serialización o cache en el hilo de audio ni prueba deadline del plugin.
El siguiente soporte físico requiere dominio y cierre nuevos, aunque su
certificación se ejecute con menos restauraciones de datos.
