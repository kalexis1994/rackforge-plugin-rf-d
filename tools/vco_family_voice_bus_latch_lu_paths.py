"""Reuse endpoint validation and collect pivot activity from the current column."""
from prepare_hybrid_stamp import once


def depletion(source):
    return once(source, "        self.charge(from)?; self.charge(to)?;\n",
                """        self.charge(from)?; self.charge(to)?;
        self.increment_validated(from, to)
    }

    // The latch has already evaluated and validated both endpoint charges.
    pub(super) fn increment_validated(self, from: f64, to: f64) -> Result<f64, Error> {
""")


def latch(source, law):
    source = once(source, "use crate::{junction_charge::Parameters as Depletion,StepError};",
                  f'#[path = "{law}"] mod charge;\nuse charge::Parameters as Depletion;\nuse crate::StepError;')
    source = once(source, " let ca=law.charge(a)", " let old_exp=(a/VT).exp();\n let ca=law.charge(a)")
    assert source.count("t*1e-14*(a/VT).exp()") == 2
    source = source.replace("t*1e-14*(a/VT).exp()", "t*1e-14*old_exp")
    return once(source, "law.charge_increment(a,b)", "law.increment_validated(a,b)")


def active_rows(source):
    target = ("        for col in 0..N{\n"
              "            let mut pivot=col;let mut best=0.;for row in col..N{let value=self.lu.a[row][col];"
              "if value==0.{continue;}let q=value.abs()/scale[row];if q>best{best=q;pivot=row;}}")
    source = once(source, target, """        let mut active = [0; N];
        for col in 0..N {
            let mut count = 0;
            let mut pivot = col;
            let mut best = 0.;
            for row in col..N {
                let value = self.lu.a[row][col];
                if value == 0. {
                    continue;
                }
                active[count] = row;
                count += 1;
                let q = value.abs() / scale[row];
                if q > best {
                    best = q;
                    pivot = row;
                }
            }""")
    return once(source, """            for (offset,current) in tail.iter_mut().enumerate(){if current[col]==0.{continue;}let factor=current[col]/diagonal;current[col]=factor;""",
                """            for &before in &active[..count] {
                if before == pivot {
                    continue;
                }
                // Elimination only writes the selected row and its border.
                let row_after_swap = if before == col { pivot } else { before };
                let offset = row_after_swap - col - 1;
                let current = &mut tail[offset];
                let factor = current[col] / diagonal;
                current[col] = factor;""")


def profile_windows(source):
    source = once(source, '    let (first, last, count) = if label == "negative" { (15, 20, 64) } else { (76, 81, 512) };', """
    let (first, last, count) = match label {
        "negative" => (15, 20, 64),
        "before" => (52, 57, 512),
        "positive" => (76, 81, 512),
        "after" => (96, 101, 512),
        _ => return Err("unknown profile window".into()),
    };
    let history = if label == "negative" { "negative" } else { "positive" };""")
    return once(source, "        let c = controls(label, frame);\n        for sub in 0..count {",
                "        let c = controls(history, frame);\n        for sub in 0..count {")
