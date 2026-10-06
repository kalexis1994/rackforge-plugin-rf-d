#include <stdio.h>
#include "voice_refine_dd.h"
int main(void) {
    char op;double a,b,c,d;int n,j,ok;RFDD r,x,p,q;
    while(scanf(" %c",&op)==1) {
        ok=1;
        if(op=='P') {if(scanf("%lf%lf",&a,&b)!=2)return 2;ok=rf_product(a,b,&r);}
        else if(op=='S') {if(scanf("%lf%lf%lf%lf",&a,&b,&c,&d)!=4)return 2;x.hi=a;x.lo=b;p.hi=c;p.lo=d;r=rf_add(x,p);ok=rf_good(r);}
        else if(op=='R') {
            if(scanf("%lf%d",&b,&n)!=2 || n<0)return 2;r.hi=b;r.lo=0;
            for(j=0;j<n;j++) {
                if(scanf("%lf%lf%lf",&a,&c,&d)!=3)return 2;x.hi=c;x.lo=d;
                if(!rf_ax(-a,x,&q))ok=0;
                else {r=rf_add(r,q);if(!rf_good(r))ok=0;}
            }
        } else return 2;
        if(ok)printf("1 %.17g %.17g\n",r.hi,r.lo);else printf("0\n");
    }
    return 0;
}
