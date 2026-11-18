"""Unidades SI e verificações de integridade, sem limites de aceitação inventados."""
from math import isfinite


def numero(valor, nome, positivo=False, nao_negativo=False):
    if valor is None or isinstance(valor, bool):
        raise ValueError(f"{nome}: valor numérico obrigatório")
    try:
        v = float(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{nome}: número inválido") from exc
    if not isfinite(v):
        raise ValueError(f"{nome}: precisa ser finito")
    if positivo and v <= 0:
        raise ValueError(f"{nome}: precisa ser maior que zero")
    if nao_negativo and v < 0:
        raise ValueError(f"{nome}: não pode ser negativo")
    return v


def opcional(valor):
    if valor is None or str(valor).strip() == "":
        return None
    return numero(valor, "Campo")


def verificar_carga(carga, barco=None):
    for field in ("id", "nome", "categoria"):
        if not str(carga.get(field, "")).strip():
            raise ValueError(f"Carga sem '{field}'")
    numero(carga.get("massa_kg"), "Massa da carga", positivo=True)
    for axis in ("x_m", "y_m", "z_m"):
        numero(carga.get(axis), axis)
    for dim in ("comp_m", "larg_m", "alt_m"):
        if carga.get(dim) is not None:
            numero(carga[dim], dim, positivo=True)
    if barco:
        L, B, D = (barco.get(k) for k in ("L_m", "B_m", "D_m"))
        x, y, z = (carga[k] for k in ("x_m", "y_m", "z_m"))
        if L is not None and not 0 <= x <= L:
            raise ValueError(f"{carga['nome']}: X fora do comprimento informado")
        if B is not None and abs(y) > B / 2:
            raise ValueError(f"{carga['nome']}: Y fora da boca informada")
        # Pontal NÃO é limite superior da posição do CG: cargas podem ficar no convés/casaria.
        if barco.get("z_min_m") is not None and z < barco["z_min_m"]:
            raise ValueError(f"{carga['nome']}: Z abaixo do limite operacional informado")
        if barco.get("z_max_m") is not None and z > barco["z_max_m"]:
            raise ValueError(f"{carga['nome']}: Z acima do limite operacional informado")
        if B is not None and carga.get("larg_m") is not None and abs(y) + carga["larg_m"]/2 > B/2:
            raise ValueError(f"{carga['nome']}: volume da carga excede a boca nominal")
    return True


def verificar_hidro(tabela):
    required = ("deslocamento_kg", "calado_m", "km_m")
    if not tabela:
        return
    vals = []
    for i, row in enumerate(tabela):
        for col in required:
            numero(row.get(col), f"Hidrostática linha {i+1}/{col}", positivo=True)
        vals.append(row["deslocamento_kg"])
        for col in ("kb_m", "lcb_m", "lcf_m", "mtc_kgm_por_m"):
            if row.get(col) is not None:
                numero(row[col], col, positivo=(col == "mtc_kgm_por_m"))
    if any(b <= a for a,b in zip(vals, vals[1:])):
        raise ValueError("A tabela hidrostática deve ter deslocamentos estritamente crescentes, sem repetição")
