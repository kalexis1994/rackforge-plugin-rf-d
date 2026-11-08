"""Derive exact two-stage scattering with a shared sparse buffer."""
from prepare_hybrid_stamp import once


def fused(source):
    source = once(source, "struct Sparse{row:[usize;M+1],column:", "struct Sparse{row:[[usize;N+1];2],count:usize,column:")
    source = once(source, "Self{row:[0;M+1],column:", "Self{row:[[0;N+1];2],count:0,column:")
    source = once(source, "    fn residual(&self,b:", """    fn slots(&self, row: usize) -> impl Iterator<Item = usize> {
        let stage = row / N;
        let local = row % N;
        let [start, end] = [self.row[stage][local], self.row[stage][local + 1]];
        let (first, stride) = if stage == 0 { (start, 1) } else { (start.wrapping_sub(1), usize::MAX) };
        (0..start.abs_diff(end)).map(move |offset| first.wrapping_add(stride.wrapping_mul(offset)))
    }
    fn residual(&self,b:""")
    assert source.count("self.row[i]..self.row[i+1]") == 1
    source = source.replace("self.row[i]..self.row[i+1]", "self.slots(i)")
    source = once(source, "self.sparse.row[i]..self.sparse.row[i+1]", "self.sparse.slots(i)")
    source = once(source, "self.sparse.row[M]);", "self.sparse.count);")
    start = source.index("        self.outer.a=[[0.;4];4];let mut count=0;")
    end = source.index("        self.contour.factor", start)
    return once(source, source[start:end], """        self.outer.a = [[0.; 4]; 4];
        let mut cursor = [0, CAPACITY];
        for a in 0..N {
            for i in 0..2 {
                self.sparse.row[i][a] = cursor[i];
                self.sparse.floor[i * N + a] = 0.;
            }
            for j in 0..2 {
                for (b, dc, mass) in stages[j].tangent.entries(a) {
                    let col = j * N + b;
                    if dc != 0. || mass != 0. {
                        self.scatter(j, a, col, weights[j][j] * mass + dc, &mut cursor)?;
                    }
                    if mass != 0. {
                        let i = 1 - j;
                        self.scatter(i, a, col, weights[i][j] * mass + 0., &mut cursor)?;
                    }
                }
            }
        }
        for i in 0..2 {
            self.sparse.row[i][N] = cursor[i];
        }
        self.sparse.count = cursor[0] + CAPACITY - cursor[1];
""").replace(
        "    // Read the actual retained coefficients",
        """    #[inline(always)]
    fn scatter(
        &mut self, stage: usize, a: usize, col: usize, value: f64, cursor: &mut [usize; 2],
    ) -> Result<(), StepError> {
        if !value.is_finite() {
            return Err(StepError::InvalidInput);
        }
        if value == 0. {
            return Ok(());
        }
        let row = stage * N + a;
        let ri = LOCAL[row];
        let ci = LOCAL[col];
        match (OWNER[row], OWNER[col]) {
            (1, 1) => {
                self.contour.lu.a[ri][ci] = value;
                self.contour.scale[ri] = self.contour.scale[ri].max(value.abs());
            }
            (2, 2) => {
                self.audio.lu.a[ri][ci] = value;
                self.audio.scale[ri] = self.audio.scale[ri].max(value.abs());
            }
            (0, 0) => self.outer.a[ri][ci] = value,
            (1, 0) => self.contour.border[ri][ci] = value,
            (2, 0) => self.audio.border[ri][ci] = value,
            (0, 1) => self.contour.cross[ri][ci] = value,
            (0, 2) => self.audio.cross[ri][ci] = value,
            _ => return Err(StepError::InvalidInput),
        }
        if cursor[0] == cursor[1] {
            return Err(StepError::InvalidInput);
        }
        let slot = if stage == 0 {
            let next = cursor[0];
            cursor[0] += 1;
            next
        } else {
            cursor[1] -= 1;
            cursor[1]
        };
        self.sparse.column[slot] = col as u16;
        self.sparse.value[slot] = value;
        self.sparse.floor[row] += value.abs() * 2e-9;
        Ok(())
    }
    // Read the actual retained coefficients""", 1)


def profile_solver(source):
    source = once(source, "        if weights.iter().flatten()",
                  "        let assembly = std::time::Instant::now();\n        if weights.iter().flatten()")
    return once(source, "        self.contour.factor(&mut self.outer.a)?;self.audio.factor(&mut self.outer.a)?;self.outer.factor()",
                """        crate::cost::record(3, assembly);
        crate::cost::measure(4, || {
            self.contour.factor(&mut self.outer.a)?;
            self.audio.factor(&mut self.outer.a)?;
            self.outer.factor()
        })""")


def profile_cost(source):
    assert source.count("AtomicU64; 3") == source.count("AtomicU64::new(0) }; 3") == 2
    source = source.replace("AtomicU64; 3", "AtomicU64; 5").replace("AtomicU64::new(0) }; 3", "AtomicU64::new(0) }; 5")
    return once(source, "    pub fn measure<T>", """    pub fn record(slot: usize, start: Instant) {
        TIME[slot].fetch_add(start.elapsed().as_nanos() as u64, Relaxed);
        CALLS[slot].fetch_add(1, Relaxed);
    }

    pub fn measure<T>""").replace("pub use instrumentation::measure;", "pub use instrumentation::{measure, record};")


def bit_rows(source):
    start = source.index("pub struct Row{")
    end = source.index("pub struct Tangent", start)
    row = source[start:end].replace("Row", "BitRow")
    row = once(row, "seen:[bool;N],columns:[usize;N],count:usize", "seen:u128")
    row = once(row, "seen:[false;N],columns:[0;N],count:0", "seen:0")
    row = once(row, "if !self.seen[k]{self.seen[k]=true;self.columns[self.count]=k;self.count+=1;}",
               "self.seen |= 1u128 << k;")
    source = once(source, "pub struct Tangent", row + "\npub struct Tangent")
    return once(source, "    pub fn complete(&self)", """    pub fn push_bits(&mut self, a: usize, row: &BitRow) -> Result<(), StepError> {
        if a != self.next || a >= N {
            return Err(StepError::InvalidInput);
        }
        if self.count + row.seen.count_ones() as usize > CAPACITY {
            let mut required = 0;
            let mut pending = row.seen;
            while pending != 0 {
                let k = pending.trailing_zeros() as usize;
                pending &= pending - 1;
                required += usize::from(row.dc[k] != 0. || row.mass[k] != 0.);
            }
            if self.count + required > CAPACITY {
                return Err(StepError::InvalidInput);
            }
        }
        self.rows[a] = self.count;
        let mut pending = row.seen;
        while pending != 0 {
            let k = pending.trailing_zeros() as usize;
            pending &= pending - 1;
            let (dc, mass) = (row.dc[k], row.mass[k]);
            if dc == 0. && mass == 0. {
                continue;
            }
            self.columns[self.count] = k as u16;
            self.dc[self.count] = dc;
            self.mass[self.count] = mass;
            self.count += 1;
        }
        self.rows[a + 1] = self.count;
        self.next += 1;
        Ok(())
    }

    pub fn complete(&self)""")


def bit_graph(source):
    source = once(source, "use super::incidence::{Row,Tangent};", "use super::incidence::{BitRow,Tangent};")
    source = once(source, "let mut row=Row::new();", "let mut row=BitRow::new();")
    return once(source, "tangent.push_row(a,&mut row)?;", "tangent.push_bits(a,&row)?;")
