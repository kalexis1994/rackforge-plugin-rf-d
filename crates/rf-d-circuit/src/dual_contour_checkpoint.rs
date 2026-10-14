//! Exact laboratory restart state; caller owns subsequent source events.
use crate::dual_contour::{Controls, State, N};
use crate::StepError;
pub const SIZE: usize = 40 + 16 * N;
pub const TICKS_PER_US: u64 = 1073741824;
#[derive(Clone, Copy)]
pub struct Checkpoint {
    pub state: State,
    pub controls: Controls,
    pub ticks: u64,
    pub proposal: u64,
}
impl Checkpoint {
    pub fn encode(self) -> [u8; SIZE] {
        let mut b = [0; SIZE];
        b[..8].copy_from_slice(b"RFDC5011");
        b[8..16].copy_from_slice(&self.ticks.to_le_bytes());
        b[16..24].copy_from_slice(&self.proposal.to_le_bytes());
        let flags = (self.controls.optional as u32) | ((self.controls.short as u32) << 1);
        b[24..28].copy_from_slice(&flags.to_le_bytes());
        b[32..40].copy_from_slice(&self.controls.key.to_le_bytes());
        for (k, v) in self
            .state
            .high
            .into_iter()
            .chain(self.state.low)
            .enumerate()
        {
            b[40 + 8 * k..48 + 8 * k].copy_from_slice(&v.to_le_bytes());
        }
        b
    }
    pub fn decode(b: &[u8], expected_optional: bool) -> Result<Self, StepError> {
        if b.len() != SIZE || &b[..8] != b"RFDC5011" || b[28..32] != [0; 4] {
            return Err(StepError::InvalidInput);
        }
        let ticks = u64::from_le_bytes(b[8..16].try_into().unwrap());
        let proposal = u64::from_le_bytes(b[16..24].try_into().unwrap());
        let flags = u32::from_le_bytes(b[24..28].try_into().unwrap());
        let key = f64::from_le_bytes(b[32..40].try_into().unwrap());
        if flags > 3
            || (flags & 1 != 0) != expected_optional
            || ticks > 36000 * TICKS_PER_US
            || ticks % 2 != 0
            || proposal < 2
            || !proposal.is_power_of_two()
            || proposal > 8 * TICKS_PER_US
            || !key.is_finite()
            || !(0. ..=10.).contains(&key)
        {
            return Err(StepError::InvalidInput);
        }
        let values = std::array::from_fn::<_, { 2 * N }, _>(|k| {
            f64::from_le_bytes(b[40 + 8 * k..48 + 8 * k].try_into().unwrap())
        });
        let state = State {
            high: std::array::from_fn(|k| values[k]),
            low: std::array::from_fn(|k| values[k + N]),
            optional: expected_optional,
        };
        if !state.valid() {
            return Err(StepError::InvalidInput);
        }
        Ok(Self {
            state,
            controls: Controls {
                key,
                short: flags & 2 != 0,
                optional: expected_optional,
            },
            ticks,
            proposal,
        })
    }
}
