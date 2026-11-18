"""Equilíbrio estático em pequeno ângulo e dinâmica linear opcional.

I φ''+c φ'+(Δ g GMef)φ = (g M_massa), em radianos; g padrão 9.80665 m/s².
O modelo de dinâmica é fenomenológico e exige I efetivo e amortecimento medidos/fornecidos.
"""
from math import atan, degrees, radians, tan
import numpy as np
from scipy.integrate import solve_ivp
from .validacao import numero

G0=9.80665


def equilibrio_angulo(momento_kgm, deslocamento_kg, gm_efetivo_m):
    numero(deslocamento_kg,"deslocamento",positivo=True)
    numero(gm_efetivo_m,"GM",positivo=True)
    return degrees(atan(momento_kgm/(deslocamento_kg*gm_efetivo_m)))


def avancar_dinamica(estado, momento_kgm, deslocamento_kg, gm_efetivo_m, inercia_kgm2,
                      amortecimento_Nms, dt_s):
    """Integração dinâmica com equilíbrio linear φeq=M/(Δ GM), não atan.
    Não usar fora do regime angular linear; tolerâncias externas definem estabilização.
    """
    m=numero(deslocamento_kg,"deslocamento",positivo=True)
    gm=numero(gm_efetivo_m,"GM",positivo=True)
    I=numero(inercia_kgm2,"inércia efetiva",positivo=True)
    c=numero(amortecimento_Nms,"amortecimento",nao_negativo=True)
    dt=numero(dt_s,"passo",positivo=True)
    y0=[float(estado.get("phi_rad",0)),float(estado.get("omega_rad_s",0))]
    def fun(_t,y):
        return [y[1],(G0*momento_kgm - c*y[1] - m*G0*gm*y[0])/I]
    sol=solve_ivp(fun,(0,dt),y0,rtol=1e-9,atol=1e-11)
    if not sol.success: raise RuntimeError(sol.message)
    return {"phi_rad":float(sol.y[0,-1]),"omega_rad_s":float(sol.y[1,-1]),"tempo_s":float(estado.get("tempo_s",0)+dt)}


def estabilizado(estado, momento_kgm, delta_kg, gm_m, tol_angulo_graus, tol_vel_graus_s):
    for k,v in (("tolerância angular",tol_angulo_graus),("tolerância velocidade",tol_vel_graus_s)):
        numero(v,k,positivo=True)
    # Apenas modelo LINEAR no caso dinâmico.
    phi_eq=momento_kgm/(delta_kg*gm_m)
    return abs(degrees(estado["phi_rad"]-phi_eq)) <= tol_angulo_graus and abs(degrees(estado["omega_rad_s"])) <= tol_vel_graus_s


def leitura_teorica(momento_kgm, deslocamento_kg, gm_efetivo_m, pendulos):
    theta=equilibrio_angulo(momento_kgm, deslocamento_kg, gm_efetivo_m)
    return {"angulo_graus":theta,"tangente":tan(radians(theta)),
            "deflexoes":{p["id"]:p["comprimento_m"]*tan(radians(theta)) for p in pendulos}}
