"""I/O dos formatos CSV, XLSX e JSON. Importação validada; sem valores inventados."""
import io
import json
import pandas as pd
import numpy as np

BARCO_CAMPOS={"nome", "massa_base_kg","base_x_m","base_y_m","base_z_m",
              "L_m","B_m","D_m","deslocamento_referencia_kg","calado_m","km_m",
              "kb_m","lcb_m","lcf_m","mtc_kgm_por_m","fsm_kgm", "gz_deslocamento_kg", "gz_kg_referencia_m", "z_min_m", "z_max_m"}
COLUNAS_CARGAS=["id","nome","categoria","massa_kg","x_m","y_m","z_m","comp_m","larg_m","alt_m"]
COLUNAS_HIDRO=["deslocamento_kg","calado_m","km_m","kb_m","lcb_m","lcf_m","mtc_kgm_por_m"]
COLUNAS_GZ=["angulo_graus","gz_m"]
COLUNAS_CASCO=["x_m","y_m"]


def registro_vazio():
    b={k:None for k in BARCO_CAMPOS}
    b["nome"]="Embarcação sem identificação"
    b["hidro_tabela"]=[]
    b["gz_curva"]=[]
    b["casco_contorno"]=[]
    return b


def normalizar(obj):
    if isinstance(obj, dict): return {str(k):normalizar(v) for k,v in obj.items()}
    if isinstance(obj, (list,tuple)):return [normalizar(v) for v in obj]
    if isinstance(obj,np.generic):return normalizar(obj.item())
    if isinstance(obj,float) and not np.isfinite(obj):return None
    return obj


def ler(arquivo, tipo):
    """CSV/XLSX de tabelas; JSON: objeto completo ou lista homogênea para campo dado."""
    nome=arquivo.name.lower()
    dados=arquivo.getvalue()
    if nome.endswith(".json"):
        parsed=json.loads(dados.decode("utf-8-sig"))
        if tipo=="barco" and isinstance(parsed,dict):
            return parsed.get("barco",parsed) if isinstance(parsed.get("barco",parsed),dict) else parsed
        if isinstance(parsed,dict):
            chave={"cargas":"cargas", "hidro":"hidro_tabela", "gz":"gz_curva", "casco":"casco_contorno", "leituras":"leituras"}.get(tipo)
            # Pacotes do relatório trazem tabelas hidrostáticas/GZ dentro de 'barco'.
            if tipo in ("hidro","gz","casco") and isinstance(parsed.get("barco"),dict):
                parsed=parsed["barco"].get(chave,[])
            else:parsed=parsed.get(chave,parsed)
        if not isinstance(parsed,list): raise ValueError("Esperada lista de registros no JSON para esta importação")
        return parsed
    tabela=pd.read_csv(io.BytesIO(dados),sep=None,engine="python",encoding="utf-8-sig") if nome.endswith(".csv") else pd.read_excel(io.BytesIO(dados)) if nome.endswith(".xlsx") else None
    if tabela is None: raise ValueError("Formatos aceitos: .csv, .xlsx, .json")
    tabela=tabela.replace({np.nan:None})
    records=tabela.to_dict("records")
    if tipo=="barco":
        if {"campo","valor"}.issubset(tabela.columns):
            raw=dict(zip(tabela["campo"],tabela["valor"]))
        elif len(records)==1: raw=records[0]
        else: raise ValueError("CSV/XLSX de barco: colunas 'campo,valor' ou uma linha com parâmetros")
        return {k:raw[k] for k in raw if k in BARCO_CAMPOS}
    return normalizar(records)


def preparar_barco(obj, atual=None):
    base=registro_vazio() if atual is None else {**atual}
    for k,v in obj.items():
        if k in BARCO_CAMPOS:
            if k=="nome": base[k]=str(v)
            else:
                try:base[k]=None if v is None or str(v).strip()=="" or str(v).lower()=="nan" else float(v)
                except (ValueError, TypeError) as e:raise ValueError(f"Parâmetro '{k}' inválido") from e
        elif k in ("hidro_tabela","gz_curva","casco_contorno"):
            if not isinstance(v,list):raise ValueError(f"{k} precisa ser uma lista")
            base[k]=v
    return base


def tabela_para_lista(linhas, colunas):
    out=[]
    for n,row in enumerate(linhas):
        linha={}
        for c in colunas:
            v=row.get(c)
            if v is None or str(v).strip()=="" or (isinstance(v,float) and np.isnan(v)):
                linha[c]=None
            elif c in ("nome","categoria","id"):
                linha[c]=str(v)
            else:
                try:linha[c]=float(v)
                except (ValueError,TypeError) as ex:raise ValueError(f"Linha {n+1} campo '{c}' inválido: {v}") from ex
        out.append(linha)
    return out


def csv_bytes(rows):
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


def json_bytes(data):
    return json.dumps(normalizar(data),indent=2,ensure_ascii=False).encode("utf-8")
