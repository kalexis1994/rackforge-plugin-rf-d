# Próximo corte: primer soporte continuo desde el anclaje post-KEY

El [estado publicado y prefijo](BIESTABLE_POST_KEY_ARRANQUE_RESULTADOS.md)
aportan un límite derecho acotado y 512 intervalos discretos con procedencia
propia. No prueban error continuo. Este plan no fija todavía un protocolo
de radios, reconstrucción o subdivisiones para nuevas mediciones.

## Separar arranque de interpolación multihistorial

El primer intervalo sólo tiene dos estados reales. Elegir y congelar una
reconstrucción de orden declarado que use el origen post-KEY; no inventar
dos historiales previos para aplicar el polinomio antiguo de cuatro estados.
Conservar el salto entre DC y evento aparte del soporte a la derecha.

Una opción es reconstruir potenciales y cargas con extremos y tangentes
consistentes. Las 25 tasas auxiliares de t=0+ ya existen, pero no son vdot.
Si se requieren tangentes de potencial, derivar las restricciones y KCL
con KEY constante: el descriptor H permite resolver (vdot,yddot) con RHS
(0,-ydot). Validar unidades y condiciones de diferenciabilidad de junturas.
No confundir ydot con vdot ni con un estado previo aceptado.

Para el extremo siguiente, medir el desajuste entre memoria publicada y
ley ideal Q(v), incluyendo el evaluador que usa high redondeado. Si se
resuelve un punto/tasa consistente a carga fija, declararlo como otro
experimento offline con seeds, dominio y radios previos; conservar estado
original, corrección y error del adapter por separado. No sustituir la
trayectoria aceptada sin identidad y cota de publicación nuevas.

## Anclaje, residuales y recinto autosuficiente

La caja de 25 cargas iniciales permanece la del DC; su error ponderado es
~147,95 pV en sus pesos propios. Convertirla explícitamente a los pesos
y métrica del primer soporte, conservando ese mismo vector físico de error.
El error nodal publicado ~37,51 nV no sustituye la cota de carga ni autoriza
usar presupuestos de ventanas no contiguas.

Encerrar el interpolante completo, cargas constitutivas, exponentes y
residual integrado sobre todo el primer intervalo. Incluir derivadas,
error de publicación, dependencia de capacitancias y transiciones de ley.
Probar que la propagación propuesta permanece en el recinto usado para
su Jacobiano y resto; no asumir el tubo al usarlo para demostrar su cota.
Conservar fallos y todos los parámetros nominales sintéticos.

Una cota tangente o una KCL discreta pequeña no cierra el error no lineal
del DAE. Registrar origen, intervalo y norma realmente cubiertos. Cuando
el primer tramo esté probado, ampliar por interfaces contiguas y pagar
cambios de norma. Mantener inventario de huecos y región reset separada.

## Alcance

La coincidencia de dos arranques dentro de ~3,6 pV no estima el error común
frente al modelo. No cambiar el gate global 1 mV ni promover resultados
de trayectoria nominal a hardware. Física, voz completa y deadline siguen
su proceso independiente.
