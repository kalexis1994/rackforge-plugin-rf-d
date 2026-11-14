// RF-D programs use stable control IDs in the RackForge program document.
use std::collections::BTreeMap;

use rackforge_program_api::{
    PreparedProgram, ProgramDocument, ProgramEditRequest, ProgramEditorValue,
    ProgramFieldEditRequest,
};
use serde::Serialize;
use serde_json::{json, Value};

use crate::{control_index, program_data, Controls};

const PLUGIN_ID: &str = "org.rackforge.lab.rf-d-voice";
const PREFIX: &str = "custom.";
const MAX_PROGRAMS: usize = 64;
pub const TRANSFER_BYTES: usize = 32_768;

#[derive(Default)]
pub struct Library(BTreeMap<String, ProgramDocument>);

fn write(value: &impl Serialize, output: &mut [u8]) -> Option<usize> {
    let bytes = serde_json::to_vec(value).ok()?;
    output.get_mut(..bytes.len())?.copy_from_slice(&bytes);
    Some(bytes.len())
}

fn controls(document: &ProgramDocument, mut candidate: Controls) -> Option<Controls> {
    document.validate().ok()?;
    if document.plugin_id != PLUGIN_ID
        || document.payload_version != 1
        || document.plugin_state_version != 1
        || document.name.chars().count() > 64
        || document.id.len() > 64
    {
        return None;
    }
    let payload = document.payload.as_object()?;
    let values = payload.get("parameters")?.as_object()?;
    if payload.len() != 1 || values.len() != program_data::FIELDS.len() {
        return None;
    }
    for &(index, name) in program_data::FIELDS {
        let value = values.get(name)?.as_f64()?;
        candidate.0[control_index(index, value)?] = value;
    }
    Some(candidate)
}

fn envelope(document: ProgramDocument) -> Option<PreparedProgram> {
    controls(&document, Controls::default())?;
    let prepared = PreparedProgram {
        schema_version: 1,
        storage_path: format!("programs/{}.rackforge-program.json", document.id),
        preview_sound_id: format!("{PREFIX}{}", document.id),
        document,
        artifacts: Vec::new(),
    };
    prepared.validate().ok()?;
    Some(prepared)
}

fn prepared(bytes: &[u8]) -> Option<ProgramDocument> {
    let incoming: PreparedProgram = serde_json::from_slice(bytes).ok()?;
    (envelope(incoming.document.clone())? == incoming).then_some(incoming.document)
}

impl Library {
    pub fn begin(
        &self,
        read_parameter: impl Fn(u32) -> Option<f64>,
        request: &[u8],
        output: &mut [u8],
    ) -> Option<usize> {
        let request: ProgramEditRequest = serde_json::from_slice(request).ok()?;
        request.validate().ok()?;
        if let Some(id) = request.program_id.as_deref() {
            let document = self.0.get(id.strip_prefix(PREFIX)?)?;
            return write(&envelope(document.clone())?, output);
        }
        let id = (1..=MAX_PROGRAMS)
            .map(|slot| format!("user-{slot:02}"))
            .find(|id| !self.0.contains_key(id))?;
        let parameters = program_data::FIELDS
            .iter()
            .map(|&(index, id)| read_parameter(index).map(|value| (id, value)))
            .collect::<Option<BTreeMap<_, _>>>()?;
        let document = ProgramDocument {
            schema_version: 1,
            id,
            name: "New program".into(),
            plugin_id: PLUGIN_ID.into(),
            plugin_version: program_data::VERSION.into(),
            plugin_state_version: 1,
            payload_version: 1,
            category: None,
            tags: Vec::new(),
            payload: json!({"parameters": parameters}),
        };
        write(&envelope(document)?, output)
    }

    pub fn prepare(&self, bytes: &[u8], output: &mut [u8]) -> Option<usize> {
        self.prepare_document(serde_json::from_slice(bytes).ok()?, output)
    }

    fn prepare_document(&self, document: ProgramDocument, output: &mut [u8]) -> Option<usize> {
        let prepared = envelope(document)?;
        self.catalog_with(Some(&prepared.document), output)?;
        write(&prepared, output)
    }

    pub fn install(&mut self, bytes: &[u8]) -> bool {
        let Some(document) = prepared(bytes) else {
            return false;
        };
        if self
            .catalog_with(Some(&document), &mut vec![0; TRANSFER_BYTES])
            .is_none()
        {
            return false;
        }
        self.0.insert(document.id.clone(), document);
        true
    }

    pub fn catalog(&self, output: &mut [u8]) -> Option<usize> {
        self.catalog_with(None, output)
    }

    fn catalog_with(
        &self,
        candidate: Option<&ProgramDocument>,
        output: &mut [u8],
    ) -> Option<usize> {
        let mut catalog: Value = serde_json::from_str(program_data::CATALOG).ok()?;
        let rows = catalog.get_mut("presets")?.as_array_mut()?;
        let mut programs: BTreeMap<_, _> = self
            .0
            .values()
            .map(|document| (&document.id, document))
            .collect();
        if let Some(document) = candidate {
            programs.insert(&document.id, document);
        }
        if programs.len() > MAX_PROGRAMS {
            return None;
        }
        for (order, document) in programs.values().enumerate() {
            rows.push(
                json!({"id": format!("{PREFIX}{}", document.id), "name": document.name,
                "bank": "user", "order": 1000 + order, "tags": [], "editable": true}),
            );
        }
        write(&catalog, output)
    }

    pub fn recall(&self, id: &str, current: Controls) -> Option<Controls> {
        let document = self.0.get(id.strip_prefix(PREFIX)?)?;
        controls(document, current)
    }

    pub fn preview(bytes: &[u8], current: Controls) -> Option<Controls> {
        controls(&prepared(bytes)?, current)
    }

    pub fn editor(bytes: &[u8], output: &mut [u8]) -> Option<usize> {
        let document: ProgramDocument = serde_json::from_slice(bytes).ok()?;
        let candidate = controls(&document, Controls::default())?;
        write(
            &json!({
                "schema_version": 1,
                "title": "RF-D Program",
                "pages": [{
                    "id": "program",
                    "label": "Program",
                    "detail": "Edit the synthesis controls in PLAY",
                    "fields": [{
                        "id": "cutoff", "label": "Cutoff", "detail": "Filter cutoff percentage",
                        "kind": {"type": "number", "minimum": 0, "maximum": 10000, "step": 1, "decimals": 2, "unit": "%"},
                        "value": {"type": "integer", "value": (candidate.0[0] * 100.).round() as i64},
                        "live_preview": true
                    }]
                }]
            }),
            output,
        )
    }

    pub fn edit(&self, bytes: &[u8], output: &mut [u8]) -> Option<usize> {
        let mut request: ProgramFieldEditRequest = serde_json::from_slice(bytes).ok()?;
        request.validate().ok()?;
        if request.field_id != "cutoff" {
            return None;
        }
        let ProgramEditorValue::Integer(value) = request.value else {
            return None;
        };
        request
            .document
            .payload
            .get_mut("parameters")?
            .as_object_mut()?
            .insert("cutoff".into(), json!(value as f64 / 100.));
        self.prepare_document(request.document, output)
    }
}
