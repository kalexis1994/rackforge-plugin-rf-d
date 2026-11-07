# Recuperación no lineal como puerto compacto

Previo, 2026-11-06. Usar CA-72 como referencia arquitectónica, revisión
d268d22a0af63a881868968abe5442a43d544f9f, docs/circuit/board4.md:
separar la recuperación estática no lineal de sus acoplamientos y cargas.
Implementación nueva derivada del stamp RF-D/SVC-9 Fig.9-11 p.13;
no incorporar código, tablas o ajustes de su recreación hardware.

Mantener perfil nominal R61=200/L1, cutoff .49/.50/.51, VCA1/2=2 V,
puerto OSC1 (BUS-.5*U)/39250, los18 capacitores y todos los retornos.
Los cuatro BJT de recuperación son Q8/Q6/Q7/Q5, nodos16..23 del grafo68.
Usar los mismos IS/beta/Vt de nuestro oráculo Ebers–Moll; mejorar el modelo
de dispositivos sería otra hipótesis, no parte de esta corrección.

## Derivación

Cada unión BE/BC aporta un vector de corrientes D_j y una diferencia de
voltaje E_j*x/Vt. Alrededor del DC, su defecto exacto respecto de G es
n_j(z)=Iexp_dc*(expm1(z)-z). Los ocho defectos reemplazan sólo esos BJT;
el resto del circuito conserva la linealización anterior. Series cerca
de cero para evaluar el defecto sin cancelación. La ley no es un clip
o distorsión insertada en J7. Es exacta para los cuatro BJT del oráculo
condicional, sin prometer exactitud no lineal de ladder/control/otros VCA.

En una etapa BE de SDIRK, L=(G+M/dt)^-1 se prepara fuera de audio.
x=Xhist*qhist+Xu*U-L*D*n(z), z=E*x. Resolver sólo ocho diferencias de
unión con Newton; recuperar q=Ainc*x y corrientes de puerto. Proyectar
matrices a18 cargas y8 uniones antes de procesar, sin solve68 por muestra.
SDIRK2, gamma=1-1/sqrt(2), conserva los pesos y la historia de cargas;
constitución y error temporal se contrastan por separado.

## Gates y mediciones acotadas

1. Contrastar el defecto de corriente con el stamp nativo para perturbaciones
   sólo en nodos16..23:64 direcciones en±1 mV/±50 mV. Error<=1e-12 A
   +1e-10*|I|. Derivadas del solve8 frente a FD relativas1e-5 +1e-10.
2. Comparar etapas del híbrido con Newton68 del MISMO circuito híbrido:
   nodos<=1e-9 V; KCL híbrido<=1e-12 A; q=Ainc*x<=1e-11 V.
   El solve68 independiente comparte G/M/DC y leyes, no es otro oráculo físico.
3. Reutilizar reservas no lineales de nivel de CHARGE_CONTROL en los tres
   cutoff, a=.01/.1/1 V. Gates conservados1 uV nodal,2 nA de puerto,
   J7 RMS .001/pico .003/media1 uV, fallback1 nV. No ajustar con reservas.
   Retener rechazos. Consultar estados/corrientes retenidos al mismo reloj;
   declarar cobertura dispersa donde la rejilla completa fue retirada.
4. Rust/Python<=1e-10 V/1e-14 A. Rechazos de entrada o presupuesto conservan
   estado por bits; retry válido, cero heap. Sólo afirmar los fallos ensayados.
5. Medir núcleo más FIR48 kHz a384 kHz,1200 bloques128, primero incluido,
   objetivo50% de2.6667 ms, sin ningún deadline observado perdido. Cronómetro
   e IO fuera. Si no cabe, conservar rechazo sin escoger otra repetición.

El ensayo fino separa constitución de integración; no trasladar al nuevo
SDIRK la admisión temporal de la variante exponencial anterior. No promover
cutoff dinámico, voz con H128/contornos o hardware por aprobar recuperación.
Un tmp/lab-current, compiler/rlib congelados; procesos<=240 s, export<=32MiB,
recibos<=8MiB sin QA. Aprovechar corpus existente; sin nueva campaña SPICE,
Cargo/cache/WAV o carpetas de muestras. Fuentes,8769 inputs y escucha protegidos.
