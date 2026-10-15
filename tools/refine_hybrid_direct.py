"""Avoid dividing zero pivot candidates; positive candidates retain their order."""
from prepare_hybrid_stamp import once
def transform(s):
    for matrix in ['self.a','self.lu.a']:
        s=once(s,f'let q={matrix}[row][col].abs()/scale[row];',f'let value={matrix}[row][col];if value==0.{{continue;}}let q=value.abs()/scale[row];')
    return s

def prepared_scales(s):
    s=once(s,'struct Block<const N:usize>{lu:Lu<N>,','struct Block<const N:usize>{scale:[f64;N],lu:Lu<N>,')
    s=once(s,'Self{lu:Lu::new(),','Self{scale:[0.;N],lu:Lu::new(),')
    s=once(s,'self.lu.perm=std::array::from_fn(|i|i);let mut scale=[0_f64;N];\n        for i in 0..N{scale[i]=self.lu.a[i].iter().fold(0_f64,|s,x|s.max(x.abs()));if scale[i]==0.{return Err(StepError::SingularJacobian);}}',
        'self.lu.perm=std::array::from_fn(|i|i);let mut scale=self.scale;\n        if scale.iter().any(|v|*v==0.){return Err(StepError::SingularJacobian);}')
    s=once(s,'        self.contour.lu.a=[[0.;108];108];', '        if weights.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}\n        self.contour.scale=[0.;108];self.audio.scale=[0.;124];\n        self.contour.lu.a=[[0.;108];108];')
    s=once(s,'                    let value=weight*mass[b]+if i==jj{dc[b]}else{0.};', '''                    // With finite weights, two zero terms give an exact zero.
                    // Inspect the actual inputs; no scene-derived support mask.
                    if mass[b]==0.&&(i!=jj||dc[b]==0.){continue;}
                    let value=weight*mass[b]+if i==jj{dc[b]}else{0.};''')
    s=once(s,'(1,1)=>self.contour.lu.a[ri][ci]=value,','(1,1)=>{self.contour.lu.a[ri][ci]=value;self.contour.scale[ri]=self.contour.scale[ri].max(value.abs());},')
    s=once(s,'(2,2)=>self.audio.lu.a[ri][ci]=value,','(2,2)=>{self.audio.lu.a[ri][ci]=value;self.audio.scale[ri]=self.audio.scale[ri].max(value.abs());},')
    return s
