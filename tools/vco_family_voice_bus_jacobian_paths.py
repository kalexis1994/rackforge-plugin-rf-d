"""Generate the direct audio stamp and bounded substitutions from frozen laws."""
from prepare_hybrid_stamp import once


def audio(source):
    source = once(source, "fn natural_jacobian(j:&[[f64;N];N])->[[f64;N];N]{*j}\n", "")
    source = once(source, "struct Stamp<'a,const FULL:bool> {", "struct Stamp<'a, 'j, const FULL: bool, const W: usize> {")
    source = once(source, "    j: [[f64; N]; N],", "    j: &'j mut [[f64; W]; W],")
    source = once(source, "impl<'a,const FULL:bool> Stamp<'a,FULL>", "impl<const FULL: bool, const W: usize> Stamp<'_, '_, FULL, W>")
    source = once(source, "fn evaluate<const FULL:bool>(", "fn evaluate<const FULL: bool, const W: usize>(")
    source = once(source, """) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut s = Stamp::<FULL> {
        x,low,
        r: [0.0; N],
        j: [[0.0; N]; N],
    };""", """    j: &mut [[f64; W]; W],
) -> Result<[f64; N], StepError> {
    let mut s = Stamp::<FULL, W> { x, low, r: [0.; N], j };""")
    source = once(source, "s.j[POSITION[49]] = [0.0; N];", "s.j[POSITION[49]][..N].fill(0.);")
    source = once(source, "s.j.iter().flatten().any(|v|!v.is_finite())",
                  "s.j[..N].iter().any(|row| row[..N].iter().any(|v| !v.is_finite()))")
    source = once(source, "    Ok((s.r, s.j))", "    Ok(s.r)")
    return once(source, """ pub fn linearize<const FULL:bool>(self,x:&[f64;N],low:&[f64;N])->Result<([f64;N],[[f64;N];N]),StepError>{
  if x.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
  let(r,j)=evaluate::<FULL>(x,low,self.p,self.conversion,self.headphone,self.b,self.metadata)?;Ok((r,natural_jacobian(&j)))
 }""", """ /// The caller owns a freshly cleared stage matrix with at least 66 nodes.
 pub fn linearize_into<const FULL: bool, const W: usize>(
     self, x: &[f64; N], low: &[f64; N], jac: &mut [[f64; W]; W],
 ) -> Result<[f64; N], StepError> {
     const { assert!(W >= N); }
     if x.iter().any(|v| !v.is_finite()) {
         return Err(StepError::InvalidInput);
     }
     evaluate::<FULL, W>(x, low, self.p, self.conversion, self.headphone, self.b, self.metadata, jac)
 }""")


def chain(source):
    source = once(source, "let low=std::array::from_fn(|k|now.low[k]);let(r,j)=p.audio.linearize::<FULL>(&x,&low)?;",
                  """let low = std::array::from_fn(|k| now.low[k]);
 let mut jac = [[0.; N]; N];
 let r = p.audio.linearize_into::<FULL, N>(&x, &low, &mut jac)?;""")
    return once(source, " let mut jac=[[0.;N];N];if FULL{for a in 0..66 {jac[a][..66].copy_from_slice(&j[a]);}}\n", "")


def triangular(source):
    source = once(source, "border:[[f64;4];N],cross:[[f64;N];4]}",
                  "border:[[f64;4];N],cross:[[f64;N];4],lower_first:[usize;N],upper_end:[usize;N]}")
    source = once(source, "border:[[0.;4];N],cross:[[0.;N];4]}}",
                  "border:[[0.;4];N],cross:[[0.;N];4],lower_first:[0;N],upper_end:[0;N]}}")
    source = once(source, "let diagonal=self.lu.a[col][col];",
                  """let diagonal=self.lu.a[col][col];
            self.upper_end[col] = end;
            self.lower_first[col] = self.lu.a[col][..col].iter()
                .position(|value| *value != 0.).unwrap_or(col);""")
    start = source.index("    fn forward(&self")
    end = source.index("\n}\nconst CAPACITY", start)
    source = once(source, source[start:end], """    fn forward(&self, b: [f64; N], rhs: &mut [f64; 4]) -> Result<[f64; N], StepError> {
        let mut x = [0.; N];
        for i in 0..N {
            let mut v = b[self.lu.perm[i]];
            // A finite nonzero or +0 is unchanged by subtracting either signed zero.
            let start = if v.to_bits() == (-0.0_f64).to_bits() { 0 } else { self.lower_first[i] };
            for k in start..i {
                v -= self.lu.a[i][k] * x[k];
            }
            if !v.is_finite() {
                return Err(StepError::SingularJacobian);
            }
            x[i] = v;
        }
        for (port, value) in rhs.iter_mut().enumerate() {
            for k in 0..N {
                *value -= self.cross[port][k] * x[k];
            }
        }
        Ok(x)
    }

    fn reconstruct(&self, mut x: [f64; N], ports: [f64; 4]) -> Result<[f64; N], StepError> {
        for i in (0..N).rev() {
            let mut v = x[i];
            let end = self.upper_end[i];
            for k in i + 1..end {
                v -= self.lu.a[i][k] * x[k];
            }
            if v.to_bits() == (-0.0_f64).to_bits() {
                for k in end..N {
                    v -= self.lu.a[i][k] * x[k];
                }
            }
            for k in 0..4 {
                v -= self.border[i][k] * ports[k];
            }
            x[i] = v / self.lu.a[i][i];
            if !x[i].is_finite() {
                return Err(StepError::SingularJacobian);
            }
        }
        Ok(x)
    }""")
    for block, mapping in (("contour", "CONTOUR"), ("audio", "AUDIO")):
        old = f"self.{block}.forward({mapping}.map(|i|b[i]),&mut rhs)"
        source = once(source, old, old + "?")
    for block, values in (("contour", "c"), ("audio", "a")):
        old = f"self.{block}.reconstruct({values},p)"
        source = once(source, old, old + "?")
    return source


def zero_cross(source):
    return once(source, "self.cross[p][col]=factor;",
                """self.cross[p][col] = factor;
                // Uneliminated exterior entries can only hold +0.
                if factor == 0. {
                    continue;
                }""")
