"""Derive the anticipation experiment from the validated collector clock."""
from prepare_hybrid_stamp import once


def controller(source):
    source = once(source, "pub fn run(path: &str, label: &str, cap: usize)", """fn approaching(anchor: [f64; 4], present: [f64; 4]) -> bool {
    [0, 2].into_iter().any(|i| {
        let initial = (anchor[i] - anchor[i + 1]).abs();
        let gap = (present[i] - present[i + 1]).abs();
        gap < 0.75 * 9.3 && initial - gap > VT / 16.
    })
}

pub fn run(path: &str, label: &str, cap: usize, intermediate_cap: usize, mut phase: f64)""")
    source = once(source, "!matches!(cap, 32 | 64 | 128 | 256)",
                  "!matches!(cap, 8 | 16 | 32) || !matches!(intermediate_cap, 64 | 128) || !(0. ..1.).contains(&phase)")
    source = once(source, '    let mut phase = if label == "negative" { 0.37 } else { 0. };',
                  "    let anchor = collectors(&state);\n    let intermediate_width = TICKS / intermediate_cap;")
    source = once(source, "    let mut proposal = ceiling;",
                  "    let mut proposal = ceiling;\n    let (mut approach_retries, mut approach_ticks) = (0, 0);")
    source = once(source, "            let mut width = proposal;",
                  """            let prior_approach = approaching(anchor, before);
            let mut width = if prior_approach { proposal.min(intermediate_width) } else { proposal };""")
    source = once(source, "            let (q, motion, end) = loop {", "            let (q, motion, end, limited) = loop {")
    source = once(source, "                        if width > FINE", """                        let limited = prior_approach || approaching(anchor, intermediate) || approaching(anchor, end);
                        if limited && width > intermediate_width {
                            approach_retries += 1;
                            width /= 2;
                            continue;
                        }
                        if width > FINE""")
    source = once(source, "                        break (q, motion, end);", "                        break (q, motion, end, limited);")
    source = once(source, "            within += width;",
                  "            within += width;\n            if limited { approach_ticks += width; }")
    return once(source, '    print!("CLOCK,{guard_retries},{newton_retries},{audits}");',
                '    println!("APPROACH,{intermediate_cap},{approach_retries},{approach_ticks}");\n'
                '    print!("CLOCK,{guard_retries},{newton_retries},{audits}");')


def fixed_phase(source):
    source = once(source, "fn branch(path: &str, which: &str, subdivisions: usize)",
                  "fn branch(path: &str, which: &str, subdivisions: usize, initial_phase: Option<f64>)")
    source = once(source, 'let mut phase = if which == "positive" { 0. } else { 0.37 };',
                  'let mut phase = initial_phase.unwrap_or(if which == "positive" { 0. } else { 0.37 });')
    return once(source, '        Some("branch") if args.len() == 5 => branch(&args[2], &args[3], args[4].parse()?),',
                '''        Some("branch") if args.len() == 5 => branch(&args[2], &args[3], args[4].parse()?, None),
        Some("branch-phase") if args.len() == 6 => branch(&args[2], &args[3], args[4].parse()?, Some(args[5].parse()?)),''')


def hold_after_switch(source):
    source = once(source, "    let (mut approach_retries, mut approach_ticks) = (0, 0);",
                  """    let (mut approach_retries, mut approach_ticks) = (0, 0);
    let mut hold_until = 0;
    let mut hold_ticks = 0;
    let mut held_steps = 0;""")
    source = once(source, "            let prior_approach = approaching(anchor, before);",
                  """            let held = tick < hold_until;
            let prior_approach = held || approaching(anchor, before);""")
    source = once(source, "            if crossing {\n                for pair", """            if crossing {
                hold_until = ((tick + width) / TICKS + 1) * TICKS;
                for pair""")
    source = once(source, "            if limited { approach_ticks += width; }",
                  """            if limited { approach_ticks += width; }
            if held {
                held_steps += 1;
                hold_ticks += width;
            }""")
    return once(source, '    println!("APPROACH,{intermediate_cap},{approach_retries},{approach_ticks}");',
                '    println!("APPROACH,{intermediate_cap},{approach_retries},{approach_ticks}");\n'
                '    println!("HOLD,{held_steps},{hold_ticks}");')
