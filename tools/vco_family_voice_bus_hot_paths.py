"""Generate the two exact hot-path experiments from the retained sources."""
from prepare_hybrid_stamp import once


def matrix(source):
    return once(source, "    pub fn complete(&self)", """
    /// A single-owner row arrives in global column order.
    pub fn push_sorted(
        &mut self, row: usize, entries: impl Iterator<Item = (usize, f64, f64)>,
    ) -> Result<(), StepError> {
        if row != self.next || row >= N {
            return Err(StepError::InvalidInput);
        }
        let start = self.count;
        let mut end = start;
        for (column, dc, mass) in entries {
            if dc == 0. && mass == 0. {
                continue;
            }
            if !dc.is_finite() || !mass.is_finite() || end == CAPACITY {
                return Err(StepError::InvalidInput);
            }
            self.columns[end] = column as u16;
            self.dc[end] = dc;
            self.mass[end] = mass;
            end += 1;
        }
        self.rows[row] = start;
        self.rows[row + 1] = end;
        self.count = end;
        self.next += 1;
        Ok(())
    }

    pub fn complete(&self)""")


def graph(source):
    start = source.index("        for a in 0..N{let mut row=Row::new();")
    end = source.index("\n    }", start)
    return once(source, source[start:end], """        // Invert the unique audio column map in physical-column order.
        const AUDIO_COLUMNS: [(usize, usize); 68] = {
            let mut columns = [(0, 0); 68];
            let mut destination = 0;
            let mut physical = 0;
            while physical < N {
                let mut local = 0;
                while local < 68 {
                    if chain_index(local) == physical {
                        columns[destination] = (physical, local);
                        destination += 1;
                    }
                    local += 1;
                }
                physical += 1;
            }
            assert!(destination == 68);
            columns
        };
        for a in 0..54 {
            let entries = dual.j[a].iter().copied().zip(dual.mass[a]).enumerate()
                .map(|(column, (dc, mass))| (column, dc, mass));
            s.tangent.push_sorted(a, entries)?;
        }
        // Each shared row retains the contour stamp and the original audio sum.
        for a in 54..56 {
            let mut row = Row::new();
            for b in 0..56 {
                row.set(b, dual.j[a][b], dual.mass[a][b])?;
            }
            let local = AUDIO_ROW[a];
            for b in 0..68 {
                row.add(chain_index(b), audio.dc_jacobian[local][b], audio.mass_over_h[local][b])?;
            }
            s.tangent.push_row(a, &mut row)?;
        }
        for a in 56..N {
            let local = AUDIO_ROW[a];
            let entries = AUDIO_COLUMNS.into_iter().map(|(column, b)| {
                let dc = audio.dc_jacobian[local][b];
                let mass = audio.mass_over_h[local][b];
                // Row::add on an empty row keeps +0 for an absent contribution.
                (column, if dc == 0. { 0. } else { dc }, if mass == 0. { 0. } else { mass })
            });
            s.tangent.push_sorted(a, entries)?;
        }""")


def solver(source):
    start = source.index("        self.lu.perm=std::array::from_fn")
    end = source.index("        if self.lu.a.iter()", start)
    source = once(source, source[start:end], """        self.lu.perm = std::array::from_fn(|i| i);
        if self.scale.contains(&0.) {
            return Err(StepError::SingularJacobian);
        }
        for col in 0..N {
            let mut pivot = col;
            let mut best = 0.;
            // Keep the logical search order and its first-winner tie rule.
            for logical in col..N {
                let row = self.lu.perm[logical];
                let value = self.lu.a[row][col];
                if value == 0. {
                    continue;
                }
                let quality = value.abs() / self.scale[row];
                if quality > best {
                    best = quality;
                    pivot = logical;
                }
            }
            if best < 1e-12 {
                return Err(StepError::SingularJacobian);
            }
            self.lu.perm.swap(col, pivot);
            let pivot_row = self.lu.perm[col];
            let (before, at_and_after) = self.lu.a.split_at_mut(pivot_row);
            let (row, after) = at_and_after.split_first_mut().unwrap();
            let end = row.iter().rposition(|value| *value != 0.).unwrap() + 1;
            let diagonal = row[col];
            let upper = self.border[pivot_row];
            let coefficients = &row[col + 1..end];
            for &physical in &self.lu.perm[col + 1..] {
                let current = if physical < pivot_row {
                    &mut before[physical]
                } else {
                    &mut after[physical - pivot_row - 1]
                };
                if current[col] == 0. {
                    continue;
                }
                let factor = current[col] / diagonal;
                current[col] = factor;
                for (value, coefficient) in current[col + 1..end].iter_mut().zip(coefficients) {
                    *value -= factor * coefficient;
                }
                for (value, coefficient) in self.border[physical].iter_mut().zip(upper) {
                    *value -= factor * coefficient;
                }
            }
            for (cross, exterior) in self.cross.iter_mut().zip(outer.iter_mut()) {
                let factor = cross[col] / diagonal;
                cross[col] = factor;
                for (value, coefficient) in cross[col + 1..end].iter_mut().zip(coefficients) {
                    *value -= factor * coefficient;
                }
                for (value, coefficient) in exterior.iter_mut().zip(upper) {
                    *value -= factor * coefficient;
                }
            }
        }
""")
    source = once(source,
                  "let mut v=b[self.lu.perm[i]];for k in 0..i{v-=self.lu.a[i][k]*x[k];}",
                  "let row=self.lu.perm[i];let mut v=b[row];for k in 0..i{v-=self.lu.a[row][k]*x[k];}")
    return once(source,
                "let mut v=x[i];for k in i+1..N{v-=self.lu.a[i][k]*x[k];}for k in 0..4{v-=self.border[i][k]*p[k];}x[i]=v/self.lu.a[i][i];",
                "let row=self.lu.perm[i];let mut v=x[i];for k in i+1..N{v-=self.lu.a[row][k]*x[k];}for k in 0..4{v-=self.border[row][k]*p[k];}x[i]=v/self.lu.a[row][i];")


