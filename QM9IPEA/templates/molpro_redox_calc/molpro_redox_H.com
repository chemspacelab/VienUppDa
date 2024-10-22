memory,$${MEMORY},M
file,1,$${INT_NAME}
file,2,$${WFU_NAME}
gthresh,throvl=0.5e-09,throrth=1e-07,energy=1e-08
local,domopt=tight

basis={
default,avtz-f12                                                                                !default orbital basis set
Li=vtz-f12
Be=vtz-f12
Ca=aug-cc-pVTZ
Zn=aug-cc-pVTZ-PP
Br=VTZ-PP-F12
set,df                                                                                          !density fitting basis
default,avtz/mp2fit
Li=Def2-TZVPP/mp2fit
Be=Def2-TZVPP/mp2fit
Ca=Def2-TZVPP/mp2fit
Zn=aug-cc-pVTZ-PP/mp2fit
Br=aug-cc-pVTZ-PP/mp2fit
set,jk                                                                                          !density fitting basis for Fock and exchange matrices
default,avtz/jkfit
Li=Def2-TZVPP/jkfit
Be=Def2-TZVPP/jkfit
Ca=Def2-TZVPP/jkfit
Zn=aug-cc-pVTZ-PP/jkfit
Br=aug-cc-pVTZ-PP/jkfit
set,ri                                                                                          !ri cabs basis
default,vtz-f12+/optri
Li=Def2-TZVPP/jkfit
Be=Def2-TZVPP/jkfit
Ca=Def2-TZVPP/jkfit
Zn=aug-cc-pVTZ-PP/optri
Br=VTZ-PP-F12/OPTRI
set,ripno                                                                                       !ri cabs basis for PNO
default,vtz-f12/cabs
Be=Def2-TZVPP/jkfit
Li=Def2-TZVPP/jkfit
Ca=Def2-TZVPP/jkfit
Zn=aug-cc-pVTZ-PP/jkfit
Br=aug-cc-pVTZ-PP/jkfit
}

symmetry,nosym
orient,noorient
geometry={
$${GEOM_LINES}}

wf,charge=$${CHARGE},spin=$${SPIN}
runit                                                                                           !call procedure
etot=e                                                                                          !save energies


ca=2100.2                                                                                       !Save wavefunction

table,method,etot
title, Total energies from different methods
digits,,10

procedure runit
nogprint,variable
$method=[df$${HF_TYPE}]
{df-$${HF_TYPE},df_basis=jk,accu=15,maxit=200,use_disk;save,$ca}
e(1)=energy                                                                                     !df$${HF_TYPE} energy
gprint,variable
endproc
