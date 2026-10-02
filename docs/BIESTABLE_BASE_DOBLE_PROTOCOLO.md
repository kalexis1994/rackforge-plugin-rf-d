# Base completa de historia doble: protocolo

Declarado el 2 de octubre de 2026 antes de medir. Complementa las
[ocho direcciones no lineales](BIESTABLE_MEMORIA_LARGA_RESULTADOS.md),
sin repetir integración ni reconstruir derivados espaciales.

## Plan y fórmulas

Se congelan los 256 mapas X (94x25) y T (25x25), coeficientes BDF2, anclas
y relojes de las cuatro ventanas de 64 pasos del informe anterior.
Los SHA de fuentes se verifican antes/después. No se modifica ese corpus.

La historia doble tiene 50 coordenadas: primero las 25 memorias actuales,
después las 25 previas. Las cargas mantienen Q/(1 pF), escala numérica
exclusivamente. Para la base lineal E inicial: actual = [I,0], previa =
[0,I]. No son 50 inyecciones físicas finitas de 1 V ni historias aceptadas.

Por intervalo:

```
V = (1+gamma) E_actual - gamma E_previa
N = X V
M = T V
E_previa <- E_actual
E_actual <- M
H = [M; E_previa]
```

Se guardan N 94x50, M 25x50 y las normas espectrales/singular values de
N, M y H 50x50 en los 256 intervalos. La norma 2 y su dirección derecha
máxima describen sensibilidad homogénea del mapa lineal con esta escala,
reloj y trayectoria. Normalizar el signo de la dirección con su componente
de mayor módulo positiva. No existe gate de gain físico ni un umbral
universal para RACE; los máximos por ventana se seleccionan bajo esa regla
declarada, sin limitar cobertura por el resultado.

## Contraste de redondeo

Se repite toda la recurrencia en Decimal **80 y 100 dígitos**. Cada entrada
X/T y los coeficientes gamma y (1+gamma) se levantan exactamente de sus
binary64 originales. La suma (1+gamma) ya redondeada es parte del algoritmo
fijado. Productos Decimal se acumulan en índices crecientes; sólo se omiten
ceros exactos, sin umbrales ni recortes. Se guarda SHA de matrices Decimal
completas expresadas en cadenas, y las matrices de 80 dígitos redondeadas
a binary64. La regeneración puede verificar ambas identidades completas.

Gate en cada N/M: max |binary64-Decimal80 redondeado| /
(1+|Decimal80 redondeado|) < **1e-8**. Matrices redondeadas a 80/100 dígitos
deben coincidir exactamente; conservar diferencias y fallos. No se afirma
aritmética racional de los productos ni exactitud de los coeficientes
frente al circuito físico. La auditoría precedente sólo tiene 12 puntos
espaciales seleccionados y dinámica/contorno compartidos.

## Alcance y fallos

Son **cero solves no lineales nuevos y cero solves espaciales nuevos**.
La base cubre todas las direcciones del operador lineal archivado, sin
validar la respuesta no lineal finita en todas ellas. No se añade fuerza
de truncamiento, defecto exacto ni término afín: sensibilidad homogénea no
es cota global del error temporal ni explicación exclusiva de sus fallos.

Un resultado no finito detiene esa ventana y conserva las dos matrices
entrantes. Un fallo de contraste permanece en el informe sin modificar
gate, precisión, coordenadas o mapas. No se admite refinamiento temporal,
conmutación física, audio ni deadline. El gate temporal de 1 mV sigue abierto.

[Productor](../tools/loudness_latch_bdf_static_precision_memory_basis.py).
