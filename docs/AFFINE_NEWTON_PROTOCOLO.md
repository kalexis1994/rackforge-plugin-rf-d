# Una preparación de Newton para la corrección física completa

## Contrato previo

Partir de la unión [sin segundo stamp DC](SPLIT_LADDER_RESULTADOS.md).
Mismas leyes/tarjetas nominales CA3046/SVC-204D, SVC-9 pp.9/13/19 y p.10,
118 nodos físicos, 111 coordenadas por etapa, cargas/puertos e historial
HIGH/LOW. Rama 40–100 ms, KEY OFF 75 ms; VCO/semilla sin recalibrar.
Directo vigente activo hasta pasar precisión y costo. Sin dominio nuevo.

Construir el Newton desde los J/M físicos actuales, no desde una respuesta
guardada de otro estado. Con x=T[z,y], comprobar M·Tz=Tzᵀ·M=0. Separar
por etapa A=Jzz, C=Jzy, D=Jyz, E=Jyy. Factorizar A (7×7), preparar
S=E−D A⁻¹C y la masa retenida en el solver 222. Para cualquier RHS físico
b, transformar bz=Tzᵀb, by=Tyᵀb, y calcular:

`p=A⁻¹bz`, `S·dy=by−D·p`, `dz=p−A⁻¹C·dy`, `dx=Tz·dz+Ty·dy`.

Las dos etapas se unen con B original. El residual algebraico bz no se
descarta, aunque sea pequeño. El soporte de C se inspecciona desde los
coeficientes actuales y no se aprende de una escena. Mantener reacciones
de los cinco puertos, todas las cargas y las identidades TAIL/VCA_BASE.

Una preparación toma prestadas etapas y workspace; mientras existe no
pueden cambiarse esos datos ni reinicializarse los factores. Permite varios
RHS y refinamientos del mismo operador. Un fallo no entrega un token válido.
Después de cambiar etapa/h/receta se prepara de nuevo. Los factores numéricos
no persisten como cache entre puntos. El procesamiento conserva arrays fijos,
sin heap/IO/locks/serialización. Sólo las herramientas de laboratorio usan
la referencia completa y la instrumentación.

Retener un CSR del operador físico 236 con sus coeficientes reales y
residual compensado. Cada solución dx debe pasar backward ≤1e-11; máximo
tres refinamientos físicos, reutilizando la misma preparación reducida.
Conservar también el backward/refinamiento del solver 222. Rechazar escala
de normalización no finita, además de entradas/productos/factores no finitos.
La salida de Newton exige residual físico 1 pA y corrección física 2 nV;
el estimador sigue examinando los 118 nodos reconstruidos.

## Gates y ejecución

- 24 pares ROOT/48 etapas admitidas: 24 RHS por par (residual real, 14
  incidencias en filas algebraicas de ambas etapas, ocho puertos y una
  mezcla determinista), 576 direcciones frente al solve completo vigente.
  Gate 2 nV+1e-7·abs(ref), incluyendo casos bz no nulo. Coeficientes físicos
  contra fórmula original; comprobar también masa sin carga en z.
- Resolver varios RHS desde un solo préstamo y demostrar mismo resultado
  al preparar de nuevo. Probar no finitos, singularidad, masa en z, enlaces
  no representables, capacidad, overflow y recuperación válida exacta.
- Dos trayectorias 64/32 µs, 481 observaciones cada una: conservar gates
  del directo (nodos/estados 20 µV+2e-6·abs(ref), cargas 2 nA+2e-5·abs(ref),
  J7 RMS 0,1 %, pico 0,3 %, media 1 µV), voz reservada y refinamiento.
- Ocho replays, diez rechazos atómicos y heap cero en el candidato.
  Auditoría independiente de 24 pares/5712 filas originales: 20 pA/2 nV.
- Control directo fresco 32 µs y unión anterior fresca como comparación
  funcional; compiler/rlib/flags iguales, sin timers para admisión. Ratio
  candidato/directo ≤0,90, sin cambiar gate si sólo supera a otro rechazado.

Registrar preparaciones, RHS reutilizados y refinamientos; distinguirlos
de pasos aceptados y del costo de una trayectoria. Cualquier perfil mide
su ubicación explícita e incluye replays si corresponde. Un menor número
de factorizaciones no acredita por sí solo velocidad o RT.

Usar `tmp/lab-current`, retirando binarios al guardar recibos. Sin WAV,
Cargo, rlib o inputs privados de sonido nuevos. Fallos con fuentes/entrada
y replay antes de corregir. Referenciar por commit/ruta/SHA los inputs
públicos inmutables; guardar imágenes de fuentes nuevas/editadas para
evitar incluir recibos grandes recursivamente. Presupuesto de recibos 8 MiB,
excluyendo el cierre QA. Tests Rust heredados por identidad, sin simular
su reejecución ni afirmar fidelidad de una unidad física.
