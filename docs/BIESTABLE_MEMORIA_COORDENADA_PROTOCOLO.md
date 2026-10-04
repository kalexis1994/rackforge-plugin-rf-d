# Protocolo: memoria saliente por coordenada y comparación de 22 grupos

Mismo modelo, estados, reloj, reconstrucción y residual. Reutilizar
el primer intervalo realmente certificado y los recintos del segundo
intento fallido, sin solves de circuito, candidatos de inversa ni métricas
nuevas. Reconstruir las 24 inversas exteriores completas por certificado
(8 del primer intervalo seleccionado y 16 del segundo), con SHA verificado.
Conservar P, normalización y cotas de tasa de junturas del modo retenido.
Identificar cada certificado de tasa reutilizado por SHA y fuente.

## Refinamiento soportado por una trayectoria ya probada

Para z_i=w_i*e_i de las 21 cargas lineales, usar diagonal firmada
mu_i=sup(-Hinv_ii) y ganancias desde otras coordenadas, con normas duales
P^-1 para junturas. En cada celda del PRIMER intervalo, los seis picos
de grupo ya certificados acotan todos esos errores. No usar una trayectoria
rechazada como soporte para refinar el anclaje.

Inyección L1 individual = forcing_i_L1 + h*sum(gain_ik*peak_group_k),
excluyendo la propia coordenada. Kernel escalar exterior E_i/P_i del
helper existente: endpoint <= E_i*initial_i + P_i*injection_L1.
Intersectar con la cota saliente de su grupo del certificado anterior,
sólo porque ambos acotan el mismo error en la misma norma. Propagar cada
coordenada a la siguiente celda desde ese resultado. Registrar diagonal,
inyección, kernels, bruto, cota anterior y mínimo. Junturas conservan su
cota cuadrática final original, sin convertirla en cotas físicas por carga.

## Segundo intervalo y banco fijo

Partición: 21 coordenadas lineales individuales más un grupo cuadrático
de cuatro junturas. Construir comparación Metzler de 22 grupos: diagonales
lineales firmadas, acoplamientos individuales y duales completos, diagonal
de junturas reutilizada; forcing L1, ganancias nodales y directo completos.
No usar ganancias de la partición anterior tras cambiar grupos.

Radios 0,1; 1; 10 µV en el orden anterior. Rechazar previamente cuando
la cota nodal entrante no cabe. Dos modos por radio elegible, en orden:
anclaje agrupado anterior levantado a 22 grupos; anclaje refinado por
coordenada. Ejecutar ambos y conservar todos los resultados; elegir el
primer par aceptado. Los dos usan EXACTAMENTE las mismas métricas finas,
recintos, residual y P. Comparar también con el presupuesto histórico
de seis grupos sobre ese radio, sin modificar su evidencia.

Cerrar sólo por inclusión nodal estricta, origen incluido, descriptor
medio invertible y dominio/continuación del protocolo original. La memoria
entrante refinada es conocida, no una tolerancia propuesta. Si cierra,
certificar únicamente el segundo intervalo y su unión con el primero;
si no, mantener 195,3125 ns de cobertura real y el hueco original.

Validar ley escalar conocida, intersección en la misma coordenada,
conversiones duales manufacturadas, una sucesión no lineal conocida,
anclaje anisótropo y forcing tardío. Reproducir las inversas y sus hashes,
los 168 refinamientos escalares, métricas, kernels, cierres y selección.
Congelar fuentes antes de medir; datos/tests antes de validar; conservar
intentos y recuperar todo el corpus. Global 1 mV, circuito físico, voz
completa y deadline mantienen sus gates independientes.
