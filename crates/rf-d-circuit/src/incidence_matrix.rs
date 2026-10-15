//! Current stage coefficients, sorted by physical row/column; never a scene mask.
use crate::StepError;
pub const N:usize=118;
pub const CAPACITY:usize=4096;
pub struct Row{dc:[f64;N],mass:[f64;N],seen:[bool;N],columns:[usize;N],count:usize}
impl Row{
    pub const fn new()->Self{Self{dc:[0.;N],mass:[0.;N],seen:[false;N],columns:[0;N],count:0}}
    fn touch(&mut self,k:usize){if !self.seen[k]{self.seen[k]=true;self.columns[self.count]=k;self.count+=1;}}
    pub fn set(&mut self,k:usize,g:f64,m:f64)->Result<(),StepError>{
        if k>=N||!g.is_finite()||!m.is_finite(){return Err(StepError::InvalidInput);}
        if g!=0.||m!=0.{self.touch(k);}self.dc[k]=g;self.mass[k]=m;Ok(())
    }
    pub fn add(&mut self,k:usize,g:f64,m:f64)->Result<(),StepError>{
        if k>=N||!g.is_finite()||!m.is_finite(){return Err(StepError::InvalidInput);}
        // Match the original two independent nonzero accumulation guards.
        let dc=if g!=0.{self.dc[k]+g}else{self.dc[k]};let mass=if m!=0.{self.mass[k]+m}else{self.mass[k]};
        if !dc.is_finite()||!mass.is_finite(){return Err(StepError::ExponentialDomain);}
        if g!=0.||m!=0.{self.touch(k);}self.dc[k]=dc;self.mass[k]=mass;Ok(())
    }
}
pub struct Tangent{rows:[usize;N+1],columns:[u16;CAPACITY],dc:[f64;CAPACITY],mass:[f64;CAPACITY],count:usize,next:usize}
impl Tangent{
    pub const fn new()->Self{Self{rows:[0;N+1],columns:[0;CAPACITY],dc:[0.;CAPACITY],mass:[0.;CAPACITY],count:0,next:0}}
    pub fn push_row(&mut self,a:usize,row:&mut Row)->Result<(),StepError>{
        if a!=self.next||a>=N{return Err(StepError::InvalidInput);}
        row.columns[..row.count].sort_unstable();
        let required=row.columns[..row.count].iter().filter(|k|row.dc[**k]!=0.||row.mass[**k]!=0.).count();
        if self.count+required>CAPACITY{return Err(StepError::InvalidInput);}
        self.rows[a]=self.count;
        for &k in &row.columns[..row.count]{let g=row.dc[k];let m=row.mass[k];if g==0.&&m==0.{continue;}
            self.columns[self.count]=k as u16;self.dc[self.count]=g;self.mass[self.count]=m;self.count+=1;
        }self.rows[a+1]=self.count;self.next+=1;Ok(())
    }
    pub fn complete(&self)->bool{self.next==N}
    pub fn entries(&self,a:usize)->impl Iterator<Item=(usize,f64,f64)>+'_ {
        (self.rows[a]..self.rows[a+1]).map(|z|(self.columns[z]as usize,self.dc[z],self.mass[z]))
    }
    /// The VCO port is added after the chain, preserving the original sum order.
    pub fn add(&mut self,a:usize,b:usize,g:f64,m:f64)->Result<(),StepError>{
        if !self.complete()||a>=N||b>=N||!g.is_finite()||!m.is_finite(){return Err(StepError::InvalidInput);}
        let mut z=self.rows[a];while z<self.rows[a+1]&&(self.columns[z]as usize)<b{z+=1;}
        if z<self.rows[a+1]&&self.columns[z]as usize==b{
            let dc=self.dc[z]+g;let mass=self.mass[z]+m;
            if !dc.is_finite()||!mass.is_finite(){return Err(StepError::ExponentialDomain);}
            if dc==0.&&mass==0.{self.columns.copy_within(z+1..self.count,z);self.dc.copy_within(z+1..self.count,z);self.mass.copy_within(z+1..self.count,z);self.count-=1;for row in a+1..=N{self.rows[row]-=1;}return Ok(());}
            self.dc[z]=dc;self.mass[z]=mass;return Ok(());
        }
        if g==0.&&m==0.{return Ok(());}if self.count==CAPACITY{return Err(StepError::InvalidInput);}
        self.columns.copy_within(z..self.count,z+1);self.dc.copy_within(z..self.count,z+1);self.mass.copy_within(z..self.count,z+1);
        self.columns[z]=b as u16;self.dc[z]=g;self.mass[z]=m;self.count+=1;for row in a+1..=N{self.rows[row]+=1;}Ok(())
    }
    #[cfg(laboratory)]pub fn dense(&self)->([[f64;N];N],[[f64;N];N]){
        assert!(self.complete());let mut dc=[[0.;N];N];let mut mass=dc;
        for a in 0..N{for(b,g,m)in self.entries(a){dc[a][b]=g;mass[a][b]=m;}}(dc,mass)
    }
    #[cfg(laboratory)]pub fn from_dense(dc:&[[f64;N];N],mass:&[[f64;N];N])->Result<Self,StepError>{
        let mut t=Self::new();for a in 0..N{let mut row=Row::new();for b in 0..N{row.set(b,dc[a][b],mass[a][b])?;}t.push_row(a,&mut row)?;}Ok(t)
    }
}
