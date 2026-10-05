# Protocolo: continuación contigua con referencias curvas

Modelo documental CA3046 nominal y sintético. Fuente: octavo intervalo
aceptado del informe curved_reference, selección [1,1]. Usar sólo sus
22 memorias finales reales, referencia curva, reloj y P identificados.

## Banco y parada fijados antes de medir

Intentar índices 8 a 15 como máximo (ocho soportes nuevos), empezando
≈25→37,5 µs. Las historias reales fijan pasos de ≈12,5 µs desde ese
punto; el límite llegaría a ≈125 µs. Una variante c7_bubble, modo
direct_and_memory; radios en orden 0,1/1 µV. Completar ambos radios, elegir el
primer cierre estricto y transportar sólo sus 22 errores finales.
Detenerse en el primer soporte sin selección. No evaluar intervalos
posteriores al hueco. Si se alcanza el límite, declarar ese límite.

El banco conserva el radio de admisión de 1 µV y el control negativo
de 0,1 µV. No repite las ramas de 10 µV no soportadas del experimento
anterior; tampoco las usa para transportar memoria. Este banco se fija
antes de medir, sin cambiar los gates numéricos o sus dominios.

Conservar sys.set_int_max_str_digits(0), kernel <=4096, exponencial <=45
y gates previos: KCL 10 pA, corrección 10 nV, rama lineal 10 fV,
backward 1e-10, objetivo global 1 mV. No modificar circuito o integrador.

## Referencias y certificados futuros

En cada soporte, reconstruir la afín con sus dos historias publicadas.
Evaluar el descriptor Decimal100 en su punto medio y obtener X candidata
binary64 finita. Del RHS polinómico completo de 119 ecuaciones derivar
f0=-X[114,:]*R_poly, A=(f0(0)-f0(1))/2 y p=A*h*u*(1-u), en tiempo físico.
Potenciales: x_affine-X_v,C7*p; memoria C7: y_affine+p. Recalcular las
21 cargas/restricciones lineales (RC incluida) y cuatro Q(v) por piezas.
Conservar endpoints exactos y la ley constitutiva, con grado completo.

Renovar ocho precondicionadores de celda, residual, covers de Hbar,
inversas completas, tasas en P fija y acciones dirigidas del RHS en
ocho subceldas por celda. Nueve precondicionadores candidatos por soporte,
incluyendo la dirección de la burbuja. No reutilizar inversas, acciones
o tasas del octavo soporte. P fija conserva la norma y sus conversiones.
Acotar todos los restos uniformes, constitutivos e incertidumbre de Hbar.

Validar continuidad de potencial, memoria lineal y constitutiva antes de
cada transporte. Identificar hash del resultado entrante, pico conocido,
22 errores individuales y métrica. Separar pico local y acumulado. Una
burbuja candidata no prueba consistencia ni cambia la trayectoria publicada.

## Archivo por soporte y manifiesto completo

Guardar cada banco completo en curved_prefix_interval_NNN.json.gz,
con esquema, índice, reloj, fuentes, referencias, interfaces y todas las
ramas/certificados. El manifiesto sólo se publica tras terminar el prefijo
acotado o su primer hueco. Sus referencias incluyen ruta exacta, longitud,
SHA comprimido y SHA canónico; rechazar otra ruta, bytes o identidad.
Cada archivo conserva las fuentes previas a medir. El manifiesto incorpora
también los hashes de todos sus archivos. No sobrescribir destinos existentes.

Si se interrumpe la ejecución, los archivos completos ya escritos son
evidencia de soportes identificados; no se consideran una publicación del
prefijo sin su manifiesto final. Preservar el intento antes de resolverlo.
Esta división controla almacenamiento/memoria y no reduce el certificado.

## Verificación y alcance

Congelar productor/protocolo antes de medir; datos, tests y validator antes
de validar. Reproducir referencias, RHS completo, recintos, inversas,
tasas, acciones y cierres en todos los soportes, incluidos rechazos.
Probar soportes de duraciones distintas con solución cuadrática exacta,
interfaces, reloj, conversión RC/Q, transporte y parada en el hueco.
Probar cambio de bytes/ruta de un archivo y destinos existentes.
Ampliar corpus con manifiesto, archivos y recibos; conservar fallos.

Hardware, sonido vintage, trayectoria completa, 1 mV global, voz, audio
nativo y deadline conservan sus gates independientes.