def thin_graph(source):
    start = source.index("    if FULL{\n        // Source map")
    end = source.index("    if s.dc.iter()", start)
    assembly = source[start:end].replace("s.tangent.", "tangent.")
    source = once(source, source[start:end], "    let tangent = build(&audio, &dual)?;\n")
    source = once(source, "pub struct Parts{pub dc:[f64;N],pub dq:[f64;N],pub now:State,pub tangent:Tangent}",
                  "pub struct Parts<T = Tangent>{pub dc:[f64;N],pub dq:[f64;N],pub now:State,pub tangent:T}")
    signature = "pub fn parts<const FULL:bool>(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<Parts,StepError>{"
    source = once(source, signature, """fn assemble<const FULL: bool, T>(
    p: Parameters, old: State, delta: State, c: Controls, h: f64, t: f64,
    build: impl FnOnce(&chain_charge::Parts, &contour::Parts<FULL>) -> Result<T, StepError>,
) -> Result<Parts<T>, StepError> {""")
    source = once(source, "now,tangent:Tangent::new()", "now,tangent:()")
    source = once(source, "    Ok(s)\n}", "    Ok(Parts { dc: s.dc, dq: s.dq, now, tangent })\n}")
    return source + """
#[inline(always)]
""" + signature + """
    assemble::<FULL, Tangent>(p, old, delta, c, h, t, |audio, dual| {
        let mut tangent = Tangent::new();
""" + "\n".join("    " + line for line in assembly.rstrip().splitlines()) + """
        Ok(tangent)
    })
}

#[inline(always)]
pub fn residual_parts(
    p: Parameters, old: State, delta: State, c: Controls, h: f64, t: f64,
) -> Result<Parts<()>, StepError> {
    assemble::<false, ()>(p, old, delta, c, h, t, |_, _| Ok(()))
}
"""


def thin_voice(source, profiled):
    start = source.index("    let bus = chain.each_ref()")
    end = source.index("    for j in 0..2", start)
    boundary = source[start:end]
    observe_bus = "    let bus = chain.each_ref().map(|s| s.now.high[BUS] + s.now.low[BUS]);\n"
    observe = "    let (phase, ports) = observe(family, phase, h, bus)?;\n"
    source = once(source, boundary, observe_bus + observe)
    source = once(source, "pub struct Stages {\n    pub chain: [graph::Parts; 2],",
                  "pub struct Stages<T = crate::incidence::Tangent> {\n    pub chain: [graph::Parts<T>; 2],")
    source = once(source, "pub fn residual(stages: &Stages)", "pub fn residual<T>(stages: &Stages<T>)")
    call = "residual_trial(family, p, old, phase, trial, controls, h)"
    if profiled:
        call = f"crate::cost::measure(1, || {call})"
    source = once(source, """                stages::<false>(family, p, old, phase, trial, controls, h)
                    .is_ok_and(|check| maximum(&residual(&check)) < norm)""",
                  f"                {call}\n                    .is_ok_and(|check| maximum(&check) < norm)")
    return source + """
#[inline(always)]
fn observe(family: &Family, phase: f64, h: f64, bus: [f64; 2]) -> Result<([f64; 2], [Port; 2]), StepError> {
""" + boundary.removeprefix(observe_bus) + """
    Ok((phase, ports))
}

fn residual_trial(
    family: &Family, p: Parameters, old: State, phase: f64, delta: [State; 2],
    controls: Controls, h: f64,
) -> Result<[f64; M], StepError> {
    if !(0. ..1.).contains(&phase) || !(rf_d_circuit::chain_charge::MIN_DT_S..=1e-3).contains(&h) {
        return Err(StepError::InvalidInput);
    }
    let mut chain = [
        graph::residual_parts(p, old, delta[0], controls, h, p.time + h / 3.)?,
        graph::residual_parts(p, old, delta[1], controls, h, p.time + h)?,
    ];
""" + observe_bus + observe + """
    for j in 0..2 {
        chain[j].dc[BUS] += ports[j].currents_a[2];
    }
    Ok(residual(&Stages { chain, phase, ports }))
}
"""


def contiguous_solver(source):
    source = once(source,
        "self.lu.a.swap(col,pivot);self.lu.perm.swap(col,pivot);self.border.swap(col,pivot);scale.swap(col,pivot);",
        """
            if col != pivot {
                self.lu.a.swap(col, pivot);
                self.lu.perm.swap(col, pivot);
                self.border.swap(col, pivot);
                scale.swap(col, pivot);
            }""")
    source = once(source, "for k in col+1..end{current[k]-=factor*row[k];}", """
                for (value, coefficient) in current[col + 1..end].iter_mut().zip(&row[col + 1..end]) {
                    *value -= factor * coefficient;
                }
                """)
    return once(source, "for k in col+1..end{self.cross[p][k]-=factor*row[k];}", """
                for (value, coefficient) in self.cross[p][col + 1..end].iter_mut().zip(&row[col + 1..end]) {
                    *value -= factor * coefficient;
                }
                """)
