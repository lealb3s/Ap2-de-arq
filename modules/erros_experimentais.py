"""Erros experimentais explicitamente configurados; não estima vento a partir de uma fórmula empírica."""
import numpy as np
from .validacao import numero


def perturbar(momento_real_kgm, pêndulos, angulo_real_graus, configuracao, rng):
    """Massa/distância medidos são enviesados; vento aplicado como momento fornecido.

    Parâmetros: vies_massa_pct, vies_dist_pct, vies_referencia_m,
    desvio_leitura_m, momento_vento_Nm, g_ms2. Resultados rastreáveis.
    """
    from math import tan, radians
    cfg = configuracao or {}
    mg = (1 + float(cfg.get("vies_massa_pct",0))/100)
    dg = (1 + float(cfg.get("vies_dist_pct",0))/100)
    estimado = momento_real_kgm * mg * dg
    lidos=[]
    for p in pêndulos:
        L=numero(p["comprimento_m"],"comprimento",positivo=True)
        ideal=L*tan(radians(angulo_real_graus))
        ruido=rng.normal(0, float(cfg.get("desvio_leitura_m",0)))
        lidos.append({"id":p["id"],"comprimento_m":L,"deflexao_m":ideal+float(cfg.get("vies_referencia_m",0))+ruido})
    return estimado,lidos


def diagnosticar(condicoes, leituras, angulo_limite=None):
    avisos=[]
    if len(leituras)<8: avisos.append(("Incompleto", "Menos de 8 condições registradas", "Completar sequência e verificar retornos a zero", "REPETIR/CONTINUAR"))
    if not any(l.get("momento_kgm",0)>0 for l in leituras) or not any(l.get("momento_kgm",0)<0 for l in leituras):
        avisos.append(("Distribuição unilateral", "Faltam momentos positivos ou negativos", "Registrar movimentos simétricos para identificar vieses", "REPETIR"))
    minimo=condicoes.get("minimo_angulo_graus")
    if minimo is not None and leituras:
        port=[abs(r.get("angulo_graus",0)) for r in leituras if r.get("momento_kgm",0)<0]
        bore=[abs(r.get("angulo_graus",0)) for r in leituras if r.get("momento_kgm",0)>0]
        if (port and max(port)<minimo) or (bore and max(bore)<minimo):
            avisos.append(("Peso possivelmente insuficiente", "Máxima inclinação inferior ao mínimo declarado por um bordo", "Rever momento, escala, condições de mar e procedimento", "REPLANEJAR/REPETIR"))
    min_def=condicoes.get("minima_deflexao_m")
    if min_def is not None:
        por_pendulo={}
        for leitura in leituras:
            for p in leitura.get("pendulos",[]):
                por_pendulo.setdefault(p["id"],[]).append(abs(p["deflexao_m"]))
        for nome, valores in por_pendulo.items():
            if max(valores)<min_def:
                avisos.append(("Deflexão insuficiente", f"{nome}: máxima leitura menor que mínimo fornecido", "Ajustar comprimento ou momento respeitando limites", "REPLANEJAR"))
    if angulo_limite is None: avisos.append(("Critério ausente", "Limite angular não foi declarado", "Indicar limite aplicável ao projeto", "NÃO AVALIADO"))
    elif any(abs(l.get("angulo_graus",0))>angulo_limite for l in leituras):
        avisos.append(("Ângulo excedido", "Medições além do limite fornecido", "Suspender sequência e reduzir momentos", "SUSPENDER"))
    if len(leituras)>1:
        vals=[l.get("desacordo_pendulos_graus") for l in leituras if l.get("desacordo_pendulos_graus") is not None]
        if vals and condicoes.get("tolerancia_pendulos_graus") is not None and any(x>condicoes["tolerancia_pendulos_graus"] for x in vals):
            avisos.append(("Pêndulos divergentes", "Desacordo acima de tolerância definida", "Rever leitura, referência e comprimentos", "REPETIR"))
    return avisos
