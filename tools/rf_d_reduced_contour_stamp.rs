pub fn export_split(p: Parameters, x: State, c: Controls, out: &mut impl std::io::Write)
    -> Result<(), Box<dyn std::error::Error>>
{
    fn write(out: &mut impl std::io::Write, values: impl IntoIterator<Item = f64>)
        -> std::io::Result<()>
    {
        for value in values {
            out.write_all(&value.to_le_bytes())?;
        }
        Ok(())
    }
    let h = 1e-6;
    let delta = State::new([0.; N], x.optional);
    let audio = chain_charge::linearize_prevalidated::<true>(p.chain, sources(0.), x.chain(), delta.chain(), h, x.chain())
        .map_err(|error| format!("{error:?}"))?;
    let dual = contour::parts::<true>(x.contour(), delta.contour(), c, h, x.contour())
        .map_err(|error| format!("{error:?}"))?;
    write(out, dual.dc)?;
    write(out, dual.j.into_iter().flatten())?;
    write(out, dual.mass.into_iter().flatten().map(|value| value * h))?;
    write(out, audio.dc)?;
    write(out, audio.dc_jacobian.into_iter().flatten())?;
    write(out, audio.mass_over_h.into_iter().flatten().map(|value| value * h))?;
    Ok(())
}

pub fn export_contour_stage(x: State, delta: State, key: f64, h: f64, out: &mut impl std::io::Write)
    -> Result<(), Box<dyn std::error::Error>>
{
    let now = x.advanced(delta.high);
    let c = Controls { key, short: false, optional: false };
    let dual = contour::parts::<true>(x.contour(), delta.contour(), c, h, now.contour())
        .map_err(|error| format!("{error:?}"))?;
    for value in dual.dc.into_iter().chain(dual.dq).chain(dual.j.into_iter().flatten())
        .chain(dual.mass.into_iter().flatten())
    {
        out.write_all(&value.to_le_bytes())?;
    }
    Ok(())
}
