"""Controles Streamlit compartilhados para CSV/XLSX das APs.

A tela só sugere categoria e campos; o usuário confirma unidades e importação.
"""
import hashlib
import streamlit as st
import pandas as pd
from .importacao import abas_excel, inspecionar_abas, ler_bruto, escolher_cabecalho
from .mapeamento import sugestao_coluna

NOMES_TIPO={'hidro':'Tabela hidrostática', 'barco':'Dados principais da embarcação',
            'gz':'Curva GZ', 'casco':'Contorno XY', 'cargas':'Cargas AP1.2',
            'leituras':'Medições experimentais'}


def controles_tabela(uploaded, prefix):
    """Retorna aba, índice de cabeçalho zero-based, convenção decimal e categoria sugerida."""
    uid=hashlib.sha1(uploaded.getvalue()).hexdigest()[:10]
    ext=uploaded.name.lower()
    aba=None; categoria=None; header=0
    if ext.endswith('.xlsx'):
        infos=inspecionar_abas(uploaded)
        st.write('**Diagnóstico das abas encontradas**')
        st.dataframe(pd.DataFrame([{'Aba':x['aba'],
                                    'Tipo sugerido':NOMES_TIPO.get(x['tipo'],'Não reconhecido / auxiliar'),
                                    'Cabeçalho na linha':x['linha_cabecalho']+1,
                                    'Observação':x['observacao']} for x in infos]),
                     use_container_width=True,hide_index=True)
        candidatas=[i for i,x in enumerate(infos) if x['tipo'] is not None]
        indice=candidatas[0] if candidatas else 0
        aba=st.selectbox('Aba do Excel', [x['aba'] for x in infos],index=indice,
                         key=f'{prefix}_aba_{uid}')
        escolhido=next(x for x in infos if x['aba']==aba)
        header=escolhido['linha_cabecalho'];categoria=escolhido['tipo']
    elif ext.endswith('.csv'):
        raw=ler_bruto(uploaded,nrows=35)
        header,categoria=escolher_cabecalho(raw)
    elif ext.endswith('.json'):
        return None,None,False,None
    else:
        raise ValueError('Apenas arquivos CSV, XLSX e JSON são aceitos.')
    st.caption('Se houver título, logotipo ou comentários antes da tabela, ajuste a linha do cabeçalho.')
    cab=st.number_input('Linha que contém os cabeçalhos (começa em 1)',
                        min_value=1,max_value=100000,value=header+1,step=1,
                        key=f'{prefix}_cabecalho_{uid}_{aba}')-1
    decimal=st.checkbox('Os números textuais utilizam vírgula decimal (ex.: 1,25; 1.234,56)',
                        value=False,key=f'{prefix}_virgula_{uid}_{aba}')
    if cab!=header:categoria=None
    return aba,cab,decimal,categoria


def mapear_campos(dados,tipo,colunas,obrigatorios,prefix):
    nomes=list(dict.fromkeys(k for r in dados if isinstance(r,dict) for k in r if k!='__linha_origem__'))
    if not nomes:raise ValueError('Não existem colunas com nome nessa aba.')
    st.caption('Colunas detectadas: '+', '.join(nomes))
    # Exige confirmação de toda correspondência, com pré-seleção apenas de aliases exatos.
    escolhas=['— Não importar —']+nomes
    colunas_map={}
    ca,cb=st.columns(2)
    for i,c in enumerate(colunas):
        sugerido=sugestao_coluna(tipo,c,nomes)
        default=nomes.index(sugerido)+1 if sugerido is not None else 0
        with (ca if i%2==0 else cb):
            colunas_map[c]=st.selectbox(c+(' *' if c in obrigatorios else ' (opcional)'),
                         escolhas,index=default,key=f'{prefix}_{tipo}_{c}')
    st.caption('* Campo obrigatório. Uma mesma coluna de origem não pode representar dois campos.')
    return colunas_map


def aplicar_mapeamento(dados,colmap,obrigatorios):
    ausentes=[x for x in obrigatorios if colmap.get(x)=='— Não importar —']
    if ausentes:
        raise ValueError('Associe as colunas obrigatórias: '+', '.join(ausentes))
    usados=[x for x in colmap.values() if x!='— Não importar —']
    if len(usados)!=len(set(usados)):
        raise ValueError('A mesma coluna foi usada para duas grandezas. Revise o mapeamento.')
    return [dict({'__linha_origem__':r.get('__linha_origem__')},
                 **{c:r.get(s) if s!='— Não importar —' else None for c,s in colmap.items()})
            for r in dados]
