# Protocolo: cobertura temporal, linaje y conversión de normas

Congelar helper, productor y protocolo antes de medir. No ejecutar nuevos
solves, buscar otra P ni retocar resultados anteriores. Auditar la trayectoria
compensada fija desde DC y las ocho referencias propias N2/N4, con identidad
del historial entrante, estado previo completo, reloj y estado final.
La continuidad numérica no prueba el error del estado inicial físico.

## Cobertura exacta del dominio publicado

Levantar tiempos binarios como racionales exactos, sin volver a sumar dt
para construir extremos. Reproducir por separado el cierre de reloj binario.
Cada caso conserva cuatro historiales de soporte de la muestra 31. El
certificado continuo cubre sólo el intervalo entre los dos últimos tiempos;
los otros dos soportes y el resto de la ventana no reciben esa cobertura.
Comprobar SHA, duración, identidades de los ocho casos y ocho celdas por caso.

Calcular unión y complemento en el dominio completo desde DC por N y
combinados. Fusionar tramos que se solapan o tocan, sin contar dos veces
N2/N4. Registrar por separado soporte de inversa ideal, soporte de métricas
aceptadas y cobertura de error real (aún cero). El rechazo de reset queda
explícito, con sus pruebas de inversa y modos congelados conservadas.

## Conversión de normas en el mismo vector de error

Para cada uno de los seis candidatos aceptados, reconstruir la matriz
G=diag(W_J)*P*diag(W_J)/(4*a²). La norma de junturas es sqrt(e_Jᵀ*G*e_J),
con las mismas coordenadas de carga escaladas por S. Las otras cinco normas
de bloque mantienen W=1. Exigir G simétrica positiva definida y fuente por SHA.

Para todos los 36 pares ordenados, incluidos seis identidades, certificar
||e||dest<=kappa*||e||source. Un superior de kappa² se obtiene con
alpha*Gsource-Gdest positiva definida mediante LDLᵀ racional. Fijar
inferior Rayleigh max_i Gdest_ii/Gsource_ii y superior estricto
||Gdest||infinity*||Gsource^-1||infinity+1, con 32 bisecciones y raíz exterior
de 256 bits. Identidades exactas dan kappa=1 sin queries. Registrar los
30 certificados no triviales, 990 consultas, bracket, factores y raíz.
La conversión de la norma máxima de los seis bloques usa max(1,kappa).

Estos mapas comparan normas de un mismo vector, no errores de dos soluciones
N2/N4 distintas. Tampoco propagan huecos entre ventanas ni validan interfaces
temporales reales. No insertar una conversión donde falta demostrar la
dinámica o el error entrante. El inferior auxiliar es del problema de Gram,
no una cota inferior del error de trayectoria.

## Regresiones y trabajo posterior

Probar unión/complemento racional con solapamiento, contacto y huecos;
rechazar intervalos negativos, vacíos o fuera del dominio. Contrastar linaje
con historial previo, SHA y reloj alterados. Probar normas diagonales con
ratio conocido, identidad y guards; reproducir todas las queries y verificar
la desigualdad en vectores racionales independientes. Auditar todos los
historiales archivados, soportes, fuentes, bytes, rechazos y flags de alcance.
Congelar datos y suite antes de validar; conservar todos los intentos.

Fijar como siguiente etapa una estrategia de cobertura desde DC y reset:
acotar DC y error entrante; reconstruir regiones faltantes y sus residuales;
usar en reset una norma no contractiva declarada y el circuito acoplado;
convertir interfaces realmente contiguas; acotar y propagar resto no lineal.
No inferir inexistencia de toda P por el rechazo de un candidato. No requiere
contracción para obtener un superior finito si el crecimiento está acotado.
1 mV global, física, audio y deadline permanecen abiertos.
